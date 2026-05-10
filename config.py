from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings - loaded from environment variables"""

    # ===== App Configuration =====
    APP_NAME: str = "CaseForge"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # ===== Database Configuration =====
    DATABASE_URL: str
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10
    ECHO_SQL: bool = False  # Set to True for debugging SQL queries

    # ===== GROQ API Configuration =====
    GROQ_API_KEY: str
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    GROQ_TIMEOUT: int = 30
    GROQ_MAX_TOKENS: int = 4096
    GROQ_TEMPERATURE: float = 0.7

    # ===== JWT/Authentication =====
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ===== Rate Limiting (in-memory for MVP) =====
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # ===== CORS =====
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ===== Logging =====
    LOG_LEVEL: str = "INFO"
    ENABLE_STRUCTURED_LOGGING: bool = True

    # ===== Sentry (optional error tracking) =====
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()