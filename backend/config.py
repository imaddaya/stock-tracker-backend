from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache
import os

load_dotenv()

class Settings(BaseSettings):
    EMAIL_ADDRESS: str = os.environ["EMAIL_ADDRESS"]
    EMAIL_PASSWORD: str = os.environ["EMAIL_PASSWORD"]
    ALPHA_VANTAGE_API_KEY: str = os.environ["ALPHA_VANTAGE_API_KEY"]
    JWT_ALGORITHM: str = os.environ["JWT_ALGORITHM"]
    JWT_SECRET: str = os.environ["JWT_SECRET"]
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL","http://127.0.0.1:3000")
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

@lru_cache
def get_settings():
    return Settings()