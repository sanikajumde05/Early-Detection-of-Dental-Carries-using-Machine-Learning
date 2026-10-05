"""Step 6: Sentiment Analysis — 'Detects citizen sentiment'.
Uses one multilingual model (covers Hindi + English, among others) instead of
routing between two separate models — simpler, and one fewer model to download.
"""
from functools import lru_cache
from transformers import pipeline
from app.config import SENTIMENT_MODEL


@lru_cache(maxsize=1)
def _get_sentiment_model():
    return pipeline("sentiment-analysis", model=SENTIMENT_MODEL)


def analyze_sentiment(text: str, lang: str) -> tuple[str, float]:
    result = _get_sentiment_model()(text)[0]
    return result["label"], round(float(result["score"]), 4)
