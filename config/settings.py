from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: Optional[str] = None
    # JWT settings
    JWT_SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RSS"
    # Security
    SECRET_KEY: str = "your-secure-secret-key-here"
    # Development settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    # Logging
    LOG_LEVEL: str = "INFO"
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    REFRESH_INTERVAL: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()
