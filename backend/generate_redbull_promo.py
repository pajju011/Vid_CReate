"""
Generate 10-Second Red Bull Promo Video
Uses ClipForge AI pipeline with OmniForge (3D Depth Parallax Engine), Edge Neural TTS, and Whisper captions.
"""
import sys
import os
import shutil
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, init_db
from app.models.entities import Project, Job, VideoAsset
from app.workers.pipelines import run_prompt_to_video_pipeline

def main():
    print("=" * 60)
    print("STARTING RED BULL 10-SECOND PROMO VIDEO GENERATION")
    print("=" * 60)
    
    init_db()
    
    project_id = uuid.uuid4().hex[:12]
    job_id = f"job_rb_{uuid.uuid4().hex[:8]}"
    
    with SessionLocal() as db:
        proj = Project(
            id=project_id,
            name="Red Bull - Gives You Wings (10s Promo)",
            platform="instagram_reels",
            project_type="prompt_to_video",
            status="processing"
        )
        db.add(proj)
        
        job = Job(
            id=job_id,
            project_id=project_id,
            job_type="prompt_to_video",
            status="pending",
            progress=0,
            current_step="Initializing"
        )
        db.add(job)
        db.commit()
        print(f"[1/4] Created Project '{project_id}' and Job '{job_id}'")

    prompt_data = {
        "prompt": "High-energy cinematic Red Bull energy drink promo. An ice-cold Red Bull can cracking open with freezing condensation and frost droplets flying, cutting to an extreme athlete defying gravity mid-air, bold dynamic camera push-in, electric blue and red neon lighting, gives you wings slogan. 9:16 vertical format for Instagram Reels.",
        "duration_seconds": 10.0,
        "num_scenes": 2,
        "target_platform": "instagram_reels",
        "aspect_ratio": "9:16",
        "visual_style": "commercial",
        "video_engine": "omni",
        "voiceover_enabled": True,
        "voice_selection": "energetic_male",
        "caption_style": "bold_yellow",
        "background_music": "energetic"
    }

    print("[2/4] Running prompt-to-video pipeline (OmniForge 3D Engine)...")
    run_prompt_to_video_pipeline(job_id=job_id, project_id=project_id, prompt_data=prompt_data)
    
    with SessionLocal() as db:
        final_job = db.query(Job).filter(Job.id == job_id).first()
        print(f"[3/4] Pipeline finished with status: {final_job.status} (Progress: {final_job.progress}%)")
        if final_job.error_message:
            print(f"Error details: {final_job.error_message}")
            
        final_asset = db.query(VideoAsset).filter(
            VideoAsset.project_id == project_id,
            VideoAsset.asset_type == "rendered_final"
        ).first()

    if final_asset and Path(final_asset.storage_path).exists():
        src_path = Path(final_asset.storage_path)
        dest_path = Path("..") / "redbull_promo_10s.mp4"
        shutil.copy(src_path, dest_path)
        print(f"[4/4] SUCCESS! Final video generated and copied to project root:")
        print(f"      -> {dest_path.resolve()} ({dest_path.stat().st_size:,} bytes)")
        return str(dest_path.resolve())
    else:
        print("[!] Final video asset was not found or generation failed.")
        return None

if __name__ == "__main__":
    main()
