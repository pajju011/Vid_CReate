from pathlib import Path
from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.models.entities import Project, Job, VideoAsset
from app.workers.pipelines import run_prompt_to_video_pipeline

def test_prompt_to_video_pipeline():
    init_db()

    with SessionLocal() as session:
        proj = Project(
            name="Test Prompt Reel",
            project_type="prompt_to_video",
            platform="instagram_reels",
            status="processing"
        )
        session.add(proj)
        session.flush()

        job = Job(
            project_id=proj.id,
            job_type="prompt_to_video",
            status="pending",
            progress=0
        )
        session.add(job)
        session.commit()
        project_id = proj.id
        job_id = job.id

    prompt_data = {
        "prompt": "Create an energetic fitness tracker launch video with strong hook and CTA",
        "target_platform": "instagram_reels",
        "duration_seconds": 6.0,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "num_scenes": 2,
        "background_music": "none",
        "caption_style": "bold_yellow"
    }

    run_prompt_to_video_pipeline(job_id, project_id, prompt_data)

    with SessionLocal() as session:
        j = session.query(Job).filter(Job.id == job_id).first()
        assert j.status == "completed"
        assert j.progress == 100

        final_asset = session.query(VideoAsset).filter(
            VideoAsset.project_id == project_id,
            VideoAsset.asset_type == "rendered_final"
        ).first()
        assert final_asset is not None
        assert Path(final_asset.storage_path).exists()
        assert final_asset.width == 1080
        assert final_asset.height == 1920
