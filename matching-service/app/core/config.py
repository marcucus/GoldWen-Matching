from pydantic import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "goldwen-matching-secret-key-change-in-production")
    ALLOWED_HOSTS: List[str] = ["*"]  # Configure properly in production
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost:5432/goldwen_db"
    )
    
    # Redis settings (for caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Matching algorithm settings
    MAX_DAILY_PROFILES: int = 5
    MIN_DAILY_PROFILES: int = 3
    COMPATIBILITY_THRESHOLD: float = 0.6
    
    # Questionnaire settings - based on personality questions
    PERSONALITY_QUESTIONS_COUNT: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()