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
    Generate an animated cinematic gradient scene video in 9:16 vertical format.
    Provides smooth dynamic motion graphics when offline.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dur = max(1.5, float(duration or 5.0))
    w = int(width or 1080)
    h = int(height or 1920)

    palette_pairs = [
        ("0x0f172a", "0x4338ca"), # Dark Slate to Indigo
        ("0x111827", "0x059669"), # Slate to Emerald
        ("0x1e1b4b", "0x7c3aed"), # Deep Violet to Purple
        ("0x18181b", "0xd97706"), # Charcoal to Amber
        ("0x022c22", "0x0d9488"), # Forest to Teal
    ]
    c0, c1 = palette_pairs[(scene_number - 1) % len(palette_pairs)]
    vf = f"gradients=s={w}x{h}:d={dur}:c0={c0}:c1={c1}:speed=0.01"
    args = [
        "-f", "lavfi", "-i", vf,
        "-f", "lavfi", "-i", f"sine=frequency={160 + scene_number * 35}:duration={dur}",
        "-af", "volume=0.15,lowpass=f=800",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", str(dur),
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    if not success or not output_path.exists() or output_path.stat().st_size == 0:
        # Fallback to universal color background
        fallback_vf = f"color=c=0x111827:s={w}x{h}:d={dur}"
        fb_args = [
            "-f", "lavfi", "-i", fallback_vf,
            "-f", "lavfi", "-i", f"sine=frequency=220:duration={dur}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-t", str(dur),
            str(output_path)
        ]
        success, _ = run_ffmpeg(fb_args)
    return success

def create_sample_audio_track(
    output_path: Path,
    duration: float = 30.0,
    track_type: str = "music"
) -> bool:
    """
    Generate ambient synthetic audio track.
    For music: mixes a harmonic ambient chord pad with lowpass smoothing.
    Saves clean uncompressed PCM WAV or AAC depending on extension.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix.lower() == ".wav":
        codec_args = ["-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2"]
    else:
        codec_args = ["-c:a", "aac", "-b:a", "128k"]

    if track_type == "music":
        args = [
            "-f", "lavfi", "-i", f"sine=f=131:d={duration}",
            "-f", "lavfi", "-i", f"sine=f=196:d={duration}",
            "-f", "lavfi", "-i", f"sine=f=262:d={duration}",
            "-filter_complex",
            f"[0:a][1:a][2:a]amix=inputs=3,lowpass=f=650,volume=0.22,afade=t=in:ss=0:d=1,afade=t=out:st={max(0.1, duration - 1.5)}:d=1.5",
            *codec_args,
            str(output_path)
        ]
    else:
        args = [
            "-f", "lavfi",
            "-i", f"sine=frequency=330:duration={duration}",
            "-af", f"volume=0.25,lowpass=f=1200,afade=t=in:ss=0:d=0.2,afade=t=out:st={max(0.1, duration - 0.5)}:d=0.5",
            *codec_args,
            str(output_path)
        ]
    success, _ = run_ffmpeg(args)
    return success
