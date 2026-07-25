import json

from google.cloud import texttospeech
from google.oauth2 import service_account

from app.config import settings

_client = None


def get_client() -> texttospeech.TextToSpeechClient:
    global _client
    if _client is None:
        if settings.google_credentials_json:
            info = json.loads(settings.google_credentials_json)
            creds = service_account.Credentials.from_service_account_info(info)
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
