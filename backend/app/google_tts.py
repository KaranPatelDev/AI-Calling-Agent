import json

from google.cloud import texttospeech
from google.oauth2 import credentials as user_credentials
from google.oauth2 import service_account

from app.config import settings

_client = None


def _load_credentials(info: dict):
    # ponytail: this project's org policy blocks service-account key creation, so
    # GOOGLE_CREDENTIALS_JSON may hold either a real service account key or an
    # "authorized_user" credential from `gcloud auth application-default login` — support both.
    if info.get("type") == "authorized_user":
        return user_credentials.Credentials.from_authorized_user_info(info)
    return service_account.Credentials.from_service_account_info(info)


def get_client() -> texttospeech.TextToSpeechClient:
    global _client
    if _client is None:
        if settings.google_credentials_json:
            creds = _load_credentials(json.loads(settings.google_credentials_json))
            _client = texttospeech.TextToSpeechClient(credentials=creds)
        else:
            _client = texttospeech.TextToSpeechClient()
    return _client


def synthesize(ssml: str) -> bytes:
    """Synthesizes SSML into MP3 bytes using the Chirp 3: HD Hindi voice."""
    client = get_client()
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(ssml=ssml),
        voice=texttospeech.VoiceSelectionParams(
            language_code="hi-IN",
            name=settings.google_tts_voice,
        ),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3),
    )
    return response.audio_content
