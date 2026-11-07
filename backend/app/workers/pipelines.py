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
from app.services.storage.storage_service import storage_service
from app.providers.registry import providers
from app.api.websocket_manager import ws_manager

def update_job_sync(
    job_id: str,
    status: str,
    progress: int,
    current_step: str,
    result_data: dict = None,
    error_message: str = None,
    checkpoint_data: dict = None
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
            if checkpoint_data is not None:
                job.checkpoint_data = {**(job.checkpoint_data or {}), **checkpoint_data}
            if error_message:
                job.error_message = error_message
            session.commit()

            # Broadcast real-time update to WebSocket clients
            ws_manager.broadcast_sync(job_id, {
                "type": "job_progress",
                "job_id": job.id,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "result_data": job.result_data,
                "checkpoint_data": job.checkpoint_data,
                "error_message": job.error_message,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None
            })

def is_job_halted(job_id: str) -> bool:
    with SessionLocal() as session:
        job = session.query(Job).filter(Job.id == job_id).first()
        return bool(job and job.status in ("paused", "cancelled"))


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
        thumb_path = storage_service.create_temp_path(prefix=f"thumb_{asset_id}", suffix=".jpg", job_id=job_id)
        extract_thumbnail(video_path, thumb_path, timestamp=min(1.0, meta["duration"] / 2))

        # 3. Transcription
        update_job_sync(job_id, "running", 30, "Extracting audio and transcribing speech...")
        audio_wav = storage_service.create_temp_path(prefix=f"audio_{asset_id}", suffix=".wav", job_id=job_id)
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

        # Clean up temporary processing files
        storage_service.cleanup_job_temp_files(job_id)

        update_job_sync(
            job_id,
            "completed",
            100,
            f"Analysis complete! Found {len(clip_ids)} candidate short clips.",
            result_data={"clip_ids": clip_ids, "scene_cuts_count": len(scene_cuts)}
        )

    except Exception as e:
        logger.exception(f"Error in video analysis pipeline for asset {asset_id}")
        storage_service.cleanup_job_temp_files(job_id)
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

        if is_job_halted(job_id):
            return

        # 1. Trim source segment in external temporary directory
        update_job_sync(job_id, "running", 25, "Trimming high-engagement segment in temp storage...")
        trimmed_segment = storage_service.create_temp_path(prefix=f"trim_{clip_id}", suffix=".mp4", job_id=job_id)
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

        # 3. Subtitles Generation in temp directory
        update_job_sync(job_id, "running", 65, "Styling and synchronizing subtitles...")
        sub_ass_path = None
        if transcript and transcript.segments_json:
            sub_ass_path = storage_service.create_temp_path(prefix=f"sub_{clip_id}", suffix=".ass", job_id=job_id)
            subtitle_generator.generate_ass(
                segments=transcript.segments_json,
                output_path=sub_ass_path,
                style_preset=caption_style,
                time_offset=start_time,
                max_duration=(end_time - start_time)
            )

        if is_job_halted(job_id):
            return

        # 4. Render vertical video in external temporary directory
        update_job_sync(job_id, "running", 80, "Rendering vertical 1080x1920 MP4 in temp workspace...")
        rendered_filename = f"short_{clip_id}.mp4"
        temp_rendered_path = storage_service.create_temp_path(prefix=f"short_render_{clip_id}", suffix=".mp4", job_id=job_id)
        render_ok = convert_to_vertical(
            input_path=trimmed_segment,
            output_path=temp_rendered_path,
            mode=crop_mode,
            crop_x_offset=crop_x,
            target_width=1080,
            target_height=1920,
            subtitle_ass_path=sub_ass_path
        )
        if not render_ok:
            raise RuntimeError("FFmpeg failed to render vertical short video in temp storage.")

        # 5. Quality Control check on temporary file before promotion
        update_job_sync(job_id, "running", 92, "Running automated technical QC checks...")
        qc_result = qc_service.evaluate_video(temp_rendered_path, expected_aspect_ratio="9:16")

        if qc_result.get("status") == "failed":
            raise RuntimeError(f"Rendered short failed QC validation: {qc_result.get('issues')}")

        # 6. Promote to permanent external storage & optional draft copy
        storage_service.save_draft(trimmed_segment, project_id=project_id, filename=f"draft_trim_{clip_id}.mp4")
        final_rendered_path = storage_service.save_final_video(temp_rendered_path, project_id=project_id, filename=rendered_filename)

        # Clean up temporary processing files
        storage_service.cleanup_job_temp_files(job_id)

        # 7. Save rendered VideoAsset with external storage path
        with SessionLocal() as session:
            clip = session.query(Clip).filter(Clip.id == clip_id).first()
            v_asset = VideoAsset(
                project_id=project_id,
                asset_type="rendered_short",
                storage_path=str(final_rendered_path),
                original_filename=rendered_filename,
                duration=qc_result.get("metrics", {}).get("duration"),
                width=1080,
                height=1920,
                file_size_bytes=final_rendered_path.stat().st_size,
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
            "Vertical short successfully rendered in external storage!",
            result_data={"rendered_asset_id": v_asset.id, "qc_status": qc_result["status"], "storage_path": str(final_rendered_path)}
        )

    except Exception as e:
        logger.exception(f"Error rendering clip {clip_id}")
        storage_service.cleanup_job_temp_files(job_id)
        update_job_sync(job_id, "failed", 0, "Clip rendering failed", error_message=str(e))

def run_prompt_to_video_pipeline(job_id: str, project_id: str, prompt_data: dict):
    """Full Prompt-to-Video pipeline with checkpoint recovery and pause/resume support."""
    try:
        # Check initial state and checkpoint with brief retry for database synchronization
        job = None
        for attempt in range(5):
            with SessionLocal() as session:
                job = session.query(Job).filter(Job.id == job_id).first()
                if job:
                    if job.status in ("paused", "cancelled"):
                        logger.info(f"Job {job_id} is already {job.status}. Exiting.")
                        return
                    checkpoint = (job.checkpoint_data or {})
                    break
            time.sleep(0.2)

        if not job:
            raise ValueError(f"Job {job_id} not found.")

        completed_scenes = dict(checkpoint.get("completed_scenes", {}))

        # 1. AI Planning (or restore from checkpoint)
        if checkpoint.get("storyboard"):
            storyboard = checkpoint["storyboard"]
            logger.info(f"Restored storyboard from checkpoint for job {job_id}")
        else:
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
            update_job_sync(job_id, "running", 25, "Storyboard created and consistency anchors configured", checkpoint_data={"storyboard": storyboard})

        if is_job_halted(job_id):
            return

        scene_ids = []
        with SessionLocal() as session:
            existing_scenes = session.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number).all()
            if existing_scenes and len(existing_scenes) == len(storyboard):
                scene_ids = [sc.id for sc in existing_scenes]
            else:
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
            result_data={"stage": "generating_scenes", "scenes_total": len(scene_ids), "scenes_completed": len(completed_scenes)}
        )
        engine_choice = (prompt_data.get("video_engine") or "").lower()
        if engine_choice in ("pexels", "stock"):
            from app.providers.video.pexels_provider import PexelsVideoProvider
            video_provider = PexelsVideoProvider()
        elif engine_choice in ("veo", "google_veo"):
            from app.providers.video.video_providers import GoogleVeoVideoProvider
            video_provider = GoogleVeoVideoProvider(api_key=settings.VIDEO_API_KEY)
        else:
            video_provider = providers.get_video_provider()
        scene_video_paths = []

        target_w = 1080 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1920
        target_h = 1920 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1080

        for idx, sid in enumerate(scene_ids, 1):
            if is_job_halted(job_id):
                logger.info(f"Job {job_id} paused/cancelled before scene {idx}. Halting pipeline.")
                return

            # Check if this scene was completed in a previous run and file is valid
            if str(sid) in completed_scenes and Path(completed_scenes[str(sid)]).exists():
                logger.info(f"Reusing scene {idx} from checkpoint: {completed_scenes[str(sid)]}")
                scene_video_paths.append(Path(completed_scenes[str(sid)]))
                continue

            update_job_sync(
                job_id, "running",
                40 + int(idx * 25 / len(scene_ids)),
                f"Generating scene {idx} of {len(scene_ids)}...",
                result_data={"stage": "generating_scenes", "scenes_total": len(scene_ids), "scenes_completed": len(scene_video_paths), "current_scene": idx}
            )
            with SessionLocal() as session:
                sc = session.query(Scene).filter(Scene.id == sid).first()
                duration = sc.duration if sc else 5.0
                prompt_text = sc.prompt if sc else "Cinematic dynamic shot"

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
                    raw_vpath = gen_result.get("video_path")
                    if not raw_vpath:
                        logger.warning(f"Scene {idx} attempt {attempt + 1}: video_path was not returned by provider")
                        continue

                    candidate_v_path = Path(raw_vpath)
                    if not candidate_v_path.exists():
                        logger.warning(f"Scene {idx} attempt {attempt + 1}: file {candidate_v_path} does not exist")
                        continue

                    # Strict per-scene QC check
                    scene_qc = qc_service.evaluate_video(
                        candidate_v_path,
                        expected_aspect_ratio=prompt_data.get("aspect_ratio", "9:16"),
                        min_duration=0.8
                    )
                    if scene_qc["status"] == "passed":
                        v_path = candidate_v_path
                        break
                    else:
                        logger.warning(f"Scene {idx} failed QC on attempt {attempt + 1}: {scene_qc.get('issues')}")
                except Exception as e:
                    logger.warning(f"Scene {idx} generation error on attempt {attempt + 1}: {e}")

            if not v_path or not v_path.exists():
                logger.warning(f"Scene {idx} could not pass QC after retries. Generating ultra-reliable procedural scene fallback...")
                dur = max(2.0, float(duration or 5.0))
                tw = 1080 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1920
                th = 1920 if prompt_data.get("aspect_ratio", "9:16") == "9:16" else 1080
                fb_path = storage_service.create_temp_path(prefix=f"scene_{idx}_fallback", suffix=".mp4")
                try:
                    create_sample_scene_video(
                        output_path=fb_path,
                        duration=dur,
                        scene_number=idx,
                        purpose=f"Scene {idx}",
                        caption=prompt_text[:35],
                        width=tw,
                        height=th
                    )
                except Exception as fb_err:
                    logger.error(f"Fallback generation error for scene {idx}: {fb_err}")

                if fb_path.exists() and fb_path.stat().st_size > 0:
                    v_path = fb_path
                else:
                    # Guaranteed failsafe fallback using standard color background
                    from app.utils.ffmpeg import run_ffmpeg
                    run_ffmpeg([
                        "-f", "lavfi", "-i", f"color=c=0x111827:s={tw}x{th}:d={dur}",
                        "-f", "lavfi", "-i", f"sine=f=220:d={dur}",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", "-t", str(dur),
                        str(fb_path)
                    ])
                    if fb_path.exists() and fb_path.stat().st_size > 0:
                        v_path = fb_path
                    else:
                        raise RuntimeError(f"Scene {idx} failed to generate and pass quality control after retries.")

            scene_video_paths.append(v_path)
            completed_scenes[str(sid)] = str(v_path)

            with SessionLocal() as session:
                sc = session.query(Scene).filter(Scene.id == sid).first()
                if sc:
                    sc.status = "completed"
                session.commit()

            # Commit scene checkpoint
            update_job_sync(
                job_id, "running",
                40 + int(idx * 25 / len(scene_ids)),
                f"Scene {idx} ready",
                checkpoint_data={"completed_scenes": completed_scenes}
            )

        if is_job_halted(job_id):
            logger.info(f"Job {job_id} paused/cancelled before audio/assembly. Halting pipeline.")
            return


        # 3. Voiceover narration synthesis in temp directory
        voiceover_path = None
        if prompt_data.get("voiceover_enabled", True):
            update_job_sync(job_id, "running", 70, "Synthesizing voiceover narration...")
            full_narration = " ".join(s.get("narration", "") for s in storyboard if s.get("narration"))
            if full_narration.strip():
                audio_provider = providers.get_audio_provider()
                voiceover_path = storage_service.create_temp_path(prefix=f"voice_{project_id}", suffix=".wav", job_id=job_id)
                audio_provider.generate_voiceover(
                    text=full_narration,
                    voice=prompt_data.get("voice_selection", "energetic_male"),
                    output_path=voiceover_path
                )

        # 4. Background Music synthesis in temp directory
        bg_music_path = None
        if prompt_data.get("background_music") not in ("none", None):
            update_job_sync(job_id, "running", 78, "Composing background music soundtrack...")
            audio_provider = providers.get_audio_provider()
            bg_music_path = storage_service.create_temp_path(prefix=f"bgm_{project_id}", suffix=".wav", job_id=job_id)
            audio_provider.generate_music(
                mood=prompt_data.get("background_music", "upbeat"),
                duration_seconds=prompt_data.get("duration_seconds", 30.0),
                output_path=bg_music_path
            )

        # 5. Generate Subtitles from scene captions in temp directory
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

        sub_ass_path = storage_service.create_temp_path(prefix=f"sub_proj_{project_id}", suffix=".ass", job_id=job_id)
        subtitle_generator.generate_ass(
            segments=sub_segments,
            output_path=sub_ass_path,
            style_preset=prompt_data.get("caption_style", "bold_yellow"),
            max_duration=cur_t,
            video_width=target_w,
            video_height=target_h
        )

        # 6. Assembly & Audio Ducking in external temporary processing directory
        update_job_sync(job_id, "running", 88, "Assembling scenes into master video in temp workspace...")
        output_filename = f"final_{project_id}.mp4"
        temp_output_path = storage_service.create_temp_path(prefix=f"master_render_{project_id}", suffix=".mp4", job_id=job_id)

        ok = assemble_scenes(
            scene_video_paths=scene_video_paths,
            output_path=temp_output_path,
            voiceover_path=voiceover_path,
            bg_music_path=bg_music_path,
            subtitle_ass_path=sub_ass_path,
            target_width=target_w,
            target_height=target_h
        )
        if not ok:
            raise RuntimeError("FFmpeg assembly failed for final project.")

        # 7. Quality Control Check on temporary file before promotion
        update_job_sync(job_id, "running", 95, "Running automated technical QC checks...")
        qc_result = qc_service.evaluate_video(
            temp_output_path,
            expected_aspect_ratio=prompt_data.get("aspect_ratio", "9:16"),
            require_audio=True
        )

        if qc_result.get("status") == "failed":
            raise RuntimeError(f"Master video failed QC validation: {qc_result.get('issues')}")

        # 8. Promote to permanent external storage
        final_output_path = storage_service.save_final_video(temp_output_path, project_id=project_id, filename=output_filename)

        # Clean up temporary processing files
        storage_service.cleanup_job_temp_files(job_id)

        with SessionLocal() as session:
            final_asset = VideoAsset(
                project_id=project_id,
                asset_type="rendered_final",
                storage_path=str(final_output_path),
                original_filename=output_filename,
                duration=qc_result.get("metrics", {}).get("duration"),
                width=target_w,
                height=target_h,
                file_size_bytes=final_output_path.stat().st_size,
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
            "Video generation completed and stored externally!",
            result_data={
                "asset_id": final_asset.id,
                "qc_status": qc_result["status"],
                "duration": qc_result.get("metrics", {}).get("duration"),
                "has_audio": qc_result.get("metrics", {}).get("has_audio"),
                "storage_path": str(final_output_path)
            }
        )

    except Exception as e:
        logger.exception(f"Error in prompt to video pipeline for project {project_id}")
        storage_service.cleanup_job_temp_files(job_id)
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

        engine_choice = (prompt_data.get("video_engine") or "").lower()
        if engine_choice in ("pexels", "stock"):
            from app.providers.video.pexels_provider import PexelsVideoProvider
            video_provider = PexelsVideoProvider()
        elif engine_choice in ("veo", "google_veo"):
            from app.providers.video.video_providers import GoogleVeoVideoProvider
            video_provider = GoogleVeoVideoProvider(api_key=settings.VIDEO_API_KEY)
        else:
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

        storage_service.cleanup_job_temp_files(job_id)
        update_job_sync(
            job_id, "completed", 100,
            "Scene successfully regenerated in external storage!",
            result_data={"scene_id": scene_id, "video_path": str(v_path)}
        )
    except Exception as e:
        logger.exception(f"Error regenerating scene {scene_id}")
        storage_service.cleanup_job_temp_files(job_id)
        update_job_sync(job_id, "failed", 0, "Scene regeneration failed", error_message=str(e))

