from pathlib import Path
from app.core.config import settings
from app.utils.sample_media import create_sample_video
from app.utils.ffmpeg import trim_video, convert_to_vertical
from app.services.subtitles.subtitle_generator import subtitle_generator
from app.services.quality_control.qc_service import qc_service

def test_full_video_to_shorts_processing():
    source_video = settings.TEMP_DIR / "e2e_source.mp4"
    trimmed_segment = settings.TEMP_DIR / "e2e_trimmed.mp4"
    sub_path = settings.TEMP_DIR / "e2e_subtitles.ass"
    rendered_short = settings.RENDERS_DIR / "e2e_final_short.mp4"

    # 1. Create realistic source video (1920x1080)
    created = create_sample_video(source_video, duration=10.0, width=1920, height=1080)
    assert created is True
    assert source_video.exists()

    # 2. Trim clip segment (from 2.0 to 7.0 seconds = 5s)
    trimmed = trim_video(source_video, trimmed_segment, start_time=2.0, end_time=7.0)
    assert trimmed is True
    assert trimmed_segment.exists()

    # 3. Create ASS subtitles
    segments = [
        {"start": 0.5, "end": 2.5, "text": "DISCOVER CLIPFORGE AI"},
        {"start": 2.8, "end": 4.5, "text": "AUTOMATED VERTICAL SHORTS"}
    ]
    subtitle_generator.generate_ass(
        segments=segments,
        output_path=sub_path,
        style_preset="bold_yellow",
        max_duration=5.0
    )
    assert sub_path.exists()

    # 4. Render vertical 9:16 short with blurred background & burned subtitles
    converted = convert_to_vertical(
        input_path=trimmed_segment,
        output_path=rendered_short,
        mode="blurred_background",
        target_width=1080,
        target_height=1920,
        subtitle_ass_path=sub_path
    )
    assert converted is True
    assert rendered_short.exists()

    # 5. QC Evaluation
    qc = qc_service.evaluate_video(rendered_short, expected_aspect_ratio="9:16")
    assert qc["status"] == "passed"
    assert qc["metrics"]["width"] == 1080
    assert qc["metrics"]["height"] == 1920
    assert qc["metrics"]["duration"] >= 4.5

