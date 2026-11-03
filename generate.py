import os
import sys
import argparse
import shutil
import uuid
from pathlib import Path

# Ensure backend directory is in python search path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db, SessionLocal
from app.models.entities import Project, VideoAsset
from app.providers.registry import providers
from app.services.storage.storage_service import storage_service
from app.services.quality_control.qc_service import qc_service

def parse_resolution(res_str: str, aspect_ratio: str = "9:16") -> tuple[int, int]:
    """Parse resolution string into (width, height) tuples."""
    res = res_str.strip().lower()
    if "x" in res:
        parts = res.split("x")
        return int(parts[0]), int(parts[1])

    is_vertical = (aspect_ratio == "9:16")
    if "540" in res:
        return (540, 960) if is_vertical else (960, 540)
    elif "720" in res:
        return (720, 1280) if is_vertical else (1280, 720)
    elif "1080" in res:
        return (1080, 1920) if is_vertical else (1920, 1080)
    elif "480" in res:
        return (480, 854) if is_vertical else (854, 480)
    else:
        # Default to 720p
        return (720, 1280) if is_vertical else (1280, 720)

def main():
    parser = argparse.ArgumentParser(description="ClipForge AI - Command Line Video Generator")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for video generation")
    parser.add_argument("--resolution", type=str, default="720p", help="Resolution: 540p, 720p, 1080p, or WxH")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration in seconds (default: 5.0)")
    parser.add_argument("--aspect-ratio", type=str, default="9:16", help="Aspect ratio: 9:16 (default) or 16:9")
    parser.add_argument("--output", type=str, default=None, help="Optional custom output path for final MP4")
    parser.add_argument("--voiceover", action="store_true", default=False, help="Synthesize spoken voiceover narration")

    args = parser.parse_args()

    width, height = parse_resolution(args.resolution, args.aspect_ratio)
    print(f"[ClipForge] Generating video for prompt: '{args.prompt}'")
    print(f"[ClipForge] Resolution: {args.resolution} ({width}x{height}), Aspect Ratio: {args.aspect_ratio}, Duration: {args.duration}s")

    try:
        # 1. Initialize local DB and storage
        init_db()
        project_id = uuid.uuid4().hex
        job_id = f"cli_{uuid.uuid4().hex[:8]}"

        # 2. Get Video Provider
        video_provider = providers.get_video_provider()

        # 3. Generate Scene Video with exact width and height
        gen_result = video_provider.generate_video(
            prompt=args.prompt,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect_ratio,
            width=width,
            height=height
        )

        temp_video_path = Path(gen_result["video_path"])
        if not temp_video_path.exists():
            raise FileNotFoundError(f"Generated video not found at: {temp_video_path}")

        # 4. Optional Voiceover synthesis
        if args.voiceover:
            print("[ClipForge] Synthesizing neural voiceover narration...")
            audio_provider = providers.get_audio_provider()
            voice_path = storage_service.create_temp_path(prefix=f"voice_{job_id}", suffix=".wav", job_id=job_id)
            audio_provider.generate_voiceover(text=args.prompt, voice="energetic_male", output_path=voice_path)

            if voice_path.exists():
                from app.utils.ffmpeg import assemble_scenes
                mixed_output = storage_service.create_temp_path(prefix=f"mixed_{job_id}", suffix=".mp4", job_id=job_id)
                assembled = assemble_scenes(
                    scene_video_paths=[temp_video_path],
                    output_path=mixed_output,
                    voiceover_path=voice_path,
                    target_width=width,
                    target_height=height
                )
                if assembled and mixed_output.exists():
                    temp_video_path.unlink(missing_ok=True)
                    temp_video_path = mixed_output
                voice_path.unlink(missing_ok=True)

        # 5. Technical Quality Control Check
        qc_result = qc_service.evaluate_video(
            temp_video_path,
            expected_aspect_ratio=args.aspect_ratio,
            min_duration=0.5
        )

        # 6. Promote to permanent external storage
        final_filename = f"cli_gen_{args.resolution}_{project_id[:8]}.mp4"
        final_path = storage_service.save_final_video(temp_video_path, project_id=project_id, filename=final_filename)

        # Clean up temporary files
        storage_service.cleanup_job_temp_files(job_id)

        # 7. Record in database
        with SessionLocal() as session:
            proj = Project(
                id=project_id,
                name=f"CLI: {args.prompt[:35]}",
                project_type="prompt_to_video",
                platform="instagram_reels" if args.aspect_ratio == "9:16" else "youtube_shorts",
                settings={"resolution": args.resolution, "width": width, "height": height, "prompt": args.prompt},
                status="ready"
            )
            session.add(proj)

            asset = VideoAsset(
                project_id=project_id,
                asset_type="rendered_final",
                storage_path=str(final_path),
                original_filename=final_filename,
                duration=qc_result.get("metrics", {}).get("duration", args.duration),
                width=width,
                height=height,
                file_size_bytes=final_path.stat().st_size,
                metadata_json={"qc_report": qc_result}
            )
            session.add(asset)
            session.commit()

        # 8. Optional custom copy
        if args.output:
            dest = Path(args.output).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(final_path), str(dest))
            print(f"[ClipForge] Copied final video to: {dest}")

        print(f"[SUCCESS] Video rendered successfully at {args.resolution} ({width}x{height})")
        print(f"[SUCCESS] Saved in external storage: {final_path} ({final_path.stat().st_size} bytes)")
        sys.exit(0)

    except Exception as e:
        logger.exception("Error during CLI video generation")
        print(f"[ERROR] Video generation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
