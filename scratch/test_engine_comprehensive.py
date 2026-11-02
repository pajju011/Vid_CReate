import sys
import os
from pathlib import Path

# Ensure backend is on sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.models.entities import Project, VideoAsset, Clip, Job, Scene, Transcript
from app.utils.sample_media import create_sample_video, create_sample_audio_track
from app.utils.ffprobe import inspect_media
from app.workers.pipelines import (
    run_analyze_video_pipeline,
    run_render_clip_pipeline,
    run_prompt_to_video_pipeline
)

def main():
    print("=" * 60)
    print("STARTING CLIPFORGE AI CORE ENGINE COMPREHENSIVE VERIFICATION")
    print("=" * 60)
    init_db()

    # -------------------------------------------------------------
    # TEST 1: WORKFLOW B (VIDEO-TO-SHORTS)
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Video-to-Shorts Analysis & Vertical Render...")
    with SessionLocal() as session:
        proj_b = Project(name="Test Shorts Project", project_type="video_to_shorts", platform="instagram_reels")
        session.add(proj_b)
        session.commit()
        proj_b_id = proj_b.id

        # Generate sample 16:9 source video
        source_video_path = settings.UPLOAD_DIR / f"test_source_{proj_b_id}.mp4"
        create_sample_video(source_video_path, duration=15.0, width=1920, height=1080)

        asset_b = VideoAsset(
            project_id=proj_b_id,
            asset_type="source_upload",
            storage_path=str(source_video_path),
            original_filename="test_source.mp4",
            duration=15.0,
            width=1920,
            height=1080,
            file_size_bytes=source_video_path.stat().st_size
        )
        session.add(asset_b)

        job_analyze = Job(project_id=proj_b_id, job_type="analyze_video")
        session.add(job_analyze)
        session.commit()
        job_analyze_id = job_analyze.id
        asset_b_id = asset_b.id

    print(f"  -> Running analyze video pipeline (Job {job_analyze_id})...")
    run_analyze_video_pipeline(job_analyze_id, asset_b_id, target_clip_duration=6.0)

    with SessionLocal() as session:
        job_res = session.query(Job).filter(Job.id == job_analyze_id).first()
        assert job_res.status == "completed", f"Analysis job failed: {job_res.error_message}"
        clips = session.query(Clip).filter(Clip.project_id == proj_b_id).all()
        assert len(clips) > 0, "No candidate clips generated!"
        print(f"  -> Successfully generated {len(clips)} candidate clips.")
        best_clip = max(clips, key=lambda c: c.score)
        best_clip_id = best_clip.id
        print(f"  -> Best clip: '{best_clip.title}' (Score: {best_clip.score:.2f}, {best_clip.start_time:.1f}s - {best_clip.end_time:.1f}s)")

        job_render = Job(project_id=proj_b_id, job_type="render_clip")
        session.add(job_render)
        session.commit()
        job_render_id = job_render.id

    print(f"  -> Rendering candidate clip into 9:16 vertical Short (Job {job_render_id})...")
    run_render_clip_pipeline(job_render_id, best_clip_id)

    with SessionLocal() as session:
        job_res = session.query(Job).filter(Job.id == job_render_id).first()
        assert job_res.status == "completed", f"Rendering clip failed: {job_res.error_message}"
        clip_updated = session.query(Clip).filter(Clip.id == best_clip_id).first()
        assert clip_updated.rendered_asset_id is not None, "Rendered asset not linked!"
        rendered_asset = session.query(VideoAsset).filter(VideoAsset.id == clip_updated.rendered_asset_id).first()
        assert rendered_asset is not None

    rendered_meta = inspect_media(Path(rendered_asset.storage_path))
    print(f"  -> Rendered Short inspection: {rendered_meta['width']}x{rendered_meta['height']}, {rendered_meta['duration']}s, video={rendered_meta['video_codec']}, audio={rendered_meta['audio_codec']}")
    assert rendered_meta["width"] == 1080 and rendered_meta["height"] == 1920, "Aspect ratio is not vertical 1080x1920!"
    assert rendered_meta["has_audio"] is True, "Audio stream is missing from rendered Short!"
    print("  [PASSED] Video-to-Shorts pipeline verified successfully!\n")

    # -------------------------------------------------------------
    # TEST 2: WORKFLOW A (PROMPT-TO-VIDEO: FULL VOICE + MUSIC)
    # -------------------------------------------------------------
    print("[TEST 2] Testing Prompt-to-Video (Full Narration + Background Music + Subtitles)...")
    with SessionLocal() as session:
        proj_a = Project(name="AI Fitness Reel", project_type="prompt_to_video", platform="instagram_reels")
        session.add(proj_a)
        session.commit()
        proj_a_id = proj_a.id

        job_prompt = Job(project_id=proj_a_id, job_type="generate_from_prompt")
        session.add(job_prompt)
        session.commit()
        job_prompt_id = job_prompt.id

    prompt_data = {
        "prompt": "Create an energetic 15-second fitness reel showing glowing smart shoes with AI sensors, night city run, and strong call to action.",
        "target_platform": "instagram_reels",
        "duration_seconds": 15.0,
        "num_scenes": 3,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "voiceover_enabled": True,
        "voice_selection": "energetic_male",
        "background_music": "upbeat",
        "caption_style": "bold_yellow"
    }

    print(f"  -> Running prompt-to-video pipeline (Job {job_prompt_id})...")
    run_prompt_to_video_pipeline(job_prompt_id, proj_a_id, prompt_data)

    with SessionLocal() as session:
        job_res = session.query(Job).filter(Job.id == job_prompt_id).first()
        assert job_res.status == "completed", f"Prompt-to-video job failed: {job_res.error_message}"
        final_asset = session.query(VideoAsset).filter(
            VideoAsset.project_id == proj_a_id,
            VideoAsset.asset_type == "rendered_final"
        ).first()
        assert final_asset is not None, "Final rendered asset missing!"

    meta_a = inspect_media(Path(final_asset.storage_path))
    print(f"  -> Master Reel inspection: {meta_a['width']}x{meta_a['height']}, {meta_a['duration']}s, video={meta_a['video_codec']}, audio={meta_a['audio_codec']}")
    assert meta_a["width"] == 1080 and meta_a["height"] == 1920, "Master video is not 1080x1920!"
    assert abs(meta_a["duration"] - 15.0) < 0.5, f"Expected 15s duration, got {meta_a['duration']}s!"
    assert meta_a["has_audio"] is True, "Master video must have audio!"
    print("  [PASSED] Prompt-to-Video full mix pipeline verified successfully!\n")

    # -------------------------------------------------------------
    # TEST 3: PROMPT-TO-VIDEO EDGE CASE (VOICEOVER ONLY, NO BGM)
    # -------------------------------------------------------------
    print("[TEST 3] Testing Prompt-to-Video Edge Case: Voiceover Only (No BGM)...")
    with SessionLocal() as session:
        proj_c = Project(name="Voice Only Reel", project_type="prompt_to_video", platform="youtube_shorts")
        session.add(proj_c)
        session.commit()
        proj_c_id = proj_c.id

        job_c = Job(project_id=proj_c_id, job_type="generate_from_prompt")
        session.add(job_c)
        session.commit()
        job_c_id = job_c.id

    prompt_data_voice_only = {
        "prompt": "Explaining the mystery of deep space nebulas in 10 seconds.",
        "target_platform": "youtube_shorts",
        "duration_seconds": 10.0,
        "num_scenes": 2,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "voiceover_enabled": True,
        "voice_selection": "calm_female",
        "background_music": "none",
        "caption_style": "clean_minimal"
    }

    run_prompt_to_video_pipeline(job_c_id, proj_c_id, prompt_data_voice_only)

    with SessionLocal() as session:
        job_res = session.query(Job).filter(Job.id == job_c_id).first()
        assert job_res.status == "completed", f"Job failed: {job_res.error_message}"
        final_asset_c = session.query(VideoAsset).filter(
            VideoAsset.project_id == proj_c_id,
            VideoAsset.asset_type == "rendered_final"
        ).first()

    meta_c = inspect_media(Path(final_asset_c.storage_path))
    print(f"  -> Voice-only Reel inspection: {meta_c['width']}x{meta_c['height']}, {meta_c['duration']}s, video={meta_c['video_codec']}, audio={meta_c['audio_codec']}")
    assert abs(meta_c["duration"] - 10.0) < 0.5, f"Expected 10s duration, got {meta_c['duration']}s!"
    assert meta_c["has_audio"] is True
    print("  [PASSED] Voiceover-only pipeline verified successfully!\n")

    # -------------------------------------------------------------
    # TEST 4: PROMPT-TO-VIDEO EDGE CASE (NO AUDIO AT ALL -> SILENCE FALLBACK)
    # -------------------------------------------------------------
    print("[TEST 4] Testing Prompt-to-Video Edge Case: Silent (No Voiceover, No BGM)...")
    with SessionLocal() as session:
        proj_d = Project(name="Silent Visual Reel", project_type="prompt_to_video", platform="instagram_reels")
        session.add(proj_d)
        session.commit()
        proj_d_id = proj_d.id

        job_d = Job(project_id=proj_d_id, job_type="generate_from_prompt")
        session.add(job_d)
        session.commit()
        job_d_id = job_d.id

    prompt_data_silent = {
        "prompt": "Minimalist architectural shapes moving in monochrome.",
        "target_platform": "instagram_reels",
        "duration_seconds": 6.0,
        "num_scenes": 2,
        "aspect_ratio": "9:16",
        "visual_style": "3d_render",
        "voiceover_enabled": False,
        "background_music": "none",
        "caption_style": "creator_box"
    }

    run_prompt_to_video_pipeline(job_d_id, proj_d_id, prompt_data_silent)

    with SessionLocal() as session:
        job_res = session.query(Job).filter(Job.id == job_d_id).first()
        assert job_res.status == "completed", f"Job failed: {job_res.error_message}"
        final_asset_d = session.query(VideoAsset).filter(
            VideoAsset.project_id == proj_d_id,
            VideoAsset.asset_type == "rendered_final"
        ).first()

    meta_d = inspect_media(Path(final_asset_d.storage_path))
    print(f"  -> Silent Reel inspection: {meta_d['width']}x{meta_d['height']}, {meta_d['duration']}s, video={meta_d['video_codec']}, audio={meta_d['audio_codec']}")
    assert abs(meta_d["duration"] - 6.0) < 0.5, f"Expected 6s duration, got {meta_d['duration']}s!"
    assert meta_d["has_audio"] is True, "Silent AAC audio track must be present for platform compliance!"
    print("  [PASSED] Silent video pipeline verified successfully!\n")

    print("=" * 60)
    print("ALL CORE VIDEO GENERATION ENGINE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    main()
