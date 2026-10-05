"""
Central configuration for the Agentic NLP core.
Change model names here if you swap models later (e.g. zero-shot -> fine-tuned MuRIL).
"""

# ---- Model names (Hugging Face hub ids) ----
LANG_DETECT_MODEL = "papluca/xlm-roberta-base-language-detection"

TRANSLATE_HI_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"

# Zero-shot multilingual classifier. Works directly on Hindi or English text,
# no labeled training data needed. Swap this for a fine-tuned MuRIL model
# (see app/pipeline/classify.py) once you have >=50 labeled examples/category.
ZERO_SHOT_CLASSIFY_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

NER_MODEL_HI = "cfilt/HiNER-original-muril-base-cased"
NER_MODEL_EN = "dslim/bert-base-NER"

# Single multilingual model covers both Hindi and English (plus 6 other languages),
# so Hindi and English grievances share one sentiment model instead of two.
SENTIMENT_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# ---- Grievance categories -> candidate labels used by zero-shot classifier ----
# Edit this list to match your target departments (from the architecture diagram).
# NOTE: an earlier attempt to use longer, more descriptive labels here actually
# made routing WORSE (water/health complaints started defaulting to Municipal)
# because the added wording created overlap between categories. Short, distinct
# single labels work better for this model — reverted back to that.
GRIEVANCE_CATEGORIES = [
    "Water Supply",
    "Roads and Infrastructure",
    "Electricity",
    "Municipal / Sanitation",
    "Health",
    "Revenue / Property Tax",
    "Other",
]

# ---- Keyword-override safety net ----
# The zero-shot model has shown a real, repeatable bias toward "Municipal /
# Sanitation" and "Other" for Health and Revenue complaints, even with clear
# signal words present. Rather than keep guessing at label wording (already
# tried twice), this catches UNAMBIGUOUS cases with a direct keyword match
# before the zero-shot model even runs. Zero-shot is still used for anything
# that doesn't match one of these strong signals — this is not a replacement
# for the model, just a targeted correction for its known weak spot.
CATEGORY_KEYWORD_OVERRIDES = {
    "Health": {
        "en": ["hospital", "doctor", "nurse", "medicine", "medical", "clinic",
               "patient", "ambulance", "health center", "health centre"],
        "hi": ["अस्पताल", "डॉक्टर", "नर्स", "दवा", "दवाइयां", "मरीज",
               "एम्बुलेंस", "स्वास्थ्य केंद्र", "चिकित्सा"],
    },
    "Revenue / Property Tax": {
        "en": ["property tax", "land record", "tehsil", "revenue office",
               "tax receipt", "birth certificate", "caste certificate",
               "ration card", "voter id", "rti"],
        "hi": ["प्रॉपर्टी टैक्स", "संपत्ति कर", "भूमि रिकॉर्ड", "तहसील",
               "रसीद", "जन्म प्रमाण पत्र", "जाति प्रमाण पत्र", "राशन कार्ड",
               "वोटर आईडी", "सूचना के अधिकार"],
    },
}
CATEGORY_TO_DEPARTMENT = {
    "Water Supply": "Water Department",
    "Roads and Infrastructure": "Roads & Infrastructure",
    "Electricity": "Electricity Department",
    "Municipal / Sanitation": "Municipal Department",
    "Health": "Health Department",
    "Revenue / Property Tax": "Revenue Department",
    "Other": "Municipal Department",
}

# ---- Urgency keyword lexicon used by the priority-scoring rule engine ----
# (Hindi + English). Uses word STEMS rather than exact inflected forms where
# possible (e.g. "collaps" instead of "collapsed") so substring matching also
# catches "collapse", "collapsing", "could collapse", etc. — a real gap found
# during testing where "could collapse any moment" didn't match "collapsed".
URGENCY_KEYWORDS = {
    "en": [
        "urgent", "emergency", "immediately", "danger", "died", "death",
        "die", "dying", "fire", "burning", "explod", "collaps", "flood",
        "no water", "leak", "electrocut", "spark", "accident", "injur",
        "trapped", "buried", "unconscious", "not responding", "rescue",
        "evacuat", "life-threatening", "life threatening", "critical condition",
        "bleeding", "fatal", "crack", "unsafe", "risk of", "any moment",
        "week", "days", "since",
    ],
    "hi": [
        "तुरंत", "आपातकाल", "खतरा", "खतरनाक", "मृत्यु", "मौत", "मर",
        "आग", "जल", "विस्फोट", "ढह", "गिर", "बाढ़", "पानी नहीं", "रिसाव",
        "करंट", "चिंगारी", "दुर्घटना", "घायल", "फंस", "दब", "बेहोश",
        "प्रतिक्रिया नहीं", "बचाव", "निकाल", "जोखिम", "दरार", "असुरक्षित",
        "कभी भी", "हफ्ते", "दिन", "से",
    ],
}

# ---- Speech-to-text (audio grievances) ----
# openai/whisper-small handles Hindi + English (and auto-detects which one),
# in ONE model, unlike the text pipeline which needs 6 separate models.
# If it's too slow on your machine, try "openai/whisper-base" (smaller, faster,
# slightly less accurate). "openai/whisper-medium" is more accurate but slower.
WHISPER_MODEL = "openai/whisper-small"

# ---- Image classification (photo-only grievances) ----
# CLIP compares a photo against a list of text descriptions and picks the
# best match — the same "zero-shot" idea as the text classifier, just for
# images. Prompts are phrased as full sentences ("a photo of...") because
# that is CLIP's expected prompting style, unlike the short bare labels that
# work better for the text classifier (a different model, different
# mechanism — see the note on GRIEVANCE_CATEGORIES above for why THAT one
# uses short labels; this one genuinely needs the longer, descriptive form).
CLIP_MODEL = "openai/clip-vit-base-patch32"

IMAGE_CATEGORY_LABELS = [
    "a photo of a water leakage, water supply problem, or flooding",
    "a photo of a damaged road, pothole, or broken infrastructure",
    "a photo of an electrical hazard, damaged wire, or power line problem",
    "a photo of overflowing garbage, waste, or an unclean public area",
    "a photo of a health, hospital, or medical related issue",
    "a photo of a government document, property, or tax related matter",
    "a photo of some other civic issue",
]
IMAGE_LABEL_TO_CATEGORY = {
    "a photo of a water leakage, water supply problem, or flooding": "Water Supply",
    "a photo of a damaged road, pothole, or broken infrastructure": "Roads and Infrastructure",
    "a photo of an electrical hazard, damaged wire, or power line problem": "Electricity",
    "a photo of overflowing garbage, waste, or an unclean public area": "Municipal / Sanitation",
    "a photo of a health, hospital, or medical related issue": "Health",
    "a photo of a government document, property, or tax related matter": "Revenue / Property Tax",
    "a photo of some other civic issue": "Other",
}

# Rough priority signal from the photo alone — there is no pretrained model
# for "how dangerous does this image look", same situation as the text
# priority engine. This is a first-pass heuristic (image-only, no text to
# corroborate it), and is meaningfully less reliable than the text/voice
# priority engine — disclose this clearly if asked about it.
IMAGE_SEVERITY_LABELS = [
    "a photo showing a dangerous, hazardous, or urgent emergency situation",
    "a photo showing a moderate civic problem that needs attention soon",
    "a photo showing a minor cosmetic issue with no immediate danger",
]
IMAGE_SEVERITY_TO_PRIORITY = {
    "a photo showing a dangerous, hazardous, or urgent emergency situation": "Critical",
    "a photo showing a moderate civic problem that needs attention soon": "Medium",
    "a photo showing a minor cosmetic issue with no immediate danger": "Low",
}

DATABASE_URL = "sqlite:///./grievances.db"
