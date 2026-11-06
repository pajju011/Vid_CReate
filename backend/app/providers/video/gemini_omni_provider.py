import os
import uuid
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.cache import asset_cache
from app.services.storage.storage_service import storage_service
from app.services.quality_control.qc_service import qc_service
from app.providers.base import BaseVideoProvider
from app.utils.network import is_network_available

class GeminiOmniVideoProvider(BaseVideoProvider):
    """
    Direct native integration with Google GenAI Gemini Omni Video Generation.
    Model: models/gemini-omni-1.2-flash via Google GenAI Interactions API.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.model_name = "models/gemini-omni-1.2-flash"

    def generate_video(
        self,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        job_id = f"gemini_omni_{uuid.uuid4().hex[:8]}"
        out_path = storage_service.create_temp_path(prefix=job_id, suffix=".mp4")
        dur_str = f"{max(5, min(15, int(duration_seconds)))}s"

        logger.info(f"[Gemini Omni] Requesting video generation for prompt: '{prompt[:60]}...' ({dur_str})")

        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            generation_config = {'max_output_tokens': 65536}

            candidate_models = [
                self.model_name,
                "models/gemini-omni-1.1-flash",
                "gemini-omni-1.1-flash",
                "models/gemini-2.0-flash-exp"
            ]

            interaction = None
            last_err = None
            for m in candidate_models:
                try:
                    interaction = client.interactions.create(
                        model=m,
                        input=f"{prompt}, cinematic 8k quality, aspect ratio {aspect_ratio}",
                        generation_config=generation_config,
                        response_modalities=['video'],
                        response_format={
                            'type': 'video',
                            'duration': dur_str,
                        },
                    )
                    logger.info(f"[Gemini Omni] Successfully invoked model '{m}'")
                    break
                except Exception as m_err:
                    last_err = m_err
                    logger.warning(f"[Gemini Omni] Model '{m}' attempt: {m_err}")

            if not interaction:
                raise last_err or RuntimeError("Failed to invoke any Gemini Omni model.")

            video_saved = False
            for step in getattr(interaction, 'steps', []):
                if getattr(step, 'type', None) == 'model_output' and getattr(step, 'content', None):
                    for part in step.content:
                        part_type = getattr(part, 'type', None)
                        if part_type == 'text':
                            logger.info(f"[Gemini Omni] Text: {getattr(part, 'text', '')}")
                        elif part_type == 'video':
                            data = getattr(part, 'data', None)
                            if data:
                                if isinstance(data, str):
                                    raw_bytes = base64.b64decode(data)
                                elif isinstance(data, bytes):
                                    try:
                                        raw_bytes = base64.b64decode(data)
                                    except Exception:
                                        raw_bytes = data
                                else:
                                    raw_bytes = bytes(data)

                                with open(out_path, "wb") as f:
                                    f.write(raw_bytes)

                                logger.info(f"[Gemini Omni] Saved video output ({len(raw_bytes)} bytes) to {out_path}")
                                video_saved = True
                                break
                    if video_saved:
                        break

            if video_saved and out_path.exists() and out_path.stat().st_size > 1000:
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "progress": 100,
                    "video_path": str(out_path),
                    "is_demo_asset": False,
                    "provider": "gemini-omni-1.2-flash"
                }

        except Exception as e:
            logger.warning(f"[Gemini Omni] Generation API error ({e})")

        return {
            "job_id": job_id,
            "status": "failed",
            "progress": 0,
            "video_path": None,
            "error": "Failed to generate video with gemini-omni-1.2-flash"
        }

    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        return self.generate_video(prompt=f"{prompt} (from reference image)", duration_seconds=duration_seconds, aspect_ratio=aspect_ratio)

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

