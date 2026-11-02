import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.entities import Job
from app.workers.pipelines import (
    run_analyze_video_pipeline,
    run_render_clip_pipeline,
    run_prompt_to_video_pipeline,
    run_regenerate_scene_pipeline
)

class LocalJobQueue:
    """
    In-process multi-threaded background job dispatcher with persistent tracking,
    concurrency throttling, and automatic retry control.
    Runs persistently in the background without requiring browser to remain open.
    """
    def __init__(self, max_workers: int = 4, max_concurrent_renders: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="clipforge-worker")
        # Concurrency throttle to prevent system resource exhaustion during heavy FFmpeg encodes
        self.render_semaphore = threading.BoundedSemaphore(value=max_concurrent_renders)

    def _execute_with_retry(
        self,
        job_id: str,
        target_fn: Callable[..., Any],
        args: tuple,
        max_retries: int = 2
    ):
        attempt = 0
        while attempt <= max_retries:
            try:
                with self.render_semaphore:
                    logger.info(f"Worker starting execution for job {job_id} (attempt {attempt + 1}/{max_retries + 1})")
                    target_fn(*args)
                    return
            except Exception as e:
                attempt += 1
                logger.error(f"Error during job {job_id} on attempt {attempt}: {e}")
                with SessionLocal() as session:
                    job = session.query(Job).filter(Job.id == job_id).first()
                    if job:
                        job.retry_count = attempt
                        if attempt <= max_retries:
                            job.status = "retrying"
                            job.current_step = f"Transient error, retrying (attempt {attempt + 1})..."
                        else:
                            job.status = "failed"
                            job.error_message = str(e)
                        session.commit()

                if attempt <= max_retries:
                    # Exponential backoff
                    sleep_time = 2.0 ** attempt
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Job {job_id} exceeded maximum retries ({max_retries}). Marked as failed.")
                    break

    def enqueue_analysis(self, job_id: str, asset_id: str, target_clip_duration: float = 30.0):
        logger.info(f"Enqueuing video analysis job {job_id} for asset {asset_id}")
        self.executor.submit(
            self._execute_with_retry,
            job_id,
            run_analyze_video_pipeline,
            (job_id, asset_id, target_clip_duration)
        )

    def enqueue_clip_render(self, job_id: str, clip_id: str):
        logger.info(f"Enqueuing clip rendering job {job_id} for clip {clip_id}")
        self.executor.submit(
            self._execute_with_retry,
            job_id,
            run_render_clip_pipeline,
            (job_id, clip_id)
        )

    def enqueue_prompt_video(self, job_id: str, project_id: str, prompt_data: dict):
        logger.info(f"Enqueuing prompt-to-video generation job {job_id} for project {project_id}")
        self.executor.submit(
            self._execute_with_retry,
            job_id,
            run_prompt_to_video_pipeline,
            (job_id, project_id, prompt_data)
        )

    def enqueue_scene_regeneration(self, job_id: str, scene_id: str, new_prompt: str = None):
        logger.info(f"Enqueuing scene regeneration job {job_id} for scene {scene_id}")
        self.executor.submit(
            self._execute_with_retry,
            job_id,
            run_regenerate_scene_pipeline,
            (job_id, scene_id, new_prompt)
        )

local_queue = LocalJobQueue()
