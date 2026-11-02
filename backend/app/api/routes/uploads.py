import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import validate_upload_file, generate_secure_filename, sanitize_filename
from app.core.logging import logger
from app.db.session import get_db
from app.models.entities import Project, VideoAsset
from app.schemas.schemas import VideoAssetResponse
from app.utils.ffprobe import inspect_media

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("", response_model=VideoAssetResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    file: UploadFile = File(...),
    project_id: str = Form(None),
    db: Session = Depends(get_db)
):
    validate_upload_file(file)

    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Specified project does not exist.")
    else:
        proj = Project(
            name=f"Shorts: {sanitize_filename(file.filename)}",
            project_type="video_to_shorts",
            platform="instagram_reels",
            status="draft"
        )
        db.add(proj)
        db.flush()
        project_id = proj.id

    secure_name, ext = generate_secure_filename(file.filename)
    dest_path = settings.UPLOAD_DIR / secure_name

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file to disk.")

    try:
        meta = inspect_media(dest_path)
    except ValueError as e:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=f"Invalid media file: {str(e)}")

    asset = VideoAsset(
        project_id=project_id,
        asset_type="source_video",
        storage_path=str(dest_path),
        original_filename=sanitize_filename(file.filename),
        duration=meta.get("duration"),
        width=meta.get("width"),
        height=meta.get("height"),
        file_size_bytes=dest_path.stat().st_size,
        metadata_json=meta
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    asset.download_url = f"/api/assets/{asset.id}/download"
    return asset

@router.get("/{asset_id}", response_model=VideoAssetResponse)
def get_upload_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")
    asset.download_url = f"/api/assets/{asset.id}/download"
    return asset
