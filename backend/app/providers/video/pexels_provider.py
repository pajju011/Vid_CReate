import os
import re
import uuid
import urllib.parse
import subprocess
import httpx
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.core.cache import asset_cache
from app.services.storage.storage_service import storage_service
from app.services.quality_control.qc_service import qc_service
from app.providers.base import BaseVideoProvider

class PexelsVideoProvider(BaseVideoProvider):
    """
    Real 4K Commercial Stock Video Provider using the Pexels Video API & Pixabay.
    Acquires authentic, high-frame-rate, professional motion video clips
    (sizzling grills, melting cheese, athlete workouts, neon cities) with zero GPU VRAM.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or getattr(settings, "PEXELS_API_KEY", None) or os.getenv("PEXELS_API_KEY", "")).strip()
        self.base_url = "https://api.pexels.com/videos"

    def _extract_smart_keywords(self, prompt: str) -> List[str]:
        """Distills complex prompts into high-relevance stock video search queries."""
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", prompt.lower())
        stopwords = {
            "create", "video", "cinematic", "photorealistic", "ultra", "detailed", "realistic",
            "close", "shots", "smooth", "camera", "movements", "lighting", "warm", "format",
            "perfect", "instagram", "reels", "shorts", "youtube", "second", "seconds", "scene",
            "appetizing", "engaging", "showing", "being", "added", "served", "with", "from",
            "features", "featuring", "show", "make", "make", "take", "look", "looking"
        }
        words = [w for w in clean.split() if len(w) > 2 and w not in stopwords]

        # Domain query rules
        lower = prompt.lower()
        queries = []
        if any(w in lower for w in ["patty", "sizzling", "grill"]):
            queries.append("burger patty grill sizzling")
            queries.append("meat sizzling grill")
        elif any(w in lower for w in ["lettuce", "tomato", "vegetables", "toppings"]):
            queries.append("fresh vegetables cutting food")
            queries.append("burger lettuce tomato prep")
        elif any(w in lower for w in ["cheese", "melted", "dripping"]):
            queries.append("melted cheese burger")
            queries.append("cheese melting food")
        elif any(w in lower for w in ["burger", "cheeseburger"]):
            queries.append("delicious gourmet burger served")
            queries.append("eating burger restaurant")
        elif any(w in lower for w in ["pizza", "dough", "crust"]):
            queries.append("pizza baking oven dough")
            queries.append("pizza cheese pull slice")
        elif any(w in lower for w in ["fitness", "workout", "gym", "exercise"]):
            queries.append("athlete training gym workout")
            queries.append("running fitness pulse")
        elif any(w in lower for w in ["smartwatch", "tracker", "biometric", "wearable"]):
            queries.append("smartwatch fitness tracker technology")
            queries.append("wearable device glowing tech")

        if words:
            queries.append(" ".join(words[:3]))
            queries.append(" ".join(words[:2]))

        queries.append("cinematic lifestyle motion")
        return queries

    def _search_pexels(self, query: str) -> Optional[str]:
        """Search Pexels API for authentic video download link."""
        if not self.api_key:
            return None

        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": 5,
            "orientation": "portrait"
        }

        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                res = client.get(f"{self.base_url}/search", headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    videos = data.get("videos", [])
                    if not videos:
                        # Try landscape orientation if portrait returns no results
                        params["orientation"] = "landscape"
                        res = client.get(f"{self.base_url}/search", headers=headers, params=params)
                        if res.status_code == 200:
                            videos = res.json().get("videos", [])

                    for v in videos:
                        files = v.get("video_files", [])
                        # Prefer HD/Full-HD mp4 file
                        for f in files:
                            if f.get("file_type") == "video/mp4" and f.get("link"):
                                if f.get("width", 0) >= 720:
                                    logger.info(f"[Pexels] Found matching video stream for '{query}' ({f.get('width')}x{f.get('height')})")
                                    return f.get("link")
                        if files and files[0].get("link"):
                            return files[0].get("link")
        except Exception as e:
            logger.warning(f"[Pexels] Video search query error ({e}) for '{query}'")
        return None

    def _search_pixabay(self, query: str) -> Optional[str]:
        """Fallback to Pixabay Video API."""
        pixabay_key = getattr(settings, "PIXABAY_API_KEY", None) or os.getenv("PIXABAY_API_KEY", "")
        if not pixabay_key:
            return None

        params = {
            "key": pixabay_key,
            "q": query,
            "per_page": 5,
            "video_type": "film"
        }
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                res = client.get("https://pixabay.com/api/videos/", params=params)
                if res.status_code == 200:
                    hits = res.json().get("hits", [])
                    for h in hits:
                        vids = h.get("videos", {})
                        for q in ["large", "medium", "small"]:
                            if vids.get(q, {}).get("url"):
                                return vids[q]["url"]
        except Exception as e:
            logger.warning(f"[Pixabay] Video search error: {e}")
        return None

    def _adapt_to_vertical_format(
        self,
        raw_video_path: Path,
        output_path: Path,
        duration_seconds: float,
        target_width: int = 1080,
        target_height: int = 1920
    ) -> bool:
        """
        Uses FFmpeg to crop, scale, and center landscape footage into vertical 9:16
        with smooth ambient blurred background canvas if aspect ratios differ.
        """
        tw = target_width
        th = target_height
        dur = max(2.0, float(duration_seconds))

        filter_complex = (
            f"[0:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},boxblur=25:5[bg];"
            f"[0:v]scale={tw}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
        )

        cmd = [
            settings.FFMPEG_PATH, "-y",
            "-ss", "0.5",
            "-i", str(raw_video_path),
            "-t", str(dur),
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-f", "lavfi", "-i", f"sine=f=220:d={dur}",
            "-af", "volume=0.0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            return output_path.exists() and output_path.stat().st_size > 5000
        except Exception as e:
            logger.error(f"[Pexels] Video vertical adaptation error: {e}")
            return False

    def generate_video(
        self,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Searches, downloads, and crops real commercial stock footage matching the scene prompt.
        """
        dur = max(2.0, float(duration_seconds or 5.0))
        tw = width if width else (1080 if aspect_ratio == "9:16" else 1920)
        th = height if height else (1920 if aspect_ratio == "9:16" else 1080)

        # Check asset cache
        cached = asset_cache.get_cached_video(prompt, "pexels", dur, aspect_ratio)
        if cached and cached.exists():
            return {
                "job_id": f"cached_{cached.stem}",
                "status": "completed",
                "progress": 100,
                "video_path": str(cached),
                "is_demo_asset": False,
                "provider": "pexels_cache",
                "cached": True
            }

        job_id = f"pexels_{uuid.uuid4().hex[:8]}"
        queries = self._extract_smart_keywords(prompt)

        download_url = None
        for q in queries:
            download_url = self._search_pexels(q)
            if download_url:
                break
            download_url = self._search_pixabay(q)
            if download_url:
                break

        out_path = storage_service.create_temp_path(prefix=job_id, suffix=".mp4")

        if download_url:
            raw_temp = storage_service.create_temp_path(prefix="pexels_raw", suffix=".mp4")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                with httpx.Client(timeout=35.0, follow_redirects=True) as client:
                    resp = client.get(download_url, headers=headers)
                    if resp.status_code == 200 and len(resp.content) > 100000:
                        raw_temp.write_bytes(resp.content)
                        success = self._adapt_to_vertical_format(raw_temp, out_path, dur, tw, th)
                        raw_temp.unlink(missing_ok=True)
                        if success:
                            logger.info(f"[Pexels] Successfully created authentic motion video for '{prompt[:40]}'")
                            asset_cache.store_cached_video(prompt, "pexels", dur, aspect_ratio, out_path)
                            return {
                                "job_id": job_id,
                                "status": "completed",
                                "progress": 100,
                                "video_path": str(out_path),
                                "is_demo_asset": False,
                                "provider": "pexels_4k",
                                "cached": False,
                                "motion_type": "authentic_commercial_motion"
                            }
            except Exception as e:
                logger.warning(f"[Pexels] Download/adaptation failed ({e})")
                raw_temp.unlink(missing_ok=True)

        # Fallback cascade to 3D Depth Parallax if stock API key is unavailable or returned no results
        logger.info(f"[Pexels] Stock video API unavailable or no match found for '{prompt[:40]}'; smoothly cascading to OmniForge 3D Depth Parallax...")
        try:
            from app.providers.video.omni_provider import OmniForgeVideoProvider
            omni = OmniForgeVideoProvider()
            return omni.generate_video(prompt, dur, aspect_ratio, tw, th)
        except Exception as cascade_err:
            logger.warning(f"[Pexels] Cascade to OmniForge failed ({cascade_err})")

        return {
            "job_id": job_id,
            "status": "failed",
            "progress": 0,
            "video_path": None,
            "error": "No stock video match found or API offline"
        }

    def generate_video_from_image(self, image_path: Path, prompt: str, duration_seconds: float, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        return self.generate_video(prompt, duration_seconds, aspect_ratio)

    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        return {"job_id": job_id, "status": "completed", "progress": 100}

    def download_generated_video(self, video_url: str, destination_path: Path) -> bool:
        src = Path(video_url)
        if src.exists():
            import shutil
            shutil.copy(src, destination_path)
            return True
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                res = client.get(video_url)
                if res.status_code == 200:
                    destination_path.write_bytes(res.content)
                    return True
        except Exception:
            pass
        return False

    def cancel_generation(self, job_id: str) -> bool:
        return True
