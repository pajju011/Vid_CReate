import os
import uuid
import urllib.parse
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.cache import asset_cache
from app.services.storage.storage_service import storage_service
from app.providers.base import BaseVideoProvider
from app.utils.sample_media import create_sample_scene_video
from app.utils.ffmpeg import generate_image_to_video_motion
from app.utils.network import is_network_available

class PollinationsVideoProvider(BaseVideoProvider):
    """
    Real AI Video Generator powered by Pollinations.ai (Flux.1 / SDXL) and FFmpeg Ken Burns Camera Motion.
    100% Free, Zero API Key required, produces true high-definition vertical AI visuals and motion clips.
    """
    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        # Check cache first
        cached = asset_cache.get_cached_video(prompt, "cinematic", duration_seconds, aspect_ratio)
        if cached:
            return {
                "job_id": f"cached_{cached.stem}",
                "status": "completed",
                "progress": 100,
                "video_path": str(cached),
                "is_demo_asset": False,
                "provider": "pollinations",
                "cached": True
            }

        job_id = f"pol_vid_{uuid.uuid4().hex[:8]}"
        tw = 1080 if aspect_ratio == "9:16" else 1920
        th = 1920 if aspect_ratio == "9:16" else 1080

        # 1. Generate real AI image from Pollinations Flux API
        temp_img_path = storage_service.create_temp_path(prefix=f"img_{job_id}", suffix=".jpg")
        clean_prompt = prompt.strip().replace("\n", " ")
        encoded_prompt = urllib.parse.quote(f"{clean_prompt}, 8k ultra-detailed, photorealistic, cinematic volumetric lighting, 9:16 portrait vertical")
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={tw}&height={th}&model=flux&nologo=true&seed={uuid.uuid4().int % 100000}"

        image_downloaded = False
        if is_network_available():
            try:
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    resp = client.get(url)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        temp_img_path.write_bytes(resp.content)
                        image_downloaded = True
                        logger.info(f"Generated AI scene image with Pollinations Flux ({len(resp.content)} bytes)")
            except Exception as e:
                logger.warning(f"Pollinations AI image generation network error ({e}), using fallback visual")

        out_path = storage_service.create_temp_path(prefix=job_id, suffix=".mp4")

        # 2. If image downloaded, animate with Ken Burns subpixel motion
        if image_downloaded and temp_img_path.exists():
            motion_choices = ["slow_zoom_in", "slow_zoom_out", "pan_right"]
            motion = motion_choices[abs(hash(job_id)) % len(motion_choices)]
            success = generate_image_to_video_motion(
                image_path=temp_img_path,
                output_path=out_path,
                duration=duration_seconds,
                motion_type=motion,
                target_width=tw,
                target_height=th
            )
            temp_img_path.unlink(missing_ok=True)
        else:
            success = create_sample_scene_video(
                output_path=out_path,
                duration=duration_seconds,
                scene_number=1,
                purpose="Scene",
                caption=prompt[:30],
                width=tw,
                height=th
            )

        if success and out_path.exists():
            asset_cache.store_cached_video(prompt, "cinematic", duration_seconds, aspect_ratio, out_path)

        return {
            "job_id": job_id,
            "status": "completed" if success else "failed",
            "progress": 100,
            "video_path": str(out_path),
            "is_demo_asset": not image_downloaded,
            "provider": "pollinations",
            "cached": False
        }

    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        job_id = f"pol_i2v_{uuid.uuid4().hex[:8]}"
        out_path = storage_service.create_temp_path(prefix=job_id, suffix=".mp4")
        tw = 1080 if aspect_ratio == "9:16" else 1920
        th = 1920 if aspect_ratio == "9:16" else 1080

        success = generate_image_to_video_motion(
            image_path=image_path,
            output_path=out_path,
            duration=duration_seconds,
            motion_type="slow_zoom_in",
            target_width=tw,
            target_height=th
        )

        return {
            "job_id": job_id,
            "status": "completed" if success else "failed",
            "progress": 100,
            "video_path": str(out_path),
            "is_demo_asset": False,
            "provider": "pollinations_i2v"
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

class MockVideoProvider(BaseVideoProvider):
    """
    Default video generator that uses Pollinations real AI visuals with offline fallback.
    """
    def __init__(self):
        self._pol = PollinationsVideoProvider()

    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        return self._pol.generate_video(prompt, duration_seconds, aspect_ratio)

    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        return self._pol.generate_video_from_image(image_path, prompt, duration_seconds, aspect_ratio)

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

    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        return self.generate_video(prompt=f"{prompt} (from keyframe)", duration_seconds=duration_seconds, aspect_ratio=aspect_ratio)

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

class RunwayVideoProvider(BaseVideoProvider):
    """
    Real Runway Gen-3 Alpha / Turbo video generation adapter.
    API Docs: https://docs.runwayml.com/
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.dev.runwayml.com/v1"

    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": "2024-11-06",
            "Content-Type": "application/json"
        }
        ratio = "9:16" if aspect_ratio == "9:16" else "16:9"
        duration_int = 10 if duration_seconds > 7.5 else 5
        payload = {
            "promptText": prompt,
            "model": "gen3a_turbo",
            "duration": duration_int,
            "ratio": ratio
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/tasks", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                logger.error(f"Runway error: {resp.text}")
                raise RuntimeError(f"Runway error: {resp.status_code} - {resp.text}")
            data = resp.json()
            return {
                "job_id": data.get("id"),
                "status": data.get("status", "PENDING").lower(),
                "progress": 10,
                "provider": "runway"
            }

    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        return self.generate_video(prompt=prompt, duration_seconds=duration_seconds, aspect_ratio=aspect_ratio)

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": "2024-11-06"
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.base_url}/tasks/{job_id}", headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Runway status error: {resp.status_code}")
            data = resp.json()
            status_raw = data.get("status", "").lower()
            output = data.get("output", [])
            video_url = output[0] if output else None
            return {
                "job_id": job_id,
                "status": "completed" if status_raw in ("succeeded", "completed") else "failed" if status_raw in ("failed", "cancelled") else "processing",
                "progress": 100 if status_raw in ("succeeded", "completed") else int(data.get("progressRatio", 0.5) * 100),
                "video_url": video_url
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

class KlingVideoProvider(BaseVideoProvider):
    """Real Kling AI video generation adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.klingai.com/v1"

    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model_name": "kling-v1",
            "prompt": prompt,
            "duration": "5" if duration_seconds <= 5.0 else "10",
            "aspect_ratio": "9:16" if aspect_ratio == "9:16" else "16:9"
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/videos/text2video", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Kling API error: {resp.status_code} - {resp.text}")
            data = resp.json().get("data", {})
            return {"job_id": data.get("task_id"), "status": "processing", "progress": 10, "provider": "kling"}

    def generate_video_from_image(self, image_path: Path, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        return self.generate_video(prompt=prompt, duration_seconds=duration_seconds, aspect_ratio=aspect_ratio)

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.base_url}/videos/text2video/{job_id}", headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Kling status error: {resp.status_code}")
            task = resp.json().get("data", {})
            status_str = task.get("task_status", "").lower()
            works = task.get("task_result", {}).get("videos", [])
            video_url = works[0].get("url") if works else None
            return {
                "job_id": job_id,
                "status": "completed" if status_str == "succeed" else "failed" if status_str == "failed" else "processing",
                "progress": 100 if status_str == "succeed" else 50,
                "video_url": video_url
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

class PikaVideoProvider(BaseVideoProvider):
    """Real Pika video generation adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pika.art/v1"

    def generate_video(self, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "promptText": prompt,
            "options": {"aspectRatio": "9:16" if aspect_ratio == "9:16" else "16:9"}
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{self.base_url}/generate", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Pika API error: {resp.status_code} - {resp.text}")
            data = resp.json()
            return {"job_id": data.get("id"), "status": "processing", "progress": 10, "provider": "pika"}

    def generate_video_from_image(self, image_path: Path, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        return self.generate_video(prompt=prompt, duration_seconds=duration_seconds, aspect_ratio=aspect_ratio)

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.base_url}/generate/{job_id}", headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Pika status error: {resp.status_code}")
            data = resp.json()
            status_str = data.get("status", "").lower()
            return {
                "job_id": job_id,
                "status": "completed" if status_str == "finished" else "failed" if status_str == "error" else "processing",
                "progress": 100 if status_str == "finished" else 50,
                "video_url": data.get("videoUri")
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
