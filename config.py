from pydantic_settings import BaseSettings
from typing import ClassVar
import os

class Settings(BaseSettings):
    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.abspath(__file__))
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"
    SECRET_KEY: str = "myloveforyou"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30000
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "ctv55345@gmail.com"
    SMTP_PASSWORD: str = "hine cwug losy cpia"
    BASE_URL: ClassVar[str] = "http://localhost:8000"
    GEMINI_API_KEY: str = ""
    class Config:
        env_file = ".env"

settings = Settings()
print(settings.DATABASE_URL)
