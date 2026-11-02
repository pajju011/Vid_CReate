import os
from pathlib import Path
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.entities import Project, VideoAsset, Scene, Clip, Job, Transcript
from app.utils.ffprobe import inspect_media
from app.utils.ffmpeg import extract_thumbnail, extract_audio, trim_video, convert_to_vertical, assemble_scenes
from app.services.scene_detection.detector import scene_detector
from app.services.cropping.crop_detector import crop_detector
from app.services.subtitles.subtitle_generator import subtitle_generator
from app.services.clip_selection.clip_ranker import clip_ranker
from app.services.quality_control.qc_service import qc_service
from app.services.consistency.consistency_engine import consistency_engine
from app.core.cache import asset_cache
from app.providers.registry import providers

def update_job_sync(
    job_id: str,
    status: str,
    progress: int,
    current_step: str,
    result_data: dict = None,
    error_message: str = None
):
    with SessionLocal() as session:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            job.current_step = current_step
            job.updated_at = datetime.now(timezone.utc)
            if result_data is not None:
                job.result_data = {**(job.result_data or {}), **result_data}
            if error_message:
                job.error_message = error_message
            session.commit()

def run_analyze_video_pipeline(job_id: str, asset_id: str, target_clip_duration: float = 30.0):
    """Full Video-to-Shorts analysis pipeline."""
    try:
        update_job_sync(job_id, "running", 10, "Analyzing media format and streams...")

        with SessionLocal() as session:
            asset = session.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
            if not asset:
                raise ValueError(f"Asset {asset_id} not found.")
            video_path = Path(asset.storage_path)
            project_id = asset.project_id

        # 1. FFprobe metadata inspection
        meta = inspect_media(video_path)
        with SessionLocal() as session:
            asset = session.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
            asset.duration = meta["duration"]
            asset.width = meta["width"]
            asset.height = meta["height"]
            asset.metadata_json = meta
            session.commit()

        # 2. Extract thumbnail
        thumb_path = settings.TEMP_DIR / f"thumb_{asset_id}.jpg"
        extract_thumbnail(video_path, thumb_path, timestamp=min(1.0, meta["duration"] / 2))

        # 3. Transcription
        update_job_sync(job_id, "running", 30, "Extracting audio and transcribing speech...")
        audio_wav = settings.TEMP_DIR / f"audio_{asset_id}.wav"
        transcript_data = {"text": "", "language": "en", "segments": []}
        if meta.get("has_audio"):
            if extract_audio(video_path, audio_wav):
                transcriber = providers.get_transcription_provider()
                transcript_data = transcriber.transcribe_audio(audio_wav)

        with SessionLocal() as session:
            tr = Transcript(
                asset_id=asset_id,
                text=transcript_data.get("text", ""),
                segments_json=transcript_data.get("segments", []),
                language=transcript_data.get("language", "en")
            )
            session.add(tr)
            session.commit()

        # 4. Scene Detection
        update_job_sync(job_id, "running", 55, "Detecting scene cuts and shot transitions...")
        scene_cuts = scene_detector.detect_scenes(video_path)

        # 5. Candidate Clip Generation & Scoring
        update_job_sync(job_id, "running", 75, "Generating and scoring candidate clips...")
        ranked_candidates = clip_ranker.generate_candidate_clips(
            transcript_segments=transcript_data.get("segments", []),
            scene_cuts=scene_cuts,
            video_duration=meta["duration"],
            target_duration=target_clip_duration,
            num_clips=3
        )

        clip_ids = []
        with SessionLocal() as session:
            for cand in ranked_candidates:
                c = Clip(
                    project_id=project_id,
                    source_asset_id=asset_id,
                    start_time=cand["start_time"],
                    end_time=cand["end_time"],
                    score=cand["score"],
                    title=cand["title"],
                    hook=cand["hook"],
                    reason=cand["reason"],
                    status="candidate",
                    crop_mode="smart",
                    caption_style="bold_yellow"
                )
                session.add(c)
                session.flush()
                clip_ids.append(c.id)

            proj = session.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.status = "ready"
            session.commit()

        update_job_sync(
            job_id,
            "completed",
            100,
            f"Analysis complete! Found {len(clip_ids)} candidate short clips.",
            result_data={"clip_ids": clip_ids, "scene_cuts_count": len(scene_cuts)}
        )

    except Exception as e:
        logger.exception(f"Error in video analysis pipeline for asset {asset_id}")
        update_job_sync(job_id, "failed", 0, "Analysis failed", error_message=str(e))

def run_render_clip_pipeline(job_id: str, clip_id: str):
    """Render a selected Short clip with smart vertical crop and burned subtitles."""
    try:
        update_job_sync(job_id, "running", 10, "Fetching clip details...")
        with SessionLocal() as session:
            clip = session.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                raise ValueError(f"Clip {clip_id} not found.")

            source_asset = session.query(VideoAsset).filter(VideoAsset.id == clip.source_asset_id).first()
            if not source_asset:
                raise ValueError(f"Source video asset not found for clip {clip_id}.")

            transcript = session.query(Transcript).filter(Transcript.asset_id == source_asset.id).first()

            project_id = clip.project_id
            start_time = clip.start_time
            end_time = clip.end_time
            crop_mode = clip.crop_mode
            caption_style = clip.caption_style
            source_path = Path(source_asset.storage_path)
            clip.status = "rendering"
            session.commit()

        # 1. Trim source segment
        update_job_sync(job_id, "running", 25, "Trimming high-engagement segment...")
        trimmed_segment = settings.TEMP_DIR / f"trim_{clip_id}.mp4"
        trim_ok = trim_video(source_path, trimmed_segment, start_time, end_time)
        if not trim_ok:
            raise RuntimeError("Failed to trim video segment.")

        # 2. Smart Crop Offset detection
        crop_x = 0.5
        if crop_mode == "smart":
            update_job_sync(job_id, "running", 45, "Tracking primary subject for 9:16 vertical crop...")
            crop_x = crop_detector.detect_subject_horizontal_offset(
                source_path,
                start_time=start_time,
                end_time=end_time
            )

        # 3. Subtitles Generation
        update_job_sync(job_id, "running", 65, "Styling and synchronizing subtitles...")
        sub_ass_path = None
        if transcript and transcript.segments_json:
            sub_ass_path = settings.TEMP_DIR / f"sub_{clip_id}.ass"
            subtitle_generator.generate_ass(
                segments=transcript.segments_json,
                output_path=sub_ass_path,
                style_preset=caption_style,
                time_offset=start_time,
                max_duration=(end_time - start_time)
            )

        # 4. Render vertical video with subtitle burning
        update_job_sync(job_id, "running", 80, "Rendering final vertical 1080x1920 MP4...")
        rendered_filename = f"short_{clip_id}.mp4"
        rendered_path = settings.RENDERS_DIR / rendered_filename
        render_ok = convert_to_vertical(
            input_path=trimmed_segment,
            output_path=rendered_path,
            mode=crop_mode,
            crop_x_offset=crop_x,
            target_width=1080,
            target_height=1920,
            subtitle_ass_path=sub_ass_path
        )
        if not render_ok:
            raise RuntimeError("FFmpeg failed to render final vertical short video.")

        # 5. Quality Control check
        update_job_sync(job_id, "running", 92, "Running automated technical QC checks...")
        qc_result = qc_service.evaluate_video(rendered_path, expected_aspect_ratio="9:16")

        # 6. Save rendered VideoAsset and link to Clip
        with SessionLocal() as session:
            clip = session.query(Clip).filter(Clip.id == clip_id).first()
            v_asset = VideoAsset(
                project_id=project_id,
                asset_type="rendered_short",
                storage_path=str(rendered_path),
                original_filename=rendered_filename,
                duration=qc_result.get("metrics", {}).get("duration"),
                width=1080,
                height=1920,
                file_size_bytes=rendered_path.stat().st_size,
                metadata_json={"qc_report": qc_result}
            )
            session.add(v_asset)
            session.flush()

            clip.rendered_asset_id = v_asset.id
            clip.status = "completed"
            session.commit()

        update_job_sync(
            job_id,
            "completed",
            100,
            "Vertical short successfully rendered!",
            result_data={"rendered_asset_id": v_asset.id, "qc_status": qc_result["status"]}
        )

    except Exception as e:
        logger.exception(f"Error rendering clip {clip_id}")
        update_job_sync(job_id, "failed", 0, "Clip rendering failed", error_message=str(e))

def run_prompt_to_video_pipeline(job_id: str, project_id: str, prompt_data: dict):
    """Full Prompt-to-Video pipeline."""
    try:
        # 1. AI Planning
        update_job_sync(job_id, "running", 15, "AI Creative Director planning script and storyboard...")
        llm = providers.get_llm_provider()
        script = llm.generate_script(
            prompt=prompt_data["prompt"],
            duration_seconds=prompt_data.get("duration_seconds", 30.0),
            platform=prompt_data.get("target_platform", "instagram_reels")
        )
        storyboard = llm.generate_storyboard(
            script_data=script,
            num_scenes=prompt_data.get("num_scenes", 4),
            style=prompt_data.get("visual_style", "cinematic")
        )

        # Enforce Character Consistency, Camera Movement Continuity & Lighting
        storyboard = consistency_engine.enrich_storyboard_for_consistency(
            storyboard=storyboard,
            visual_style=prompt_data.get("visual_style", "cinematic"),
            user_prompt=prompt_data.get("prompt", "")
        )

        scene_ids = []
        with SessionLocal() as session:
            for s in storyboard:
                sc = Scene(
                    project_id=project_id,
                    scene_number=s["scene_number"],
                    duration=s.get("duration_seconds", 5.0),
                    prompt=s["visual_prompt"],
                    visual_description=s.get("visual_prompt"),
                    camera_movement=s.get("camera_movement", "slow_push_in"),
                    narration=s.get("narration"),
                    caption=s.get("caption"),
                    consistency_anchor=s.get("consistency_anchor"),
                    status="pending"
                )
                session.add(sc)
                session.flush()
                scene_ids.append(sc.id)
            session.commit()

        # 2. Asset Generation for Scenes with Automatic Quality Control & Retry
        update_job_sync(
            job_id, "running", 40,
            f"Generating visual assets for {len(scene_ids)} scenes...",
            result_data={"stage": "generating_scenes", "scenes_total": len(scene_ids), "scenes_completed": 0}
        )
        video_provider = providers.get_video_provider()
        scene_video_paths = []

        target_w = 1080 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1920
        target_h = 1920 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1080

        for idx, sid in enumerate(scene_ids, 1):
            update_job_sync(
                job_id, "running",
                40 + int(idx * 25 / len(scene_ids)),
                f"Generating scene {idx} of {len(scene_ids)}...",
                result_data={"stage": "generating_scenes", "scenes_total": len(scene_ids), "scenes_completed": idx - 1, "current_scene": idx}
            )
            with SessionLocal() as session:
                sc = session.query(Scene).filter(Scene.id == sid).first()
                duration = sc.duration
                prompt_text = sc.prompt

            # Scene generation with automatic QC verification and retry
            v_path = None
            max_scene_retries = 2
            for attempt in range(max_scene_retries + 1):
                try:
                    if prompt_data.get("image_keyframe_path") and Path(prompt_data["image_keyframe_path"]).exists():
                        gen_result = video_provider.generate_video_from_image(
                            image_path=Path(prompt_data["image_keyframe_path"]),
                            prompt=prompt_text,
                            duration_seconds=duration,
                            aspect_ratio=prompt_data.get("aspect_ratio", "9:16")
                        )
                    else:
                        gen_result = video_provider.generate_video(
                            prompt=prompt_text,
                            duration_seconds=duration,
                            aspect_ratio=prompt_data.get("aspect_ratio", "9:16")
                        )
                    candidate_v_path = Path(gen_result.get("video_path"))

                    # Strict per-scene QC check
                    scene_qc = qc_service.evaluate_video(
                        candidate_v_path,
                        expected_aspect_ratio=prompt_data.get("aspect_ratio", "9:16"),
                        min_duration=1.0
                    )
                    if scene_qc["status"] == "passed":
                        v_path = candidate_v_path
                        break
                    else:
                        logger.warning(f"Scene {idx} failed QC on attempt {attempt + 1}: {scene_qc.get('issues')}")
                except Exception as e:
                    logger.warning(f"Scene {idx} generation error on attempt {attempt + 1}: {e}")

            if not v_path or not v_path.exists():
                raise RuntimeError(f"Scene {idx} failed to generate and pass quality control after retries.")

            scene_video_paths.append(v_path)

            with SessionLocal() as session:
                sc = session.query(Scene).filter(Scene.id == sid).first()
                sc.status = "completed"
                session.commit()

        # 3. Voiceover narration synthesis
        voiceover_path = None
        if prompt_data.get("voiceover_enabled", True):
            update_job_sync(job_id, "running", 70, "Synthesizing voiceover narration...")
            full_narration = " ".join(s.get("narration", "") for s in storyboard if s.get("narration"))
            if full_narration.strip():
                audio_provider = providers.get_audio_provider()
                voiceover_path = settings.TEMP_DIR / f"voice_{project_id}.wav"
                audio_provider.generate_voiceover(
                    text=full_narration,
                    voice=prompt_data.get("voice_selection", "energetic_male"),
                    output_path=voiceover_path
                )

        # 4. Background Music synthesis
        bg_music_path = None
        if prompt_data.get("background_music") not in ("none", None):
            update_job_sync(job_id, "running", 78, "Composing background music soundtrack...")
            audio_provider = providers.get_audio_provider()
            bg_music_path = settings.TEMP_DIR / f"bgm_{project_id}.wav"
            audio_provider.generate_music(
                mood=prompt_data.get("background_music", "upbeat"),
                duration_seconds=prompt_data.get("duration_seconds", 30.0),
                output_path=bg_music_path
            )

        # 5. Generate Subtitles from scene captions
        update_job_sync(job_id, "running", 82, "Compiling timed subtitle track...")
        sub_segments = []
        cur_t = 0.0
        for s in storyboard:
            dur = s.get("duration_seconds", 5.0)
            caption_text = s.get("caption") or s.get("narration") or ""
            if caption_text:
                sub_segments.append({
                    "start": cur_t,
                    "end": cur_t + dur,
                    "text": caption_text
                })
            cur_t += dur

        sub_ass_path = settings.TEMP_DIR / f"sub_proj_{project_id}.ass"
        subtitle_generator.generate_ass(
            segments=sub_segments,
            output_path=sub_ass_path,
            style_preset=prompt_data.get("caption_style", "bold_yellow"),
            max_duration=cur_t,
            video_width=target_w,
            video_height=target_h
        )

        # 6. Assembly & Audio Ducking
        update_job_sync(job_id, "running", 88, "Assembling scenes into final master video...")
        output_filename = f"final_{project_id}.mp4"
        output_path = settings.RENDERS_DIR / output_filename

        ok = assemble_scenes(
            scene_video_paths=scene_video_paths,
            output_path=output_path,
            voiceover_path=voiceover_path,
            bg_music_path=bg_music_path,
            subtitle_ass_path=sub_ass_path,
            target_width=target_w,
            target_height=target_h
        )
        if not ok:
            raise RuntimeError("FFmpeg assembly failed for final project.")

        # 7. Quality Control Check
        update_job_sync(job_id, "running", 95, "Running automated technical QC checks...")
        qc_result = qc_service.evaluate_video(
            output_path,
            expected_aspect_ratio=prompt_data.get("aspect_ratio", "9:16"),
            require_audio=True
        )

        with SessionLocal() as session:
            final_asset = VideoAsset(
                project_id=project_id,
                asset_type="rendered_final",
                storage_path=str(output_path),
                original_filename=output_filename,
                duration=qc_result.get("metrics", {}).get("duration"),
                width=target_w,
                height=target_h,
                file_size_bytes=output_path.stat().st_size,
                metadata_json={"qc_report": qc_result}
            )
            session.add(final_asset)

            proj = session.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.status = "ready"
            session.commit()

        update_job_sync(
            job_id,
            "completed",
            100,
            "Video generation completed successfully!",
            result_data={
                "asset_id": final_asset.id,
                "qc_status": qc_result["status"],
                "duration": qc_result.get("metrics", {}).get("duration"),
                "has_audio": qc_result.get("metrics", {}).get("has_audio")
            }
        )

    except Exception as e:
        logger.exception(f"Error in prompt to video pipeline for project {project_id}")
        update_job_sync(job_id, "failed", 0, "Video generation failed", error_message=str(e))

def run_regenerate_scene_pipeline(job_id: str, scene_id: str, new_prompt: Optional[str] = None):
    """Regenerate a single scene clip without affecting approved scenes."""
    try:
        update_job_sync(job_id, "running", 20, f"Regenerating scene asset {scene_id}...")
        with SessionLocal() as session:
            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise ValueError(f"Scene {scene_id} not found.")

            if new_prompt:
                scene.prompt = new_prompt
            prompt_text = scene.prompt
            duration = scene.duration
            project_id = scene.project_id
            scene.status = "generating"
            session.commit()

        video_provider = providers.get_video_provider()
        gen_result = video_provider.generate_video(
            prompt=prompt_text,
            duration_seconds=duration,
            aspect_ratio="9:16"
        )
        v_path = Path(gen_result.get("video_path"))

        qc_res = qc_service.evaluate_video(v_path, expected_aspect_ratio="9:16", min_duration=1.0)
        if qc_res["status"] != "passed":
            raise RuntimeError(f"Regenerated scene failed QC checks: {qc_res.get('issues')}")

        with SessionLocal() as session:
            scene = session.query(Scene).filter(Scene.id == scene_id).first()
            scene.status = "completed"
            session.commit()

        update_job_sync(
            job_id, "completed", 100,
            "Scene successfully regenerated!",
            result_data={"scene_id": scene_id, "video_path": str(v_path)}
        )
    except Exception as e:
        logger.exception(f"Error regenerating scene {scene_id}")
        update_job_sync(job_id, "failed", 0, "Scene regeneration failed", error_message=str(e))

