from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import VideoAsset, Job
from app.schemas.schemas import JobResponse
from app.services.storage.storage_service import storage_service

router = APIRouter(prefix="", tags=["rendering"])

@router.get("/assets/{asset_id}/stream")
def stream_asset(asset_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Stream video/audio with full HTTP 206 Range Request support for smooth browser playback and scrubbing.
    """
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    file_path = storage_service.get_file(asset.storage_path)
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    media_type = "video/mp4"
    if file_path.suffix.lower() in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif file_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif file_path.suffix.lower() in [".wav", ".mp3", ".aac"]:
        media_type = "audio/mpeg"

    if range_header:
        parts = range_header.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        end = min(end, file_size - 1)
        chunk_size = (end - start) + 1

        def iterfile():
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_left = chunk_size
                while bytes_left > 0:
                    read_len = min(1024 * 1024, bytes_left)
                    data = f.read(read_len)
                    if not data:
                        break
                    bytes_left -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": media_type,
            "Content-Disposition": "inline",
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Accept-Ranges": "bytes", "Content-Disposition": "inline"}
    )

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
