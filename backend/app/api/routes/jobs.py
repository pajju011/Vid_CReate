from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Job
from app.schemas.schemas import JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.get("/project/{project_id}", response_model=List[JobResponse])
def list_project_jobs(project_id: str, db: Session = Depends(get_db)):
    return db.query(Job).filter(Job.project_id == project_id).order_by(Job.created_at.desc()).all()
