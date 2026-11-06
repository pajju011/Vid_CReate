from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import TransferAuditLog
from app.core.privacy import privacy_gateway
from app.schemas.schemas import PrivacySettingsRequest, PrivacySettingsResponse, TransferAuditLogResponse

router = APIRouter(prefix="/privacy", tags=["Privacy Gateway"])

@router.get("/status", response_model=PrivacySettingsResponse)
def get_privacy_status():
    """Retrieve current privacy tier, cloud transfer status, and provider allowlist."""
    return privacy_gateway.get_status()

@router.post("/settings", response_model=PrivacySettingsResponse)
def update_privacy_settings(payload: PrivacySettingsRequest):
    """Update privacy tier (strict_local / private_hybrid / cloud_assisted) and cloud transfer controls."""
    privacy_gateway.update_settings(
        privacy_mode=payload.privacy_mode,
        allow_cloud_transfers=payload.allow_cloud_transfers,
        allowlist=payload.allowlist
    )
    return privacy_gateway.get_status()

@router.get("/audit-logs", response_model=List[TransferAuditLogResponse])
def get_transfer_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve audit history of all external transfer attempts and policy decisions."""
    logs = db.query(TransferAuditLog).order_by(TransferAuditLog.created_at.desc()).limit(limit).all()
    return logs

@router.post("/audit-logs/clear")
def clear_transfer_audit_logs(db: Session = Depends(get_db)):
    """Clear transfer audit logs."""
    db.query(TransferAuditLog).delete()
    db.commit()
    return {"message": "Transfer audit logs cleared successfully."}

