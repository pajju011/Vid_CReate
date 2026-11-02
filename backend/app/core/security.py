import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters and return a safe basename."""
    safe_name = Path(filename).name
    # Remove any null bytes or path separators
    clean_name = safe_name.replace("\x00", "").replace("/", "").replace("\\", "")
    return clean_name or "uploaded_media"

def generate_secure_filename(original_filename: str) -> Tuple[str, str]:
    """
    Returns (secure_unique_filename, extension)
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        ext = ".mp4"
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}", ext

def validate_upload_file(file: UploadFile) -> None:
    """Validate extension and size of uploaded file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

def validate_safe_path(target_path: Path, base_dir: Path = None) -> Path:
    """
    Ensure target path does not escape external storage directories and
    strictly guarantees no media is accessed or stored inside the project folder.
    """
    try:
        resolved_target = target_path.resolve()
        resolved_project = settings.BASE_DIR.resolve()

        # Reject any media path located inside the project repository
        if str(resolved_target).lower().startswith(str(resolved_project).lower()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Media files cannot reside inside the project directory."
            )

        if base_dir:
            if not str(resolved_target).lower().startswith(str(base_dir.resolve()).lower()):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: path traversal attempt detected."
                )
            return resolved_target

        from app.services.storage.storage_service import storage_service
        allowed = storage_service.get_allowed_roots()
        is_allowed = any(str(resolved_target).lower().startswith(str(d.resolve()).lower()) for d in allowed if d.exists())
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: path traversal attempt detected."
            )
        return resolved_target
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filesystem path specified."
        )

