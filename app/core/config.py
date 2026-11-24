import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Multi-Tool AI Agent – Intelligent Task Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Server configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    STREAMLIT_PORT: int = 8501
    
    # LLM Settings
    LLM_PROVIDER: str = "groq"  # groq, openai, google, mock
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
    
    # API Keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'tasks.db'}"
    
    # Agent Guardrails & Settings
    MAX_AGENT_ITERATIONS: int = 10
    SEARCH_MAX_RESULTS: int = 5
    CONFIRM_TASK_DELETION: bool = True

settings = Settings()
