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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RSS"
    # Development settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    # Logging
    LOG_LEVEL: str = "DEBUG"
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    REFRESH_INTERVAL: int = 30
    STALE_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()
