from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import VideoAsset, Job
from app.schemas.schemas import JobResponse
from app.services.storage.storage_service import storage_service

router = APIRouter(prefix="", tags=["rendering"])

@router.get("/assets/{asset_id}/download")
def download_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    file_path = storage_service.get_file(asset.storage_path)

    media_type = "video/mp4"
    if file_path.suffix.lower() in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif file_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif file_path.suffix.lower() in [".wav", ".mp3", ".aac"]:
        media_type = "audio/mpeg"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=asset.original_filename
    )

@router.delete("/assets/{asset_id}", status_code=status.HTTP_200_OK)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """Delete a video asset and its physical file from external storage."""
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    storage_service.delete_file(asset.storage_path)
    db.delete(asset)
    db.commit()
    return {"message": "Video asset deleted from external storage."}

@router.get("/render/{job_id}", response_model=JobResponse)
def get_render_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return job
