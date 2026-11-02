from pathlib import Path
from typing import List, Dict, Any, Optional

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp string: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp string: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class SubtitleGenerator:
    ASS_STYLES = {
        "bold_yellow": {
            "fontname": "Arial",
            "fontsize": "56",
            "primary": "&H0000FFFF",   # BGR Yellow
            "secondary": "&H000000FF",
            "outline": "&H00000000",   # Solid Black Outline
            "back": "&H00000000",
            "bold": "-1",
            "italic": "0",
            "outline_w": "4",
            "shadow": "2",
            "alignment": "2",          # Bottom Center
            "margin_v": "140"
        },
        "clean_minimal": {
            "fontname": "Arial",
            "fontsize": "46",
            "primary": "&H00FFFFFF",   # Crisp White
            "secondary": "&H000000FF",
            "outline": "&H00101010",
            "back": "&H00000000",
            "bold": "0",
            "italic": "0",
            "outline_w": "2",
            "shadow": "1",
            "alignment": "2",
            "margin_v": "120"
        },
        "creator_box": {
            "fontname": "Arial",
            "fontsize": "50",
            "primary": "&H00FFFFFF",
            "secondary": "&H000000FF",
            "outline": "&H00000000",
            "back": "&H90000000",      # Translucent background box
            "bold": "-1",
            "italic": "0",
            "outline_w": "1",
            "shadow": "0",
            "alignment": "2",
            "margin_v": "150"
        },
        "cinematic": {
            "fontname": "Georgia",
            "fontsize": "48",
            "primary": "&H00E0E0E0",   # Soft ivory
            "secondary": "&H000000FF",
            "outline": "&H00202020",
            "back": "&H00000000",
            "bold": "0",
            "italic": "1",
            "outline_w": "2",
            "shadow": "2",
            "alignment": "2",
            "margin_v": "110"
        }
    }

    def generate_ass(
        self,
        segments: List[Dict[str, Any]],
        output_path: Path,
        style_preset: str = "bold_yellow",
        time_offset: float = 0.0,
        max_duration: Optional[float] = None,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """
        Generate an ASS subtitle file from segment timestamp data.
        time_offset is subtracted from timestamps to align with trimmed clip segments.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        style = self.ASS_STYLES.get(style_preset, self.ASS_STYLES["bold_yellow"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['fontname']},{style['fontsize']},{style['primary']},{style['secondary']},{style['outline']},{style['back']},{style['bold']},{style['italic']},0,0,100,100,0,0,1,{style['outline_w']},{style['shadow']},{style['alignment']},40,40,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for seg in segments:
            seg_start = seg.get("start", 0.0) - time_offset
            seg_end = seg.get("end", 0.0) - time_offset
            text = seg.get("text", "").strip()

            if not text:
                continue

            # Bounds checking
            if seg_end <= 0:
                continue
            if max_duration and seg_start >= max_duration:
                continue

            start_clamped = max(0.0, seg_start)
            end_clamped = min(max_duration, seg_end) if max_duration else seg_end

            if end_clamped <= start_clamped:
                continue

            # Check if word timestamps exist for animated word highlighting
            words = seg.get("words", [])
            if words and len(words) > 1 and style_preset == "bold_yellow":
                # Create word-level karaoke or uppercase emphasis
                text_formatted = text.upper()
            else:
                text_formatted = text

            start_str = format_ass_time(start_clamped)
            end_str = format_ass_time(end_clamped)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_formatted}")

        full_content = header + "\n".join(events) + "\n"
        output_path.write_text(full_content, encoding="utf-8")
        return output_path

    def generate_srt(
        self,
        segments: List[Dict[str, Any]],
        output_path: Path,
        time_offset: float = 0.0,
        max_duration: Optional[float] = None
    ) -> Path:
        """Generate a standard SRT subtitle file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        index = 1
        for seg in segments:
            seg_start = seg.get("start", 0.0) - time_offset
            seg_end = seg.get("end", 0.0) - time_offset
            text = seg.get("text", "").strip()
            if not text:
                continue
            if seg_end <= 0:
                continue
            if max_duration and seg_start >= max_duration:
                continue
            start_clamped = max(0.0, seg_start)
            end_clamped = min(max_duration, seg_end) if max_duration else seg_end
            if end_clamped <= start_clamped:
                continue

            lines.append(f"{index}")
            lines.append(f"{format_srt_time(start_clamped)} --> {format_srt_time(end_clamped)}")
            lines.append(f"{text}\n")
            index += 1

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

subtitle_generator = SubtitleGenerator()
