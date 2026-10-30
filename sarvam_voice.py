import base64
import io
import os
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# 15 languages used by this project.
SARVAM_LANG_MAP: Dict[str, str] = {
    "English": "en-IN",
    "Tamil": "ta-IN",
    "Hindi": "hi-IN",
    "Telugu": "te-IN",
    "Malayalam": "ml-IN",
    "Kannada": "kn-IN",
    "Bengali": "bn-IN",
    "Marathi": "mr-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN",
    "Odia": "od-IN",
    "Assamese": "as-IN",
    "Urdu": "ur-IN",
    "Nepali": "ne-IN",
    "Konkani": "kok-IN",
}

# Sarvam Bulbul TTS currently supports these 11 languages.
TTS_LANGUAGES = {
    "English",
    "Tamil",
    "Hindi",
    "Telugu",
    "Malayalam",
    "Kannada",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Punjabi",
    "Odia",
}

# Male v2 speaker + lower pitch.
TTS_SPEAKER = "karun"
LOW_PITCH = -0.50
SLOW_PACE = 0.90
LOUDNESS = 1.0


def is_tts_supported(language_name: str) -> bool:
    return language_name in TTS_LANGUAGES


def get_language_code(language_name: str) -> str:
    return SARVAM_LANG_MAP.get(language_name, "en-IN")


def _check_api_key() -> None:
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is missing. Add it to the .env file."
        )


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "voice.webm",
    language_name: str = "English",
    mime_type: str = "audio/webm",
) -> Dict:
    """Send browser-recorded audio to Sarvam STT."""
    _check_api_key()

    language_code = get_language_code(language_name)

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Accept": "application/json",
    }

    files = {
        "file": (
            filename,
            io.BytesIO(audio_bytes),
            mime_type,
        )
    }

    data = {
        "model": "saaras:v3",
        "mode": "transcribe",
        "language_code": language_code,
    }

    response = requests.post(
        SARVAM_STT_URL,
        headers=headers,
        files=files,
        data=data,
        timeout=45,
    )

    if not response.ok:
        try:
            details = response.json()
        except ValueError:
            details = response.text
        raise RuntimeError(
            f"Sarvam STT error {response.status_code}: {details}"
        )

    result = response.json()
    return {
        "transcript": result.get("transcript", "").strip(),
        "language_code": result.get("language_code"),
        "request_id": result.get("request_id"),
    }


def synthesize_speech(
    text: str,
    language_name: str = "English",
) -> Optional[bytes]:
    """Generate low-pitch Sarvam audio for the 11 supported TTS languages.

    Returns WAV bytes, or None when Sarvam TTS does not support the language.
    """
    if language_name not in TTS_LANGUAGES:
        return None

    _check_api_key()

    text = str(text or "").strip()
    if not text:
        raise ValueError("Text for speech cannot be empty.")

    # Bulbul v2 supports pitch. Negative pitch makes the voice deeper.
    payload = {
        "text": text[:1500],
        "model": "bulbul:v2",
        "language_code": get_language_code(language_name),
        "speaker": TTS_SPEAKER,
        "pitch": LOW_PITCH,
        "pace": SLOW_PACE,
        "loudness": LOUDNESS,
        "output_audio_codec": "wav",
    }

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(
        SARVAM_TTS_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if not response.ok:
        try:
            details = response.json()
        except ValueError:
            details = response.text
        raise RuntimeError(
            f"Sarvam TTS error {response.status_code}: {details}"
        )

    result = response.json()
    audios = result.get("audios") or []

    if not audios:
        raise RuntimeError("Sarvam TTS returned no audio.")

    return base64.b64decode(audios[0])
