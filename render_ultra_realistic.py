"""
Ultra-Realistic Red Bull Promo Video Render Script
Combines 8K photorealistic keyframes with 3D Depth-Mesh Parallax,
Edge Neural Voiceover narration, energetic background soundtrack, and kinetic subtitles.
"""
import sys
import os
import shutil
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.motion.parallax_engine import generate_3d_depth_parallax_video
from app.providers.audio.audio_providers import EdgeTTSAudioProvider
from app.services.subtitles.subtitle_generator import subtitle_generator
from app.utils.ffmpeg import assemble_scenes, run_ffmpeg

def main():
    print("=" * 65)
    print("PRODUCING ULTRA-REALISTIC RED BULL 10-SECOND PROMO VIDEO")
    print("=" * 65)

    work_dir = Path("backend_temp_render")
    work_dir.mkdir(exist_ok=True)

    scenes_spec = [
        {
            "img": Path("real_redbull_can.jpg"),
            "duration": 3.5,
            "prompt": "ice cold energy drink can cracking open with freezing condensation",
            "narration": "Feel the sub-zero chill. Crack open pure energy.",
            "caption": "CRACK OPEN PURE ENERGY"
        },
        {
            "img": Path("real_athlete_8k.jpg"),
            "duration": 3.5,
            "prompt": "extreme sports athlete defying gravity in mid-air",
            "narration": "Defy gravity and push beyond every limit.",
            "caption": "DEFY GRAVITY"
        },
        {
            "img": Path("real_hero_shot.jpg"),
            "duration": 3.0,
            "prompt": "energy drink neon reflections gives you wings",
            "narration": "Red Bull gives you wings.",
            "caption": "GIVES YOU WINGS"
        }
    ]

    scene_videos = []
    sub_segments = []
    current_time = 0.0

    # 1. Render 3D Parallax Video for Each Scene
    for i, s in enumerate(scenes_spec, 1):
        out_v = work_dir / f"scene_{i}_parallax.mp4"
        print(f"[1/4] Rendering Scene {i} ({s['duration']}s) with 3D Depth Parallax...")
        ok = generate_3d_depth_parallax_video(
            image_path=s["img"],
            output_path=out_v,
            duration=s["duration"],
            prompt=s["prompt"],
            target_width=1080,
            target_height=1920,
            fps=30
        )
        if not ok or not out_v.exists():
            print(f"Error rendering scene {i}")
            return
        scene_videos.append(out_v)

        dur = s["duration"]
        sub_segments.append({
            "start": current_time,
            "end": current_time + dur,
            "text": s["caption"]
        })
        current_time += dur

    # 2. Voiceover Synthesis
    print("[2/4] Synthesizing energetic human voiceover with Edge Neural TTS...")
    audio_provider = EdgeTTSAudioProvider()
    full_text = " ".join(s["narration"] for s in scenes_spec)
    voice_path = work_dir / "voiceover.wav"
    audio_provider.generate_voiceover(
        text=full_text,
        voice="energetic_male",
        output_path=voice_path
    )

    # 3. Background Music & Subtitles
    print("[3/4] Generating energetic background audio & kinetic subtitles...")
    bgm_path = work_dir / "bgm.wav"
    audio_provider.generate_music(
        mood="energetic",
        duration_seconds=10.0,
        output_path=bgm_path
    )

    sub_ass_path = work_dir / "subtitles.ass"
    subtitle_generator.generate_ass(
        segments=sub_segments,
        output_path=sub_ass_path,
        style_preset="bold_yellow",
        max_duration=10.0,
        video_width=1080,
        video_height=1920
    )

    # 4. Final Assembly
    print("[4/4] Assembling final 10-second master commercial...")
    temp_final = work_dir / "temp_final_master.mp4"
    ok = assemble_scenes(
        scene_video_paths=scene_videos,
        output_path=temp_final,
        voiceover_path=voice_path,
        bg_music_path=bgm_path,
        subtitle_ass_path=sub_ass_path,
        target_width=1080,
        target_height=1920
    )

    if ok and temp_final.exists():
        final_dest = Path("redbull_ultra_realistic_10s.mp4")
        shutil.copy(temp_final, final_dest)
        print("\n" + "=" * 65)
        print(f"SUCCESS! Ultra-realistic video created:")
        print(f"-> {final_dest.resolve()} ({final_dest.stat().st_size:,} bytes)")
        print("=" * 65)
    else:
        print("Assembly failed.")

if __name__ == "__main__":
    main()
