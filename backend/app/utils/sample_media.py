from pathlib import Path
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
    Fast, reliable, zero fontconfig dependency.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vf = f"testsrc=duration={duration}:size={width}x{height}:rate={fps}"
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
    Generate a sample scene video in 9:16 vertical format.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    colors = ["blue", "purple", "darkred", "teal", "indigo"]
    color = colors[(scene_number - 1) % len(colors)]
    vf = f"color=c={color}:size={width}x{height}:duration={duration}:rate=30"
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
    track_type: str = "music"
) -> bool:
    """
    Generate ambient synthetic audio track.
    Saves clean uncompressed PCM WAV or AAC depending on extension.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    freq = "220" if track_type == "music" else "330"
    
    # If .wav, use standard pcm_s16le to ensure 100% valid WAV RIFF container
    if output_path.suffix.lower() == ".wav":
        codec_args = ["-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2"]
    else:
        codec_args = ["-c:a", "aac", "-b:a", "128k"]

    args = [
        "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={duration}",
        "-af", f"volume=0.3,afade=t=in:ss=0:d=1,afade=t=out:st={max(0.1, duration - 1.5)}:d=1.5",
        *codec_args,
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    return success
