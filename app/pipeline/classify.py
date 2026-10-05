"""Step 3: Intent & Category Classification.

MVP uses zero-shot multilingual NLI classification (mDeBERTa-v3-xnli) so you can
start WITHOUT any labeled data, and it works directly on Hindi or English text.

UPGRADE PATH (matches your CA-3 'hybrid classification strategy'):
Once you have ~50-100 labeled grievances per category, fine-tune google/muril-base-cased
as a supervised classifier (higher accuracy, faster inference) and use zero-shot only
as a fallback for categories with too few examples. A fine-tuning script skeleton is
in tests/finetune_muril_classifier.py.
"""
from functools import lru_cache
from transformers import pipeline
from app.config import ZERO_SHOT_CLASSIFY_MODEL, GRIEVANCE_CATEGORIES, CATEGORY_KEYWORD_OVERRIDES


@lru_cache(maxsize=1)
def _get_classifier():
    return pipeline("zero-shot-classification", model=ZERO_SHOT_CLASSIFY_MODEL)


def _keyword_override(text: str) -> str | None:
    """Checks for unambiguous keyword matches BEFORE running the zero-shot
    model. Returns the matched category, or None if nothing matches (in
    which case the caller falls through to the zero-shot model as usual).
    This exists because zero-shot has shown a repeatable bias toward
    "Municipal / Sanitation" and "Other" specifically for Health and Revenue
    complaints — see CATEGORY_KEYWORD_OVERRIDES in config.py for the reasoning."""
    text_lower = text.lower()
    for category, lang_keywords in CATEGORY_KEYWORD_OVERRIDES.items():
        for keywords in lang_keywords.values():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
    return None


def classify_category(text: str) -> tuple[str, float]:
    """Returns (category, confidence). Runs on original-language text.
    Checks the keyword-override safety net first; only calls the zero-shot
    model if nothing unambiguous matched."""
    override = _keyword_override(text)
    if override:
        return override, 1.0  # confidence 1.0 signals "matched by keyword rule, not the model"

    result = _get_classifier()(text, candidate_labels=GRIEVANCE_CATEGORIES, multi_label=False)
    return result["labels"][0], round(result["scores"][0], 4)
