"""
Image classification for photo-only grievances, using CLIP zero-shot.

This is the second new model added to the project (after Whisper for audio).
Same philosophy: don't train an image classifier from scratch (would need a
large labeled photo dataset this project doesn't have) — use a pretrained
vision-language model's zero-shot ability instead, the same approach already
used for text classification, just applied to images.

Unlike audio (which converts to text and re-enters the EXISTING text
pipeline unchanged), there is no equivalent shortcut for images — a photo
genuinely needs a vision model, so this module does its own classification
independently rather than routing through orchestrator.py.
"""
from functools import lru_cache

from PIL import Image
from transformers import pipeline

from app.config import (
    CLIP_MODEL,
    IMAGE_CATEGORY_LABELS,
    IMAGE_LABEL_TO_CATEGORY,
    IMAGE_SEVERITY_LABELS,
    IMAGE_SEVERITY_TO_PRIORITY,
)


@lru_cache(maxsize=1)
def _get_image_classifier():
    return pipeline("zero-shot-image-classification", model=CLIP_MODEL)


def classify_image(image_path: str) -> dict:
    """Returns {category, category_confidence, priority, priority_score}.
    Two separate zero-shot passes over the same image: one against category
    descriptions, one against severity descriptions — CLIP doesn't have a
    built-in notion of "priority", so this reuses the same category-matching
    mechanism against a different label set."""
    image = Image.open(image_path).convert("RGB")
    classifier = _get_image_classifier()

    category_result = classifier(image, candidate_labels=IMAGE_CATEGORY_LABELS)
    top_category_label = category_result[0]["label"]
    category = IMAGE_LABEL_TO_CATEGORY.get(top_category_label, "Other")
    category_confidence = round(float(category_result[0]["score"]), 4)

    severity_result = classifier(image, candidate_labels=IMAGE_SEVERITY_LABELS)
    top_severity_label = severity_result[0]["label"]
    priority = IMAGE_SEVERITY_TO_PRIORITY.get(top_severity_label, "Medium")
    priority_score = round(float(severity_result[0]["score"]), 4)

    return {
        "category": category,
        "category_confidence": category_confidence,
        "priority": priority,
        "priority_score": priority_score,
    }
