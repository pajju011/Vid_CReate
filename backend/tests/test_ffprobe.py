import pytest
from pathlib import Path
from app.utils.ffprobe import inspect_media
from app.utils.sample_media import create_sample_video
from app.core.config import settings

def test_inspect_media_valid():
    test_video = settings.TEMP_DIR / "test_ffprobe.mp4"
    create_sample_video(test_video, duration=3.0, width=1280, height=720)
    
    meta = inspect_media(test_video)
    assert meta["has_video"] is True
    assert meta["has_audio"] is True
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["duration"] >= 2.8
    assert "video_codec" in meta

def test_inspect_media_nonexistent():
    fake_path = settings.TEMP_DIR / "nonexistent.mp4"
    with pytest.raises(FileNotFoundError):
        inspect_media(fake_path)

