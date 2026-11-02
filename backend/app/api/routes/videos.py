from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import VideoAsset, Transcript, Job
from app.schemas.schemas import JobResponse
from app.workers.local_queue import local_queue

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/{asset_id}/analyze", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def analyze_video(
    asset_id: str,
    target_clip_duration: float = 30.0,
    db: Session = Depends(get_db)
):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Video asset not found.")

    job = Job(
        project_id=asset.project_id,
        job_type="video_analysis",
        status="pending",
        progress=0,
        current_step="Queued video analysis..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    local_queue.enqueue_analysis(job.id, asset.id, target_clip_duration)
    return job

@router.get("/{asset_id}/analysis")
def get_video_analysis(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Video asset not found.")

    transcript = db.query(Transcript).filter(Transcript.asset_id == asset_id).first()

    return {
        "asset_id": asset.id,
        "duration": asset.duration,
        "width": asset.width,
        "height": asset.height,
        "metadata": asset.metadata_json,
        "transcript": {
            "text": transcript.text if transcript else None,
            "segments": transcript.segments_json if transcript else [],
            "language": transcript.language if transcript else "en"
        }
    }
