import pytest
from app.db.session import SessionLocal
from app.models.entities import Project, Job, TransferAuditLog
from app.core.privacy import privacy_gateway
from app.providers.registry import providers
from app.workers.pipelines import update_job_sync

def test_privacy_gateway_strict_local():
    privacy_gateway.update_settings(privacy_mode="strict_local", allow_cloud_transfers=False)
    
    # Test local provider is permitted
    allowed_local, reason_local = privacy_gateway.can_transfer_to_cloud("mock", "video_generation")
    assert allowed_local is True

    # Test cloud provider is blocked in Strict Local
    allowed_cloud, reason_cloud = privacy_gateway.can_transfer_to_cloud("runway", "video_generation", "Generate scene")
    assert allowed_cloud is False
    assert "Strict Local" in reason_cloud

    # Verify audit log was recorded
    with SessionLocal() as db:
        log = db.query(TransferAuditLog).filter(TransferAuditLog.provider == "runway").order_by(TransferAuditLog.created_at.desc()).first()
        assert log is not None
        assert log.allowed is False

def test_privacy_gateway_cloud_controls():
    # Cloud transfers disabled via kill switch
    privacy_gateway.update_settings(privacy_mode="cloud_assisted", allow_cloud_transfers=False)
    allowed, reason = privacy_gateway.can_transfer_to_cloud("veo", "video_generation")
    assert allowed is False
    assert "switch is disabled" in reason

    # Cloud transfers enabled and in allowlist
    privacy_gateway.update_settings(privacy_mode="cloud_assisted", allow_cloud_transfers=True, allowlist=["veo", "gemini"])
    allowed, reason = privacy_gateway.can_transfer_to_cloud("veo", "video_generation")
    assert allowed is True

    # Provider not in allowlist
    allowed, reason = privacy_gateway.can_transfer_to_cloud("unauthorized_provider", "video_generation")
    assert allowed is False
    assert "not in cloud allowlist" in reason

def test_checkpoint_persistence_and_update():
    with SessionLocal() as db:
        proj = Project(name="Checkpoint Test Project")
        db.add(proj)
        db.commit()
        project_id = proj.id

        job = Job(
            project_id=project_id,
            job_type="prompt_to_video",
            status="running",
            progress=20,
            current_step="Testing checkpoints",
            checkpoint_data={"completed_scenes": {"scene_1": "D:/temp/scene1.mp4"}}
        )
        db.add(job)
        db.commit()
        job_id = job.id

    # Update job with new checkpoint
    update_job_sync(
        job_id=job_id,
        status="paused",
        progress=50,
        current_step="Paused at scene 2",
        checkpoint_data={"completed_scenes": {"scene_1": "D:/temp/scene1.mp4", "scene_2": "D:/temp/scene2.mp4"}}
    )

    with SessionLocal() as db:
        updated = db.query(Job).filter(Job.id == job_id).first()
        assert updated.status == "paused"
        assert updated.progress == 50
        assert "scene_2" in updated.checkpoint_data["completed_scenes"]
