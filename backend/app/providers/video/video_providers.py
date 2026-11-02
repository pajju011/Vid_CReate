import os
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseVideoProvider
from app.utils.sample_media import create_sample_scene_video

class MockVideoProvider(BaseVideoProvider):
    """
    Local video generator that creates deterministic vertical scene videos
    using FFmpeg. Used for offline testing and demo mode.
    """
    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        job_id = f"mock_vid_{uuid.uuid4().hex[:8]}"
        out_path = settings.TEMP_DIR / f"{job_id}.mp4"
        success = create_sample_scene_video(
            output_path=out_path,
            duration=duration_seconds,
            scene_number=1,
            purpose="Scene",
            caption=prompt[:30],
            width=1080 if aspect_ratio == "9:16" else 1920,
            height=1920 if aspect_ratio == "9:16" else 1080
        )
        return {
            "job_id": job_id,
            "status": "completed" if success else "failed",
            "progress": 100,
            "video_path": str(out_path),
            "is_demo_asset": True,
            "provider": "mock"
        }

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        return {"job_id": job_id, "status": "completed", "progress": 100}

    def download_generated_video(self, video_url: str, destination_path: Path) -> bool:
        src = Path(video_url)
        if src.exists():
            import shutil
            shutil.copy(src, destination_path)
            return True
        return False

    def cancel_generation(self, job_id: str) -> bool:
        return True

class LumaVideoProvider(BaseVideoProvider):
    """
    Real Luma AI Dream Machine video generation adapter.
    API Docs: https://docs.lumalabs.ai/reference/generate-video
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.lumalabs.ai/dream-machine/v1"

    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "aspect_ratio": "9:16" if aspect_ratio == "9:16" else "16:9",
            "loop": False
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/generations", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                logger.error(f"Luma API generation error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Luma API error: {resp.status_code} - {resp.text}")
            data = resp.json()
            return {
                "job_id": data.get("id"),
                "status": data.get("state", "queued"),
                "progress": 10,
                "provider": "luma"
            }

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.base_url}/generations/{job_id}", headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Luma status error: {resp.status_code}")
            data = resp.json()
            state = data.get("state")
            assets = data.get("assets", {})
            return {
                "job_id": job_id,
                "status": "completed" if state == "completed" else "failed" if state == "failed" else "processing",
                "progress": 100 if state == "completed" else 50,
                "video_url": assets.get("video")
            }

    def download_generated_video(self, video_url: str, destination_path: Path) -> bool:
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(video_url)
            if resp.status_code == 200:
                destination_path.write_bytes(resp.content)
                return True
        return False

    def cancel_generation(self, job_id: str) -> bool:
        return True
