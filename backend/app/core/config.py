import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClipForge AI"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    RENDERS_DIR: Path = STORAGE_DIR / "renders"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    ASSETS_DIR: Path = STORAGE_DIR / "assets"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'clipforge.db'}"
    
    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_LOCAL_QUEUE: bool = True  # Fallback to in-process queue if Celery/Redis not available
    
    # Media & Upload Limits
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [".mp4", ".mov", ".webm", ".mkv", ".avi"]
    
    # Tools paths
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    
    # AI Providers Configuration
    DEMO_MODE: bool = True  # Automatically falls back to deterministic demo generation if keys missing
    
    LLM_PROVIDER: str = "mock"  # "gemini", "openai", "mock"
    LLM_API_KEY: Optional[str] = None
    
    VIDEO_PROVIDER: str = "mock"  # "runway", "luma", "replicate", "mock"
    VIDEO_API_KEY: Optional[str] = None
    
    IMAGE_PROVIDER: str = "mock"  # "stability", "dalle", "mock"
    IMAGE_API_KEY: Optional[str] = None
    
    AUDIO_PROVIDER: str = "mock"  # "elevenlabs", "openai", "mock"
    AUDIO_API_KEY: Optional[str] = None
    
    TRANSCRIPTION_PROVIDER: str = "mock"  # "whisper", "local", "mock"
    TRANSCRIPTION_API_KEY: Optional[str] = None

    # Storage Backend
    STORAGE_BACKEND: str = "local"  # "local", "s3"
    S3_BUCKET: Optional[str] = None
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
for directory in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.RENDERS_DIR, settings.TEMP_DIR, settings.ASSETS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
