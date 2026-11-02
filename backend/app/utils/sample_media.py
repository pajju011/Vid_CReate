import math
from pathlib import Path
from app.core.config import settings
from app.utils.ffmpeg import run_ffmpeg

def create_sample_video(
    output_path: Path,
    duration: float = 15.0,
    width: int = 1920,
    height: int = 1080,
    text: str = "ClipForge AI Sample Footage",
    fps: int = 30
) -> bool:
    """
    Generate a deterministic synthetic test video using FFmpeg testsrc & sine audio filter.
    Useful for local offline testing, demo mode, and CI verification.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Using testsrc + drawtext + sine wave audio
    # Safe escaping for drawtext
    clean_text = text.replace(":", "\\:").replace("'", "")
    vf = (
        f"testsrc=duration={duration}:size={width}x{height}:rate={fps},"
        f"drawtext=text='{clean_text}':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/2,"
        f"drawtext=text='%{{pts\\:hms}}':fontcolor=yellow:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2+80"
    )
    args = [
        "-f", "lavfi", "-i", vf,
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    return success

def create_sample_scene_video(
    output_path: Path,
    duration: float = 5.0,
    scene_number: int = 1,
    purpose: str = "Hook",
    caption: str = "AI Video Generation",
    width: int = 1080,
    height: int = 1920
) -> bool:
    """
    Generate a sample scene video in 9:16 vertical format with gradients,
    scene numbers, and simulated motion.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Generate colorful background with testsrc2 and animated zoom/pan
    colors = ["blue", "purple", "darkred", "teal", "indigo"]
    color = colors[(scene_number - 1) % len(colors)]
    clean_caption = caption.replace(":", "\\:").replace("'", "")
    vf = (
        f"color=c={color}:size={width}x{height}:duration={duration}:rate=30,"
        f"drawtext=text='Scene {scene_number} - {purpose}':fontcolor=white:fontsize=64:bold=1:x=(w-text_w)/2:y=300,"
        f"drawtext=text='{clean_caption}':fontcolor=yellow:fontsize=52:box=1:boxcolor=black@0.7:boxborderw=12:x=(w-text_w)/2:y=h-400"
    )
    args = [
        "-f", "lavfi", "-i", vf,
        "-f", "lavfi", "-i", f"sine=frequency={300 + scene_number * 50}:duration={duration}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    return success

def create_sample_audio_track(
    output_path: Path,
    duration: float = 30.0,
    track_type: str = "music" # music | narration
) -> bool:
    """Generate ambient synthetic audio track."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    freq = "220" if track_type == "music" else "330"
    args = [
        "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={duration}",
        "-af", "volume=0.3,afade=t=in:ss=0:d=1,afade=t=out:st=28:d=2",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    return success
