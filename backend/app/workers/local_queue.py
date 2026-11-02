from concurrent.futures import ThreadPoolExecutor
from app.core.logging import logger
from app.workers.pipelines import (
    run_analyze_video_pipeline,
    run_render_clip_pipeline,
    run_prompt_to_video_pipeline
)

class LocalJobQueue:
    """
    In-process multi-threaded background job dispatcher.
    Provides background execution for development without requiring Redis/Celery daemons.
    """
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="clipforge-worker")

    def enqueue_analysis(self, job_id: str, asset_id: str, target_clip_duration: float = 30.0):
        logger.info(f"Enqueuing video analysis job {job_id} for asset {asset_id}")
        self.executor.submit(run_analyze_video_pipeline, job_id, asset_id, target_clip_duration)

    def enqueue_clip_render(self, job_id: str, clip_id: str):
        logger.info(f"Enqueuing clip rendering job {job_id} for clip {clip_id}")
        self.executor.submit(run_render_clip_pipeline, job_id, clip_id)

    def enqueue_prompt_video(self, job_id: str, project_id: str, prompt_data: dict):
        logger.info(f"Enqueuing prompt-to-video generation job {job_id} for project {project_id}")
        self.executor.submit(run_prompt_to_video_pipeline, job_id, project_id, prompt_data)

local_queue = LocalJobQueue()
