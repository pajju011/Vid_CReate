import os
import shutil
from pathlib import Path
import pytest
from app.core.config import settings
from app.services.storage.storage_service import storage_service

def test_storage_directories_strictly_outside_project():
    """Verify that storage paths and temp paths are outside the project directory."""
    project_root = settings.BASE_DIR.resolve()
    
    # Assert external storage is outside project
    resolved_storage = storage_service.media_storage_path.resolve()
    resolved_temp = storage_service.temp_media_path.resolve()

    assert not str(resolved_storage).startswith(str(project_root)), "Storage dir must be outside project"
    assert not str(resolved_temp).startswith(str(project_root)), "Temp dir must be outside project"
    
    # Check assert_not_in_project validation
    with pytest.raises(Exception):
        storage_service.assert_not_in_project(project_root / "test.mp4")

def test_temp_path_allocation_and_final_promotion():
    """Verify that temp files are created in temp_media_path and promoted to renders_dir."""
    job_id = "test-job-storage-123"
    
    # 1. Create a temp video
    temp_video = storage_service.create_temp_path(prefix="render_test", suffix=".mp4", job_id=job_id)
    assert temp_video.exists() is False
    assert storage_service.temp_media_path in temp_video.parents or str(storage_service.temp_media_path) in str(temp_video)
    
    # Write dummy content to simulate rendering
    temp_video.write_bytes(b"dummy mp4 video binary stream data")
    assert temp_video.exists() is True
    
    # 2. Promote to final video in external storage
    final_video = storage_service.save_final_video(temp_video, filename="final_reel_123.mp4")
    assert final_video.exists() is True
    assert final_video.parent == storage_service.renders_dir
    assert final_video.read_bytes() == b"dummy mp4 video binary stream data"
    
    # Original temp file must be moved (no longer in temp)
    assert temp_video.exists() is False
    
    # 3. Clean up final video
    deleted = storage_service.delete_file(final_video)
    assert deleted is True
    assert final_video.exists() is False

def test_job_temp_cleanup_isolation():
    """Verify that cleanup_job_temp_files only purges temp files belonging to that job."""
    job_a = "job-a-999"
    job_b = "job-b-888"
    
    file_a = storage_service.create_temp_path(prefix="clip", suffix=".mp4", job_id=job_a)
    file_b = storage_service.create_temp_path(prefix="clip", suffix=".mp4", job_id=job_b)
    
    file_a.write_text("job a temp data")
    file_b.write_text("job b temp data")
    
    assert file_a.exists() is True
    assert file_b.exists() is True
    
    # Cleanup only job_a
    cleaned = storage_service.cleanup_job_temp_files(job_a)
    assert cleaned >= 1
    assert file_a.exists() is False
    assert file_b.exists() is True # job b must NOT be touched
    
    # Cleanup job_b
    storage_service.cleanup_job_temp_files(job_b)
    assert file_b.exists() is False

def test_storage_stats_report():
    """Verify that get_storage_stats returns accurate disk metrics and external flag."""
    stats = storage_service.get_storage_stats()
    assert "total_gb" in stats
    assert "free_gb" in stats
    assert stats["total_gb"] > 0
    assert stats["free_gb"] > 0
    assert stats["is_outside_project"] is True
    assert "media_storage_path" in stats
    assert "temp_media_path" in stats

def test_workspace_free_of_generated_media():
    """Verify that no generated media files exist within the project directory."""
    project_root = settings.BASE_DIR.resolve()
    
    media_extensions = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
    found_media = []
    
    # Scan project root, backend, frontend (excluding node_modules or venv)
    for root, dirs, files in os.walk(project_root):
        # Skip node_modules, venv, .git, scratch
        dirs[:] = [d for d in dirs if d not in {"node_modules", "venv", ".git", ".pytest_cache", "scratch"}]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in media_extensions:
                found_media.append(os.path.join(root, f))
                
    assert len(found_media) == 0, f"Found generated media files inside workspace: {found_media}"

