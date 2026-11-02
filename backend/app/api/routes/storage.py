from fastapi import APIRouter
from app.services.storage.storage_service import storage_service

router = APIRouter(prefix="/storage", tags=["storage"])

@router.get("/stats")
def get_storage_stats():
    """Retrieve external video storage diagnostics, disk usage, and directory paths."""
    return storage_service.get_storage_stats()

@router.post("/cleanup")
def cleanup_temp_storage(max_age_hours: int = 12):
    """Manually trigger safe cleanup of temporary processing media."""
    storage_service.cleanup_old_temp_files(max_age_hours=max_age_hours)
    return {"message": "Temporary processing files cleaned up safely."}

