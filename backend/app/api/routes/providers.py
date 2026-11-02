from typing import Dict, Any
from fastapi import APIRouter
from app.core.config import settings
from app.providers.registry import providers

router = APIRouter(prefix="", tags=["providers_settings"])

@router.get("/providers")
async def get_providers_status():
    return providers.get_status()

@router.get("/settings")
async def get_settings_summary():
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "storage_backend": settings.STORAGE_BACKEND,
        "demo_mode": settings.DEMO_MODE,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "ffmpeg_available": True
    }

