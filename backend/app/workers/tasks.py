import asyncio
from app.workers.celery_app import celery_app
from app.workers.pipelines import (
    run_analyze_video_pipeline,
    run_render_clip_pipeline,
    run_prompt_to_video_pipeline
)

@celery_app.task(name="tasks.analyze_video")
def celery_analyze_video(job_id: str, asset_id: str, target_clip_duration: float = 30.0):
    asyncio.run(run_analyze_video_pipeline(job_id, asset_id, target_clip_duration))

@celery_app.task(name="tasks.render_clip")
def celery_render_clip(job_id: str, clip_id: str):
    asyncio.run(run_render_clip_pipeline(job_id, clip_id))

@celery_app.task(name="tasks.prompt_to_video")
def celery_prompt_to_video(job_id: str, project_id: str, prompt_data: dict):
    asyncio.run(run_prompt_to_video_pipeline(job_id, project_id, prompt_data))

