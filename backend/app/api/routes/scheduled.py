from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import ScheduledTask
from app.services.scheduler.scheduler_service import scheduler_service

router = APIRouter(prefix="/schedules", tags=["scheduled_generation"])

class ScheduledTaskCreate(BaseModel):
    name: str
    task_type: str = "prompt_to_video" # prompt_to_video | video_to_shorts
    schedule_cron: Optional[str] = "daily" # daily, hourly, weekly, or null for one-off
    run_delay_minutes: Optional[int] = 0
    payload: Dict[str, Any]

class ScheduledTaskResponse(BaseModel):
    id: str
    name: str
    task_type: str
    schedule_cron: Optional[str]
    next_run_at: datetime
    is_active: bool
    last_run_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[ScheduledTaskResponse])
def list_scheduled_tasks(db: Session = Depends(get_db)):
    return db.query(ScheduledTask).order_by(ScheduledTask.created_at.desc()).all()

@router.post("", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_task(payload: ScheduledTaskCreate, db: Session = Depends(get_db)):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    next_run = now + timedelta(minutes=max(0, payload.run_delay_minutes or 0))

    task = ScheduledTask(
        name=payload.name,
        task_type=payload.task_type,
        schedule_cron=payload.schedule_cron,
        next_run_at=next_run,
        payload=payload.payload,
        is_active=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/trigger")
def trigger_scheduled_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found.")

    scheduler_service._dispatch_task(db, task)
    db.commit()
    return {"message": f"Scheduled task '{task.name}' triggered successfully."}

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found.")
    db.delete(task)
    db.commit()
    return None

