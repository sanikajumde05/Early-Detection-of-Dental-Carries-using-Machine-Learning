"""
Lightweight stand-in for ServiceNow's CSM Case table.
Once you have a PDI, you replace this module's writes with a REST call
to ServiceNow's Table API (POST /api/now/table/sn_customerservice_case)
and keep everything else in the pipeline unchanged.
"""
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    address = Column(String, nullable=True)
    password_hash = Column(String)
    password_salt = Column(String)
    auth_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    raw_text = Column(Text)
    detected_language = Column(String)
    translated_text = Column(Text, nullable=True)

    category = Column(String)
    category_confidence = Column(Float)
    department = Column(String)

    entities_json = Column(Text)  # JSON string of extracted entities

    sentiment_label = Column(String)
    sentiment_score = Column(Float)

    priority = Column(String)      # Low / Medium / High / Critical
    priority_score = Column(Float)

    source = Column(String, default="text")  # "text", "voice", or "image"
    image_path = Column(String, nullable=True)  # filename of an attached/submitted photo, if any

    # Snapshot of who filed this case, taken at submission time (the citizen
    # may edit these per-submission even though they're auto-filled from
    # their profile — see citizen_portal.html). Kept directly on the case
    # (rather than requiring a join every time) since staff need to see this
    # immediately when they open any case.
    citizen_id = Column(Integer, nullable=True)
    citizen_name = Column(String, nullable=True)
    citizen_phone = Column(String, nullable=True)
    citizen_email = Column(String, nullable=True)
    citizen_address = Column(String, nullable=True)

    # Where the ISSUE is located (not necessarily the citizen's home address).
    # Populated either via the browser's "use my location" button (accurate,
    # both fields set) or left null if the citizen only typed a text address.
    # Needed as real numbers (not just the text address) for the dashboard's
    # map heatmap feature.
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)

    status = Column(String, default="New")  # New -> Assigned -> In Progress -> Resolved
    resolved_at = Column(DateTime, nullable=True)  # set automatically when status becomes "Resolved"


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
