from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    API_KEY_ENCRYPTION_KEY: str

    DATABASE_URL: str

    FRONTEND_URL: str = "http://127.0.0.1:3000"

    # Keep optional in case another part of the project uses a server-level key.
    # Your portfolio endpoints currently use the user's stored Alpha Vantage key.
    ALPHA_VANTAGE_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()