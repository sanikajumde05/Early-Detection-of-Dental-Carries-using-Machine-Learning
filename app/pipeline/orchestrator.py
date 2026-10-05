"""
The Agentic NLP Engine orchestrator.
Runs the six steps from your architecture diagram in sequence and returns a
structured case dict ready to be written to the Case table (or later, POSTed
to ServiceNow's Table API).

This sequential version is intentionally simple to get you to a working demo fast.
Once it works end-to-end, you can graduate this to real agent-to-agent messaging
(e.g. AutoGen / AI Agent Studio-style conversable agents) without changing the
individual step functions below — only how they're called changes.
"""
import json
import uuid

from app.pipeline.language_detect import detect_language
from app.pipeline.translate import translate_hi_to_en
from app.pipeline.classify import classify_category
from app.pipeline.ner import extract_entities
from app.pipeline.sentiment import analyze_sentiment
from app.pipeline.priority import score_priority
from app.routing import route_to_department


def run_pipeline(raw_text: str, source: str = "text") -> dict:
    """
    source: "text" for typed grievances, "voice" for audio-transcribed ones.
    Everything below this line runs IDENTICALLY regardless of source — audio
    grievances become text (via speech_to_text.py) BEFORE reaching this
    function, so the pipeline itself never needs to know or care where the
    text came from.
    """
    # 1. Language Detection
    lang = detect_language(raw_text)

    # 2. Translation (only if Hindi; used only where an English-only step needs it)
    translated_text = translate_hi_to_en(raw_text) if lang == "hi" else None

    # 3. Intent & Category Classification (runs on native-language text)
    category, category_confidence = classify_category(raw_text)

    # 4. Entity Extraction (native-language model, routed by lang)
    entities = extract_entities(raw_text, lang)

    # 6. Sentiment Analysis (native-language model, routed by lang)
    sentiment_label, sentiment_score = analyze_sentiment(raw_text, lang)

    # 5. Priority Prediction (depends on sentiment output, so it runs after step 6 here)
    priority_level, priority_score = score_priority(raw_text, lang, sentiment_label, sentiment_score)

    # Routing
    department = route_to_department(category)

    case_number = f"GRV{uuid.uuid4().hex[:8].upper()}"

    return {
        "case_number": case_number,
        "raw_text": raw_text,
        "detected_language": lang,
        "translated_text": translated_text,
        "category": category,
        "category_confidence": category_confidence,
        "department": department,
        "entities_json": json.dumps(entities, ensure_ascii=False),
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "priority": priority_level,
        "priority_score": priority_score,
        "source": source,
        "status": "New",
    }
