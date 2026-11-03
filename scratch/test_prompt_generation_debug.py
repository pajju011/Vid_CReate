import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path("backend").resolve()))

from app.db.session import init_db, SessionLocal
from app.models.entities import Project, Job
from app.workers.pipelines import run_prompt_to_video_pipeline
from app.core.config import settings
from app.core.logging import logger

def test_pipeline():
    init_db()
    with SessionLocal() as session:
        proj = Project(
            name="Debug Test Video",
            project_type="prompt_to_video",
            platform="instagram_reels",
            settings={"prompt": "A futuristic glowing fitness watch", "duration_seconds": 10.0},
            status="processing"
        )
        session.add(proj)
        session.commit()
        session.refresh(proj)
        
        job = Job(
            project_id=proj.id,
            job_type="prompt_to_video",
            status="pending",
            progress=0,
            current_step="Starting debug test"
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        job_id = job.id
        proj_id = proj.id

    print(f"Triggering pipeline for project {proj_id}, job {job_id}")
    prompt_data = {
        "prompt": "Create a 10-second cinematic Instagram Reel about an AI-powered fitness product.",
        "target_platform": "instagram_reels",
        "duration_seconds": 10.0,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "voiceover_enabled": True,
        "voice_selection": "energetic_male",
        "caption_style": "bold_yellow",
        "background_music": "upbeat",
        "num_scenes": 2
    }
    
    run_prompt_to_video_pipeline(job_id, proj_id, prompt_data)
    
    with SessionLocal() as session:
        j = session.query(Job).filter(Job.id == job_id).first()
        p = session.query(Project).filter(Project.id == proj_id).first()
        print(f"Final Job Status: {j.status}, Progress: {j.progress}, Current Step: {j.current_step}")
        if j.error_message:
            print(f"Job Error Message: {j.error_message}")
        print(f"Final Project Status: {p.status}")

if __name__ == "__main__":
    test_pipeline()

