from pathlib import Path
from app.services.subtitles.subtitle_generator import subtitle_generator
from app.core.config import settings

def test_generate_ass_subtitles():
    segments = [
        {"start": 1.0, "end": 4.5, "text": "Next-level automated shorts generation."},
        {"start": 5.0, "end": 9.0, "text": "Built for modern creators."}
    ]
    out_file = settings.TEMP_DIR / "test_subs.ass"
    res = subtitle_generator.generate_ass(
        segments=segments,
        output_path=out_file,
        style_preset="bold_yellow",
        time_offset=0.0
    )
    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "Dialogue:" in content
    assert "NEXT-LEVEL AUTOMATED" in content

def test_generate_srt_subtitles():
    segments = [
        {"start": 0.0, "end": 2.5, "text": "Clean minimal captions."}
    ]
    out_file = settings.TEMP_DIR / "test_subs.srt"
    res = subtitle_generator.generate_srt(
        segments=segments,
        output_path=out_file
    )
    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in content
    assert "Clean minimal captions." in content

