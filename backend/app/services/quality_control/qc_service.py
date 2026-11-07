from pathlib import Path
from typing import Dict, Any, List
from app.utils.ffprobe import inspect_media
from app.core.logging import logger

class QualityControlService:
    def evaluate_video(
        self,
        video_path: Path,
        expected_aspect_ratio: str = "9:16",
        min_duration: float = 2.0,
        max_duration: float = 120.0,
        require_audio: bool = False
    ) -> Dict[str, Any]:
        """
        Perform strict technical quality control verification on a rendered media file.
        """
        issues: List[Dict[str, str]] = []

        if not video_path.exists() or video_path.stat().st_size == 0:
            return {
                "status": "failed",
                "issues": [{"type": "technical", "message": "Rendered video file is missing or empty (0 bytes)."}],
                "metrics": {}
            }

        try:
            metadata = inspect_media(video_path)
        except Exception as e:
            return {
                "status": "failed",
                "issues": [{"type": "technical", "message": f"Media decode error: {str(e)}"}],
                "metrics": {}
            }

        raw_duration = metadata.get("duration")
        try:
            duration = float(raw_duration) if raw_duration is not None else 0.0
        except (ValueError, TypeError):
            duration = 0.0

        width = metadata.get("width")
        height = metadata.get("height")
        has_audio = metadata.get("has_audio", False)
        has_video = metadata.get("has_video", False)

        if not has_video:
            issues.append({"type": "technical", "message": "Video stream is missing."})

        if require_audio and not has_audio:
            issues.append({"type": "technical", "message": "Audio stream is missing."})

        if duration > 0.0:
            if duration < (min_duration - 0.25):
                issues.append({"type": "technical", "message": f"Video duration ({duration:.1f}s) is shorter than minimum allowed ({min_duration:.1f}s)."})
            elif duration > max_duration:
                issues.append({"type": "technical", "message": f"Video duration ({duration:.1f}s) exceeds maximum allowed ({max_duration:.1f}s)."})
        elif not has_video:
            issues.append({"type": "technical", "message": "Zero or undecodable media duration."})

        # Check aspect ratio
        if width and height:
            if expected_aspect_ratio == "9:16":
                # Height must be greater than width for vertical short format
                if height <= width:
                    issues.append({"type": "technical", "message": f"Aspect ratio violation: Expected vertical 9:16, got {width}x{height}."})
            elif expected_aspect_ratio == "16:9":
                if width <= height:
                    issues.append({"type": "technical", "message": f"Aspect ratio violation: Expected horizontal 16:9, got {width}x{height}."})

        status = "passed" if len(issues) == 0 else "needs_revision"
        logger.info(f"QC check completed for {video_path.name}: {status} ({len(issues)} issues)")

        return {
            "status": status,
            "issues": issues,
            "metrics": {
                "duration": duration,
                "width": width,
                "height": height,
                "aspect_ratio": metadata.get("aspect_ratio"),
                "has_audio": has_audio,
                "fps": metadata.get("fps"),
                "file_size_bytes": video_path.stat().st_size
            }
        }

qc_service = QualityControlService()

