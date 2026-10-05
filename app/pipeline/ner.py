"""Step 4: Entity Extraction — 'Extracts key details (location, dept, name, etc.)'.
Routes to IndicNER for Hindi text and bert-base-NER for English text.
"""
from functools import lru_cache
from transformers import pipeline
from app.config import NER_MODEL_HI, NER_MODEL_EN


@lru_cache(maxsize=1)
def _get_ner_hi():
    return pipeline("ner", model=NER_MODEL_HI, aggregation_strategy="simple")


@lru_cache(maxsize=1)
def _get_ner_en():
    return pipeline("ner", model=NER_MODEL_EN, aggregation_strategy="simple")


def extract_entities(text: str, lang: str) -> list[dict]:
    ner = _get_ner_hi() if lang == "hi" else _get_ner_en()
    results = ner(text)
    return [
        {"text": r["word"], "type": r["entity_group"], "confidence": round(float(r["score"]), 4)}
        for r in results
    ]
