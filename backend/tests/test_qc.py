from pathlib import Path
from app.services.quality_control.qc_service import qc_service
from app.utils.sample_media import create_sample_video, create_sample_scene_video
from app.core.config import settings

def test_qc_pass_vertical():
    test_file = settings.TEMP_DIR / "qc_test_vertical.mp4"
    create_sample_scene_video(test_file, duration=4.0, width=1080, height=1920)
    
    report = qc_service.evaluate_video(test_file, expected_aspect_ratio="9:16")
    assert report["status"] == "passed"
    assert len(report["issues"]) == 0
    assert report["metrics"]["width"] == 1080
    assert report["metrics"]["height"] == 1920

def test_qc_aspect_ratio_mismatch():
    test_landscape = settings.TEMP_DIR / "qc_test_landscape.mp4"
    create_sample_video(test_landscape, duration=3.0, width=1920, height=1080)
    
    # Expect vertical but supply landscape
    report = qc_service.evaluate_video(test_landscape, expected_aspect_ratio="9:16")
    assert report["status"] == "needs_revision"
    assert any("Aspect ratio violation" in i["message"] for i in report["issues"])

