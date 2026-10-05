"""Step 1: Language Detection — mirrors the architecture's 'Detects the input language'."""
from functools import lru_cache
from transformers import pipeline
from app.config import LANG_DETECT_MODEL


@lru_cache(maxsize=1)
def _get_detector():
    return pipeline("text-classification", model=LANG_DETECT_MODEL)


def detect_language(text: str) -> str:
    """Returns a 2-letter ISO code, e.g. 'hi' or 'en'. Falls back to 'en' on low confidence."""
    result = _get_detector()(text, top_k=1)[0]
    lang = result["label"]
    # This model outputs many language codes; for the MVP we only branch on hi vs en,
    # everything else is treated as 'en' downstream until you add more languages.
    return lang if lang in ("hi", "en") else "en"
