import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger

def run_ffmpeg(args: List[str]) -> Tuple[bool, str]:
    """Execute FFmpeg with an argument array and return (success, stderr_output)."""
    cmd = [settings.FFMPEG_PATH, "-y"] + args
    logger.debug(f"Executing FFmpeg: {' '.join(cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return True, proc.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed: {e.stderr}")
        return False, e.stderr

def extract_thumbnail(video_path: Path, output_image_path: Path, timestamp: float = 1.0) -> bool:
    """Extract a single frame image thumbnail at timestamp."""
    args = [
        "-ss", str(max(0.0, timestamp)),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(output_image_path)
    ]
    success, _ = run_ffmpeg(args)
    return success

def extract_audio(video_path: Path, output_audio_path: Path) -> bool:
    """Extract audio track as 16kHz mono WAV suitable for Whisper or other transcription engines."""
    args = [
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_audio_path)
    ]
    success, _ = run_ffmpeg(args)
    return success

def trim_video(
    source_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float
) -> bool:
    """Extract a trimmed segment from start_time to end_time."""
    duration = max(0.1, end_time - start_time)
    args = [
        "-ss", str(max(0.0, start_time)),
        "-i", str(source_path),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    success, _ = run_ffmpeg(args)
    return success

def convert_to_vertical(
    input_path: Path,
    output_path: Path,
    mode: str = "smart", # "smart", "center", "blurred_background"
    crop_x_offset: Optional[float] = None, # 0.0 to 1.0 normalized x offset for center of crop
    target_width: int = 1080,
    target_height: int = 1920,
    subtitle_ass_path: Optional[Path] = None,
    bg_music_path: Optional[Path] = None,
    bg_music_volume: float = 0.15
) -> bool:
    """
    Convert video to vertical (9:16) format with optional blurred background,
    face/smart crop, and subtitle burning.
    """
    if mode == "blurred_background":
        vf = (
            f"[0:v]split=2[bg_src][fg_src];"
            f"[bg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},boxblur=20:20[bg];"
            f"[fg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
        )
    elif mode == "smart" and crop_x_offset is not None:
        vf = (
            f"[0:v]scale=-1:{target_height},"
            f"crop={target_width}:{target_height}:'min(max(0, (in_w * {crop_x_offset}) - {target_width}/2), in_w - {target_width})':0[outv]"
        )
    else:
        vf = (
            f"[0:v]scale=-1:{target_height},"
            f"crop={target_width}:{target_height}:(in_w-{target_width})/2:0[outv]"
        )

    final_v_label = "[outv]"
    if subtitle_ass_path and subtitle_ass_path.exists():
        escaped_sub_path = str(subtitle_ass_path).replace("\\", "/").replace(":", "\\:")
        vf += f";{final_v_label}ass='{escaped_sub_path}'[subv]"
        final_v_label = "[subv]"

    args = ["-i", str(input_path)]

    if bg_music_path and bg_music_path.exists():
        args += ["-i", str(bg_music_path)]
        audio_filter = f"[0:a]volume=1.0[a0];[1:a]volume={bg_music_volume}[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        filter_complex_str = f"{vf};{audio_filter}"
        args += [
            "-filter_complex", filter_complex_str,
            "-map", final_v_label,
            "-map", "[outa]"
        ]
    else:
        args += [
            "-filter_complex", vf,
            "-map", final_v_label,
            "-map", "0:a?"
        ]

    args += [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    success, _ = run_ffmpeg(args)
    return success

def assemble_scenes(
    scene_video_paths: List[Path],
    output_path: Path,
    bg_music_path: Optional[Path] = None,
    narration_audio_paths: Optional[List[Optional[Path]]] = None,
    subtitle_ass_path: Optional[Path] = None,
    target_width: int = 1080,
    target_height: int = 1920
) -> bool:
    """
    Concatenate multiple scene videos into a cohesive timeline,
    mix narration and background music, burn subtitles, and export.
    """
    if not scene_video_paths:
        return False

    args = []
    for vp in scene_video_paths:
        args += ["-i", str(vp)]

    filter_parts = []
    n = len(scene_video_paths)
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[vconcat]")

    current_v = "[vconcat]"
    if subtitle_ass_path and subtitle_ass_path.exists():
        escaped_sub_path = str(subtitle_ass_path).replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"{current_v}ass='{escaped_sub_path}'[vfinal]")
        current_v = "[vfinal]"

    music_idx = None
    if bg_music_path and bg_music_path.exists():
        args += ["-i", str(bg_music_path)]
        music_idx = n
        filter_parts.append(f"[{music_idx}:a]volume=0.18[bgm]")

    filter_complex_str = ";".join(filter_parts)
    args += ["-filter_complex", filter_complex_str, "-map", current_v]

    if music_idx is not None:
        args += ["-map", "[bgm]", "-shortest"]

    args += [
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    success, _ = run_ffmpeg(args)
    return success
