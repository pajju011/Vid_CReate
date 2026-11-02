import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

def inspect_media(file_path: Path) -> Dict[str, Any]:
    """
    Safely inspect video/audio file using ffprobe with argument array.
    Returns parsed metadata dict or raises ValueError if invalid media.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Media file does not exist: {file_path}")

    cmd = [
        settings.FFPROBE_PATH,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe inspection failed for {file_path}: {e.stderr}")
        raise ValueError(f"Invalid or corrupted media file: {e.stderr}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse ffprobe metadata: {e}")

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream and not audio_stream:
        raise ValueError("Media file contains neither video nor audio streams.")

    width = int(video_stream.get("width")) if video_stream and video_stream.get("width") else None
    height = int(video_stream.get("height")) if video_stream and video_stream.get("height") else None

    # Calculate duration
    duration = None
    if "duration" in format_info:
        try:
            duration = float(format_info["duration"])
        except (ValueError, TypeError):
            pass
    if duration is None and video_stream and "duration" in video_stream:
        try:
            duration = float(video_stream["duration"])
        except (ValueError, TypeError):
            pass

    # Calculate frame rate
    fps = None
    if video_stream and "r_frame_rate" in video_stream:
        try:
            num, den = video_stream["r_frame_rate"].split("/")
            fps = round(float(num) / float(den), 2) if float(den) > 0 else 30.0
        except Exception:
            fps = 30.0

    aspect_ratio = None
    if width and height:
        aspect_ratio = f"{width}:{height}"

    return {
        "duration": duration or 0.0,
        "width": width,
        "height": height,
        "fps": fps,
        "aspect_ratio": aspect_ratio,
        "video_codec": video_stream.get("codec_name") if video_stream else None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "has_audio": audio_stream is not None,
        "has_video": video_stream is not None,
        "bitrate": int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None,
        "size_bytes": int(format_info.get("size", 0)) if format_info.get("size") else file_path.stat().st_size,
        "format_name": format_info.get("format_name"),
        "raw_streams": streams
    }
