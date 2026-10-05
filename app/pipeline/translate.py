"""Step 2: Translation — mirrors 'Translates to working language'.

This reimplements the small amount of IndicTrans2 pre/post-processing directly
(instead of depending on the `IndicTransToolkit` package), because that package
ships a Cython extension that requires a C++ compiler to build on Windows.
`indic-nlp-library-itt` and `sacremoses` below are both pure Python, so this
needs no compiler at all.

Working language is English: everything downstream (NER-en, category labels)
assumes English, except the Hindi-native models (IndicNER, hindi-sentiment)
which run on the ORIGINAL text, not the translation — this is deliberate:
native-language NLU is more accurate than translate-then-analyze (see CA-2/CA-3).
Translation is used only where an English-only model is unavoidable.
"""
import re
from functools import lru_cache

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from indicnlp.tokenize import indic_tokenize
from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
from sacremoses import MosesDetokenizer

from app.config import TRANSLATE_HI_EN_MODEL

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_en_detok = MosesDetokenizer(lang="en")


@lru_cache(maxsize=1)
def _get_hi_normalizer():
    return IndicNormalizerFactory().get_normalizer("hi")


@lru_cache(maxsize=1)
def _get_model():
    tokenizer = AutoTokenizer.from_pretrained(TRANSLATE_HI_EN_MODEL, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATE_HI_EN_MODEL, trust_remote_code=True).to(_DEVICE)
    return tokenizer, model


def _preprocess_hi(text: str) -> str:
    """Normalize + tokenize Hindi text and prepend the IndicTrans2 language tags."""
    text = text.strip()
    try:
        text = _get_hi_normalizer().normalize(text)
    except Exception:
        pass  # normalizer resources unavailable; fall back to raw text
    tokens = indic_tokenize.trivial_tokenize(text, lang="hi")
    return f"hin_Deva eng_Latn {' '.join(tokens)}"


def _postprocess_en(text: str) -> str:
    """Strip any echoed language tags and detokenize the English output."""
    text = text.strip()
    text = re.sub(r"^(eng_Latn|hin_Deva)\s+", "", text)
    tokens = text.split()
    try:
        return _en_detok.detokenize(tokens)
    except Exception:
        return " ".join(tokens)


def translate_hi_to_en(text: str) -> str:
    tokenizer, model = _get_model()
    preprocessed = _preprocess_hi(text)
    inputs = tokenizer(preprocessed, return_tensors="pt", truncation=True, max_length=256).to(_DEVICE)
    with torch.no_grad():
        generated = model.generate(**inputs, max_length=256, num_beams=5)
    decoded = tokenizer.decode(generated[0], skip_special_tokens=True)
    return _postprocess_en(decoded)
