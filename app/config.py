from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_STORAGE_BUCKET: str
    smtp_email: str
    smtp_password: str
    frontend_url: str = "http://localhost:51696"

    class Config:
        env_file = ".env"

settings = Settings()
print(settings.DATABASE_URL)
