from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    api_key: str
    admin_email: str
    admin_password: str
    plivo_auth_id: str = ""
    plivo_auth_token: str = ""
    plivo_from_number: str = ""
    public_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
