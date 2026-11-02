import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class AssetCache:
    """
    Persistent content-addressable cache for generated video clips and audio.
    Prevents duplicate API calls and GPU rendering for identical prompt/style combinations.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        from app.services.storage.storage_service import storage_service
        self.cache_dir = cache_dir or storage_service.cache_dir
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _compute_key(self, namespace: str, params: Dict[str, Any]) -> str:
        serialized = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{namespace}_{digest}"

    def get_cached_video(self, prompt: str, style: str, duration: float, aspect_ratio: str) -> Optional[Path]:
        key = self._compute_key("video", {
            "prompt": prompt.strip().lower(),
            "style": style.strip().lower(),
            "duration": round(duration, 1),
            "aspect_ratio": aspect_ratio
        })
        candidate = self.cache_dir / f"{key}.mp4"
        if candidate.exists() and candidate.stat().st_size > 1024:
            logger.info(f"Asset cache HIT for video clip [{key[:16]}]")
            return candidate
        return None

    def store_cached_video(self, prompt: str, style: str, duration: float, aspect_ratio: str, video_path: Path) -> Path:
        if not video_path.exists():
            return video_path
        key = self._compute_key("video", {
            "prompt": prompt.strip().lower(),
            "style": style.strip().lower(),
            "duration": round(duration, 1),
            "aspect_ratio": aspect_ratio
        })
        dest = self.cache_dir / f"{key}.mp4"
        try:
            shutil.copyfile(video_path, dest)
            logger.info(f"Stored video clip in asset cache: {dest.name}")
            return dest
        except Exception as e:
            logger.warning(f"Failed to store video in cache: {e}")
            return video_path

    def get_cached_audio(self, text: str, voice: str) -> Optional[Path]:
        key = self._compute_key("audio", {
            "text": text.strip().lower(),
            "voice": voice.strip().lower()
        })
        candidate = self.cache_dir / f"{key}.wav"
        if candidate.exists() and candidate.stat().st_size > 512:
            logger.info(f"Asset cache HIT for audio [{key[:16]}]")
            return candidate
        return None

    def store_cached_audio(self, text: str, voice: str, audio_path: Path) -> Path:
        if not audio_path.exists():
            return audio_path
        key = self._compute_key("audio", {
            "text": text.strip().lower(),
            "voice": voice.strip().lower()
        })
        dest = self.cache_dir / f"{key}.wav"
        try:
            shutil.copyfile(audio_path, dest)
            return dest
        except Exception as e:
            logger.warning(f"Failed to store audio in cache: {e}")
            return audio_path

asset_cache = AssetCache()

