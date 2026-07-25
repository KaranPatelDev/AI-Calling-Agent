from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    api_key: str
    admin_email: str
    admin_password: str
    plivo_auth_id: str = ""
    plivo_auth_token: str = ""
    plivo_from_number: str = ""
    forward_to_number: str = ""
    public_base_url: str = "http://localhost:8000"
    # ponytail: the full JSON contents of a GCP service account key (not a file path) — Render's
    # filesystem is ephemeral, so we parse this directly instead of reading a mounted file.
    google_credentials_json: str = ""
    google_tts_voice: str = "hi-IN-Chirp3-HD-Leda"

    class Config:
        env_file = ".env"


settings = Settings()
