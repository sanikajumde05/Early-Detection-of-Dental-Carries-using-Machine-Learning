"""
FastAPI service exposing the Agentic NLP core, plus citizen login/registration.
"""
import os
import shutil
import tempfile
import uuid
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import init_db, get_session, Case, Citizen
from app.auth import hash_password, verify_password, generate_token
from app.pipeline.orchestrator import run_pipeline
from app.pipeline.speech_to_text import transcribe_audio
from app.pipeline.image_classify import classify_image
from app.routing import route_to_department

IMAGE_UPLOAD_DIR = "uploaded_images"

app = FastAPI(title="Agentic Grievance NLP Core", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# The upload folder must exist before StaticFiles mounts it below (this line
# runs at import time, before the startup event above would otherwise fire).
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)

# Serves uploaded photos back out at http://localhost:8000/images/<filename>
# so the dashboard and citizen portal can display them directly.
app.mount("/images", StaticFiles(directory=IMAGE_UPLOAD_DIR), name="images")


# ==================================================================== AUTH

class CitizenRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str | None = None
    password: str


class CitizenLogin(BaseModel):
    email: EmailStr
    password: str


def _citizen_public_shape(citizen: Citizen, token: str) -> dict:
    return {
        "token": token,
        "id": citizen.id,
        "full_name": citizen.full_name,
        "email": citizen.email,
        "phone": citizen.phone,
        "address": citizen.address,
    }


@app.post("/auth/register")
def register(payload: CitizenRegister, db: Session = Depends(get_session)):
    existing = db.query(Citizen).filter(Citizen.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    pw_hash, salt = hash_password(payload.password)
    token = generate_token()

    citizen = Citizen(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        password_hash=pw_hash,
        password_salt=salt,
        auth_token=token,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return _citizen_public_shape(citizen, token)


@app.post("/auth/login")
def login(payload: CitizenLogin, db: Session = Depends(get_session)):
    citizen = db.query(Citizen).filter(Citizen.email == payload.email).first()
    if not citizen or not verify_password(payload.password, citizen.password_salt, citizen.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = generate_token()
    citizen.auth_token = token
    db.commit()

    return _citizen_public_shape(citizen, token)


def get_current_citizen(x_auth_token: str = Header(...), db: Session = Depends(get_session)) -> Citizen:
    """Dependency used by every grievance-submitting endpoint below — only a
    logged-in citizen (valid token) can file a grievance."""
    citizen = db.query(Citizen).filter(Citizen.auth_token == x_auth_token).first()
    if not citizen:
        raise HTTPException(status_code=401, detail="Not logged in, or session expired. Please log in again.")
    return citizen


@app.get("/auth/me")
def get_me(citizen: Citizen = Depends(get_current_citizen)):
    return _citizen_public_shape(citizen, citizen.auth_token)


@app.post("/auth/logout")
def logout(citizen: Citizen = Depends(get_current_citizen), db: Session = Depends(get_session)):
    citizen.auth_token = None
    db.commit()
    return {"detail": "Logged out"}


# ==================================================================== GRIEVANCES

class GrievanceIn(BaseModel):
    text: str
    # Auto-filled from the citizen's profile by the frontend, but editable
    # per-submission — these override the profile defaults if provided.
    citizen_name: str | None = None
    citizen_phone: str | None = None
    citizen_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None


def _citizen_snapshot(citizen: Citizen, name: str | None, phone: str | None, address: str | None) -> dict:
    """Builds the citizen-info snapshot stored on the Case: uses the
    submission-time override if given, otherwise falls back to the citizen's
    saved profile value."""
    return {
        "citizen_id": citizen.id,
        "citizen_name": name or citizen.full_name,
        "citizen_phone": phone or citizen.phone,
        "citizen_email": citizen.email,
        "citizen_address": address or citizen.address,
    }


@app.post("/grievance")
def submit_grievance(
    payload: GrievanceIn,
    db: Session = Depends(get_session),
    citizen: Citizen = Depends(get_current_citizen),
):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    result = run_pipeline(payload.text)
    result.update(_citizen_snapshot(citizen, payload.citizen_name, payload.citizen_phone, payload.citizen_address))
    result["location_lat"] = payload.location_lat
    result["location_lng"] = payload.location_lng

    case = Case(**result)
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "id": case.id,
        "case_number": case.case_number,
        "department": case.department,
        "category": case.category,
        "priority": case.priority,
        "sentiment": case.sentiment_label,
        "source": case.source,
        "status": case.status,
    }


@app.post("/grievance/audio")
async def submit_grievance_audio(
    audio: UploadFile = File(...),
    citizen_name: str = Form(None),
    citizen_phone: str = Form(None),
    citizen_address: str = Form(None),
    location_lat: float = Form(None),
    location_lng: float = Form(None),
    db: Session = Depends(get_session),
    citizen: Citizen = Depends(get_current_citizen),
):
    suffix = os.path.splitext(audio.filename or "")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name

    try:
        transcribed_text = transcribe_audio(tmp_path)
    finally:
        os.remove(tmp_path)

    if not transcribed_text:
        raise HTTPException(status_code=400, detail="Could not transcribe any speech from the audio file")

    result = run_pipeline(transcribed_text, source="voice")
    result.update(_citizen_snapshot(citizen, citizen_name, citizen_phone, citizen_address))
    result["location_lat"] = location_lat
    result["location_lng"] = location_lng

    case = Case(**result)
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "id": case.id,
        "case_number": case.case_number,
        "transcribed_text": case.raw_text,
        "department": case.department,
        "category": case.category,
        "priority": case.priority,
        "sentiment": case.sentiment_label,
        "source": case.source,
        "status": case.status,
    }


@app.post("/grievance/image")
async def submit_grievance_image(
    image: UploadFile = File(...),
    description: str = Form(None),
    citizen_name: str = Form(None),
    citizen_phone: str = Form(None),
    citizen_address: str = Form(None),
    location_lat: float = Form(None),
    location_lng: float = Form(None),
    db: Session = Depends(get_session),
    citizen: Citizen = Depends(get_current_citizen),
):
    """
    Photo-based grievance. Unlike audio, there's no shortcut back into the
    text pipeline here — CLIP classifies the image directly. An optional
    short text description can be attached too (shown to staff alongside
    the photo), but it is NOT run through the text classifier — the photo's
    classification is what determines category/priority for this endpoint.
    """
    suffix = os.path.splitext(image.filename or "")[1] or ".jpg"
    saved_filename = f"{uuid.uuid4().hex}{suffix}"
    saved_path = os.path.join(IMAGE_UPLOAD_DIR, saved_filename)
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    try:
        classification = classify_image(saved_path)
    except Exception:
        os.remove(saved_path)
        raise HTTPException(status_code=400, detail="Could not process this image. Please try a different photo (JPG or PNG).")

    department = route_to_department(classification["category"])
    case_number = f"GRV{uuid.uuid4().hex[:8].upper()}"

    result = {
        "case_number": case_number,
        "raw_text": description.strip() if description and description.strip() else "[Photo-only grievance — no text description provided]",
        "detected_language": "en",
        "translated_text": None,
        "category": classification["category"],
        "category_confidence": classification["category_confidence"],
        "department": department,
        "entities_json": "[]",
        "sentiment_label": "neutral",
        "sentiment_score": 0.0,
        "priority": classification["priority"],
        "priority_score": classification["priority_score"],
        "source": "image",
        "image_path": saved_filename,
        "location_lat": location_lat,
        "location_lng": location_lng,
        "status": "New",
    }
    result.update(_citizen_snapshot(citizen, citizen_name, citizen_phone, citizen_address))

    case = Case(**result)
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "id": case.id,
        "case_number": case.case_number,
        "department": case.department,
        "category": case.category,
        "priority": case.priority,
        "source": case.source,
        "status": case.status,
        "image_url": f"/images/{case.image_path}",
    }


@app.get("/citizen/my-cases")
def my_cases(db: Session = Depends(get_session), citizen: Citizen = Depends(get_current_citizen)):
    """Every grievance THIS logged-in citizen has ever filed — so they don't
    need to remember individual case numbers."""
    cases = db.query(Case).filter(Case.citizen_id == citizen.id).order_by(Case.created_at.desc()).all()
    return [
        {
            "case_number": c.case_number,
            "created_at": c.created_at.isoformat(),
            "category": c.category,
            "department": c.department,
            "priority": c.priority,
            "status": c.status,
            "raw_text": c.raw_text,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "image_url": f"/images/{c.image_path}" if c.image_path else None,
        }
        for c in cases
    ]


@app.get("/cases")
def list_cases(db: Session = Depends(get_session)):
    """Staff/dashboard-facing — deliberately NOT behind citizen auth (this is
    the government side, a separate concern from citizen login)."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "case_number": c.case_number,
            "created_at": c.created_at.isoformat(),
            "category": c.category,
            "department": c.department,
            "priority": c.priority,
            "priority_score": c.priority_score,
            "sentiment": c.sentiment_label,
            "language": c.detected_language,
            "source": c.source,
            "status": c.status,
            "raw_text": c.raw_text,
            "citizen_name": c.citizen_name,
            "citizen_phone": c.citizen_phone,
            "citizen_email": c.citizen_email,
            "citizen_address": c.citizen_address,
            "location_lat": c.location_lat,
            "location_lng": c.location_lng,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "image_url": f"/images/{c.image_path}" if c.image_path else None,
        }
        for c in cases
    ]


@app.get("/cases/track/{case_number}")
def track_case(case_number: str, db: Session = Depends(get_session)):
    case = db.query(Case).filter(Case.case_number == case_number).first()
    if not case:
        raise HTTPException(status_code=404, detail="No grievance found with that case number")
    return {
        "case_number": case.case_number,
        "created_at": case.created_at.isoformat(),
        "category": case.category,
        "department": case.department,
        "priority": case.priority,
        "source": case.source,
        "status": case.status,
        "raw_text": case.raw_text,
        "location": case.citizen_address,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "image_url": f"/images/{case.image_path}" if case.image_path else None,
    }


@app.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_session)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {c.name: getattr(case, c.name) for c in case.__table__.columns}


@app.patch("/cases/{case_id}/status")
def update_status(case_id: int, status: str, db: Session = Depends(get_session)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = status
    if status == "Resolved":
        case.resolved_at = datetime.utcnow()
    else:
        # Case reopened/moved backward — clear the old resolution timestamp
        # so it doesn't misleadingly still show a "resolved on" date.
        case.resolved_at = None
    db.commit()
    return {"id": case.id, "status": case.status, "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None}
