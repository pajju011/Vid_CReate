from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Project, Scene, Job
from app.schemas.schemas import PromptPlanningRequest, ProductionPlan, SceneResponse, SceneUpdateRequest, JobResponse
from app.providers.registry import providers
from app.workers.local_queue import local_queue

router = APIRouter(prefix="/generation", tags=["generation"])

@router.post("/storyboard", response_model=ProductionPlan)
def generate_storyboard(payload: PromptPlanningRequest):
    """Generate structured script and storyboard without rendering."""
    llm = providers.get_llm_provider()
    try:
        script = llm.generate_script(
            prompt=payload.prompt,
            duration_seconds=payload.duration_seconds,
            platform=payload.target_platform
        )
        scenes = llm.generate_storyboard(
            script_data=script,
            num_scenes=payload.num_scenes,
            style=payload.visual_style
        )
        return {
            "title": script.get("title", "AI Generated Video"),
            "platform": payload.target_platform,
            "duration_seconds": payload.duration_seconds,
            "aspect_ratio": payload.aspect_ratio,
            "style": payload.visual_style,
            "language": payload.language,
            "scenes": scenes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storyboard planning failed: {str(e)}")

@router.post("/video", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_prompt_to_video(payload: PromptPlanningRequest, db: Session = Depends(get_db)):
    """Initialize project and enqueue full prompt-to-video generation job."""
    proj = Project(
        name=f"Reel: {payload.prompt[:40]}",
        project_type="prompt_to_video",
        platform=payload.target_platform,
        settings=payload.model_dump(),
        status="processing"
    )
    db.add(proj)
    db.flush()

    job = Job(
        project_id=proj.id,
        job_type="prompt_to_video",
        status="pending",
        progress=0,
        current_step="Queueing generation..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    local_queue.enqueue_prompt_video(job.id, proj.id, payload.model_dump())
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    job.status = "cancelled"
    job.current_step = "Cancelled by user"
    db.commit()
    return {"message": "Job marked as cancelled."}

@router.patch("/scenes/{scene_id}", response_model=SceneResponse)
def update_scene(scene_id: str, payload: SceneUpdateRequest, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    if payload.prompt is not None:
        scene.prompt = payload.prompt
    if payload.visual_description is not None:
        scene.visual_description = payload.visual_description
    if payload.duration is not None:
        scene.duration = payload.duration
    if payload.narration is not None:
        scene.narration = payload.narration
    if payload.caption is not None:
        scene.caption = payload.caption
    if payload.camera_movement is not None:
        scene.camera_movement = payload.camera_movement

    db.commit()
    db.refresh(scene)
    return scene
