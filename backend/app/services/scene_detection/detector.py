import subprocess
from pathlib import Path
from typing import List
from app.core.config import settings
from app.core.logging import logger

class SceneDetector:
    def detect_scenes(self, video_path: Path, threshold: float = 0.35) -> List[float]:
        """
        Detect scene boundaries and shot changes using FFmpeg scene filter.
        Returns a sorted list of timestamps in seconds.
        """
        if not video_path.exists():
            return [0.0]

        cmd = [
            settings.FFMPEG_PATH,
            "-i", str(video_path),
            "-filter_complex", f"select='gt(scene,{threshold})',metadata=print:key=lavfi.scene_score",
            "-f", "null",
            "-"
        ]

        cuts = [0.0]
        try:
            # Run FFmpeg and capture stderr for metadata lines
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

            # Look for lines: "pts_time:12.3456"
            for line in proc.stderr.splitlines():
                if "pts_time:" in line:
                    parts = line.split("pts_time:")
                    if len(parts) > 1:
                        time_part = parts[1].split()[0]
                        try:
                            t = float(time_part)
                            if not cuts or abs(t - cuts[-1]) >= 1.5:  # Debounce cuts closer than 1.5s
                                cuts.append(t)
                        except ValueError:
                            pass
        except Exception as e:
            logger.warning(f"FFmpeg scene detection error: {e}")

        logger.info(f"Detected {len(cuts)} scene boundaries for {video_path.name}")
        return cuts

scene_detector = SceneDetector()

