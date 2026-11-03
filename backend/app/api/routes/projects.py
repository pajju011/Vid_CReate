from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Project
from app.schemas.schemas import ProjectCreate, ProjectResponse, ProjectDetailResponse

from app.services.storage.storage_service import storage_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    proj = Project(
        name=payload.name,
        project_type=payload.project_type,
        platform=payload.platform,
        settings=payload.settings,
        status="draft"
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    for a in proj.assets:
        a.download_url = f"/api/assets/{a.id}/download"
        a.stream_url = f"/api/assets/{a.id}/stream"
    for c in proj.clips:
        if c.rendered_asset_id:
            c.download_url = f"/api/assets/{c.rendered_asset_id}/download"
            c.stream_url = f"/api/assets/{c.rendered_asset_id}/stream"
        c.duration = round(c.end_time - c.start_time, 2)

    return proj

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Remove all external media files belonging to this project
    for asset in proj.assets:
        storage_service.delete_file(asset.storage_path)

    db.delete(proj)
    db.commit()
    return None
