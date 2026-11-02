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
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
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
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    face/smart crop, burned subtitles, and audio mixing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filter_parts = []

    # 1. Video scaling / cropping filter
    if mode == "blurred_background":
        filter_parts.append(
            f"[0:v]split=2[bg_src][fg_src];"
            f"[bg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},boxblur=20:20[bg];"
            f"[fg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
        )
    elif mode == "smart" and crop_x_offset is not None:
        filter_parts.append(
            f"[0:v]scale=-1:{target_height},"
            f"crop={target_width}:{target_height}:'min(max(0, (in_w * {crop_x_offset}) - {target_width}/2), in_w - {target_width})':0[outv]"
        )
    else:
        filter_parts.append(
            f"[0:v]scale=-1:{target_height},"
            f"crop={target_width}:{target_height}:(in_w-{target_width})/2:0[outv]"
        )

    current_v = "[outv]"
    if subtitle_ass_path and subtitle_ass_path.exists():
        escaped_sub_path = str(subtitle_ass_path).replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f"{current_v}ass='{escaped_sub_path}'[subv]")
        current_v = "[subv]"

    # Check if source video has audio
    has_audio = False
    try:
        from app.utils.ffprobe import inspect_media
        meta = inspect_media(input_path)
        has_audio = meta.get("has_audio", False)
    except Exception:
        has_audio = True

    args = ["-i", str(input_path)]

    if bg_music_path and bg_music_path.exists():
        args += ["-i", str(bg_music_path)]
        if has_audio:
            filter_parts.append(
                f"[0:a]volume=1.0[a0];[1:a]volume={bg_music_volume}[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,apad[outa]"
            )
        else:
            filter_parts.append(f"[1:a]volume={bg_music_volume},apad[outa]")
        audio_map = "[outa]"
    elif has_audio:
        filter_parts.append("[0:a]apad[outa]")
        audio_map = "[outa]"
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        filter_parts.append("[1:a]volume=1.0[silenta]")
        audio_map = "[silenta]"

    filter_complex_str = ";".join(filter_parts)
    args += [
        "-filter_complex", filter_complex_str,
        "-map", current_v,
        "-map", audio_map,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]

    success, _ = run_ffmpeg(args)
    return success

def assemble_scenes(
    scene_video_paths: List[Path],
    output_path: Path,
    voiceover_path: Optional[Path] = None,
    bg_music_path: Optional[Path] = None,
    subtitle_ass_path: Optional[Path] = None,
    target_width: int = 1080,
    target_height: int = 1920
) -> bool:
    """
    Concatenate multiple scene videos into a cohesive timeline,
    mix narration voiceover & background music, burn subtitles, and export.
    """
    if not scene_video_paths:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
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

    # Audio inputs & mixing
    extra_input_idx = n
    has_voiceover = voiceover_path and voiceover_path.exists()
    has_bg_music = bg_music_path and bg_music_path.exists()

    if has_voiceover and has_bg_music:
        args += ["-i", str(voiceover_path), "-i", str(bg_music_path)]
        voice_idx = extra_input_idx
        music_idx = extra_input_idx + 1
        filter_parts.append(
            f"[{voice_idx}:a]volume=1.0[voice];[{music_idx}:a]volume=0.15[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0,apad[outa]"
        )
        final_a = "[outa]"
    elif has_voiceover:
        args += ["-i", str(voiceover_path)]
        voice_idx = extra_input_idx
        filter_parts.append(f"[{voice_idx}:a]volume=1.0,apad[voice]")
        final_a = "[voice]"
    elif has_bg_music:
        args += ["-i", str(bg_music_path)]
        music_idx = extra_input_idx
        filter_parts.append(f"[{music_idx}:a]volume=0.25,apad[bgm]")
        final_a = "[bgm]"
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        silent_idx = extra_input_idx
        filter_parts.append(f"[{silent_idx}:a]volume=1.0[silenta]")
        final_a = "[silenta]"

    filter_complex_str = ";".join(filter_parts)
    args += [
        "-filter_complex", filter_complex_str,
        "-map", current_v,
        "-map", final_a,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]

    success, _ = run_ffmpeg(args)
    return success
