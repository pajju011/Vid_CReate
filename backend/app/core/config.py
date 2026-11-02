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
    
    # External Local Media Storage Configuration
    MEDIA_STORAGE_PATH: Path = Path(os.getenv("MEDIA_STORAGE_PATH", "D:/AI_Video_Storage"))
    TEMP_MEDIA_PATH: Path = Path(os.getenv("TEMP_MEDIA_PATH", "D:/AI_Video_Temp"))
    ENABLE_DRAFT_STORAGE: bool = True

    @property
    def STORAGE_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.media_storage_path
        except Exception:
            return self.MEDIA_STORAGE_PATH

    @property
    def UPLOAD_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.uploads_dir
        except Exception:
            return self.MEDIA_STORAGE_PATH / "uploads"

    @property
    def RENDERS_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.renders_dir
        except Exception:
            return self.MEDIA_STORAGE_PATH / "renders"

    @property
    def DRAFTS_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.drafts_dir
        except Exception:
            return self.MEDIA_STORAGE_PATH / "drafts"

    @property
    def THUMBNAILS_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.thumbnails_dir
        except Exception:
            return self.MEDIA_STORAGE_PATH / "thumbnails"

    @property
    def CACHE_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.cache_dir
        except Exception:
            return self.MEDIA_STORAGE_PATH / "cache"

    @property
    def ASSETS_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.media_storage_path / "assets"
        except Exception:
            return self.MEDIA_STORAGE_PATH / "assets"

    @property
    def TEMP_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.temp_processing_dir
        except Exception:
            return self.TEMP_MEDIA_PATH / "processing"

    @property
    def TEMP_PROCESSING_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.temp_processing_dir
        except Exception:
            return self.TEMP_MEDIA_PATH / "processing"

    @property
    def TEMP_CHUNKS_DIR(self) -> Path:
        try:
            from app.services.storage.storage_service import storage_service
            return storage_service.temp_chunks_dir
        except Exception:
            return self.TEMP_MEDIA_PATH / "chunks"
    
    # Database - standard SQLite for reliable zero-latency local development
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'clipforge.db'}"
    
    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_LOCAL_QUEUE: bool = True
    
    # Media & Upload Limits
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [".mp4", ".mov", ".webm", ".mkv", ".avi"]
    
    # Tools paths
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    
    # AI Providers Configuration
    DEMO_MODE: bool = True
    
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: Optional[str] = None
    
    VIDEO_PROVIDER: str = "mock"
    VIDEO_API_KEY: Optional[str] = None
    
    IMAGE_PROVIDER: str = "mock"
    IMAGE_API_KEY: Optional[str] = None
    
    AUDIO_PROVIDER: str = "mock"
    AUDIO_API_KEY: Optional[str] = None
    
    TRANSCRIPTION_PROVIDER: str = "mock"
    TRANSCRIPTION_API_KEY: Optional[str] = None

    # Storage Backend
    STORAGE_BACKEND: str = "local"
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
