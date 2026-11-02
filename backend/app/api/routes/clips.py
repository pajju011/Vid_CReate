from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Clip, VideoAsset, Transcript, Job
from app.schemas.schemas import ClipResponse, ClipUpdateRequest, GenerateClipsRequest, JobResponse
from app.services.clip_selection.clip_ranker import clip_ranker
from app.services.scene_detection.detector import scene_detector
from app.workers.local_queue import local_queue

router = APIRouter(prefix="", tags=["clips"])

@router.get("/projects/{project_id}/clips", response_model=List[ClipResponse])
def list_project_clips(project_id: str, db: Session = Depends(get_db)):
    clips = db.query(Clip).filter(Clip.project_id == project_id).order_by(Clip.score.desc()).all()
    for c in clips:
        c.duration = round(c.end_time - c.start_time, 2)
        if c.rendered_asset_id:
            c.download_url = f"/api/assets/{c.rendered_asset_id}/download"
    return clips

@router.post("/videos/{asset_id}/clips", response_model=List[ClipResponse])
def generate_clips_for_video(
    asset_id: str,
    payload: GenerateClipsRequest,
    db: Session = Depends(get_db)
):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Video asset not found.")

    transcript = db.query(Transcript).filter(Transcript.asset_id == asset_id).first()
    segments = transcript.segments_json if transcript else []

    scene_cuts = scene_detector.detect_scenes(Path(asset.storage_path))

    candidates = clip_ranker.generate_candidate_clips(
        transcript_segments=segments,
        scene_cuts=scene_cuts,
        video_duration=asset.duration or 30.0,
        target_duration=payload.target_duration,
        num_clips=payload.num_clips
    )

    created_clips = []
    for cand in candidates:
        c = Clip(
            project_id=asset.project_id,
            source_asset_id=asset.id,
            start_time=cand["start_time"],
            end_time=cand["end_time"],
            score=cand["score"],
            title=cand["title"],
            hook=cand["hook"],
            reason=cand["reason"],
            status="candidate",
            crop_mode=payload.crop_mode,
            caption_style=payload.caption_style
        )
        db.add(c)
        db.flush()
        c.duration = round(c.end_time - c.start_time, 2)
        created_clips.append(c)

    db.commit()
    return created_clips

@router.patch("/clips/{clip_id}", response_model=ClipResponse)
def update_clip(
    clip_id: str,
    payload: ClipUpdateRequest,
    db: Session = Depends(get_db)
):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    if payload.start_time is not None:
        clip.start_time = payload.start_time
    if payload.end_time is not None:
        clip.end_time = payload.end_time
    if payload.title is not None:
        clip.title = payload.title
    if payload.crop_mode is not None:
        clip.crop_mode = payload.crop_mode
    if payload.caption_style is not None:
        clip.caption_style = payload.caption_style

    db.commit()
    db.refresh(clip)
    clip.duration = round(clip.end_time - clip.start_time, 2)
    if clip.rendered_asset_id:
        clip.download_url = f"/api/assets/{clip.rendered_asset_id}/download"
    return clip

@router.post("/clips/{clip_id}/render", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def render_clip(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    job = Job(
        project_id=clip.project_id,
        job_type="render_clip",
        status="pending",
        progress=0,
        current_step="Queued short clip render..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    local_queue.enqueue_clip_render(job.id, clip.id)
    return job
