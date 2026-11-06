import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.entities import ScheduledTask, Project, Job
from app.workers.local_queue import local_queue

class SchedulerService:
    """
    Persistent background scheduler that executes automated prompt-to-video
    or video-to-shorts generation jobs without requiring the browser to remain open.
    """
    def __init__(self, check_interval_seconds: int = 10):
        self.check_interval_seconds = check_interval_seconds
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="clipforge-scheduler")
        self._thread.start()
        logger.info("ClipForge background scheduler service started.")

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("ClipForge background scheduler service stopped.")

    def _run_loop(self):
        while self._running:
            try:
                self.process_due_tasks()
            except Exception as e:
                logger.error(f"Error in scheduler process loop: {e}")
            if self._stop_event.wait(self.check_interval_seconds):
                break

    def process_due_tasks(self):
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            due_tasks = session.query(ScheduledTask).filter(
                ScheduledTask.is_active == True,
                ScheduledTask.next_run_at <= now
            ).all()

            for task in due_tasks:
                logger.info(f"Triggering scheduled generation task: '{task.name}' (ID: {task.id})")
                self._dispatch_task(session, task)

            session.commit()

    def _dispatch_task(self, session, task: ScheduledTask):
        payload = task.payload or {}
        task_type = task.task_type

        # 1. Create Project
        proj = Project(
            name=f"[Scheduled] {task.name}",
            project_type=task_type,
            platform=payload.get("target_platform", "instagram_reels"),
            settings=payload,
            status="processing"
        )
        session.add(proj)
        session.flush()

        # 2. Create Job
        job = Job(
            project_id=proj.id,
            job_type=task_type,
            status="pending",
            progress=0,
            current_step="Scheduled run dispatched..."
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # 3. Enqueue to persistent worker
        if task_type == "prompt_to_video":
            local_queue.enqueue_prompt_video(job.id, proj.id, payload)
        elif task_type == "video_to_shorts" and payload.get("asset_id"):
            local_queue.enqueue_analysis(job.id, payload["asset_id"], payload.get("target_clip_duration", 30.0))

        # 4. Advance schedule
        task.last_run_at = datetime.now(timezone.utc)
        if task.schedule_cron == "hourly":
            task.next_run_at = task.last_run_at + timedelta(hours=1)
        elif task.schedule_cron == "daily":
            task.next_run_at = task.last_run_at + timedelta(days=1)
        elif task.schedule_cron == "weekly":
            task.next_run_at = task.last_run_at + timedelta(weeks=1)
        else:
            task.is_active = False # One-off schedule executed

        logger.info(f"Task {task.id} dispatched successfully (Job {job.id}). Next run: {task.next_run_at if task.is_active else 'Deactivated'}")

scheduler_service = SchedulerService()

