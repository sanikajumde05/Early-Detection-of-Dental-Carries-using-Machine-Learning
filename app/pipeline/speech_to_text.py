"""
Speech-to-text for audio grievances (voice notes, phone recordings).

This is the ONLY new AI model needed for audio support. Once speech becomes
text, it re-enters the EXISTING 6-stage text pipeline (language detection,
translation, classification, NER, sentiment, priority) completely unchanged —
we are not building a second, separate "audio brain."

Requires ffmpeg installed as a system program (not a Python package).
"""
import subprocess
from functools import lru_cache

import numpy as np
from transformers import pipeline

from app.config import WHISPER_MODEL

TARGET_SAMPLE_RATE = 16000


@lru_cache(maxsize=1)
def _get_asr():
    return pipeline("automatic-speech-recognition", model=WHISPER_MODEL)


def _decode_audio_file(file_path: str) -> np.ndarray:
    """
    Decodes ANY audio/video file ffmpeg supports into a 16kHz mono float32
    array, by calling ffmpeg directly on the real file PATH.

    This matters specifically for phone-recorded MP4/M4A files (e.g. WhatsApp
    voice notes): many store their format index ("moov atom") at the END of
    the file. ffmpeg can only find that by seeking backward — something it
    CANNOT do if the file is piped in as a raw byte stream (which is how the
    Whisper pipeline decodes audio internally when given a file path).
    Calling ffmpeg on the actual path instead keeps the file seekable and
    avoids that failure entirely.
    """
    command = [
        "ffmpeg", "-nostdin", "-i", file_path,
        "-ac", "1", "-ar", str(TARGET_SAMPLE_RATE),
        "-f", "f32le", "-hide_banner", "-loglevel", "error", "pipe:1",
    ]
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        stderr = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg could not decode this audio file: {stderr.strip() or 'unknown error'}")
    return np.frombuffer(result.stdout, dtype=np.float32)


def transcribe_audio(file_path: str) -> str:
    """Transcribes an audio file to text. Whisper auto-detects the spoken
    language (Hindi or English) and returns text in that SAME language —
    it does not translate, which is what we want: the existing language
    detection step downstream will then route it exactly like typed text."""
    audio_array = _decode_audio_file(file_path)
    asr = _get_asr()
    result = asr({"array": audio_array, "sampling_rate": TARGET_SAMPLE_RATE})
    return result["text"].strip()
