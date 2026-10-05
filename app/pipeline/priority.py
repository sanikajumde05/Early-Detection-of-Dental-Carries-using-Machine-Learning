"""Step 5: Priority Prediction — 'Predicts urgency & priority level'.

No pretrained model exists for civic-grievance urgency, so this is a transparent,
explainable rule engine combining:
  1. Negative-sentiment strength (from Step 6)
  2. Presence of urgency keywords (bilingual lexicon in config.py)
  3. Duration/repetition cues already caught by the keyword lexicon ("since", "हफ्ते")

UPGRADE PATH: once you log real resolution-time data, replace this with a regression
model (e.g. Random Forest / gradient boosting on these same features) as your CA-3
validation table specifies (MAE/RMSE vs. this rule-based baseline).
"""
from app.config import URGENCY_KEYWORDS


def score_priority(text: str, lang: str, sentiment_label: str, sentiment_score: float) -> tuple[str, float]:
    text_lower = text.lower()
    keywords = URGENCY_KEYWORDS.get(lang, URGENCY_KEYWORDS["en"])
    keyword_hits = sum(1 for kw in keywords if kw.lower() in text_lower)

    # Normalize sentiment into a 0-1 "distress" signal (only negative sentiment counts)
    is_negative = sentiment_label.upper() in ("NEGATIVE", "NEG", "LABEL_0")
    distress = sentiment_score if is_negative else 0.0

    # Weighted score: 60% distress signal, 40% keyword density (capped at 3 hits)
    keyword_signal = min(keyword_hits, 3) / 3
    score = round(0.6 * distress + 0.4 * keyword_signal, 4)

    if score >= 0.75:
        level = "Critical"
    elif score >= 0.5:
        level = "High"
    elif score >= 0.25:
        level = "Medium"
    else:
        level = "Low"

    return level, score
