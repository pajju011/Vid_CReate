import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from app.core.logging import logger

class SmartCropDetector:
    def __init__(self):
        self.cascade = None
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            try:
                self.cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                self.cascade = None

    def detect_subject_horizontal_offset(
        self,
        video_path: Path,
        start_time: float = 0.0,
        end_time: float = 10.0,
        num_samples: int = 10
    ) -> float:
        """
        Samples video frames between start_time and end_time to locate the primary subject's
        horizontal position. Returns a normalized x offset between 0.0 and 1.0 (0.5 = center).
        """
        if not video_path.exists():
            return 0.5

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning(f"Failed to open video for subject tracking: {video_path}")
            return 0.5

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920

        start_frame = int(start_time * fps)
        end_frame = min(total_frames - 1, int(end_time * fps))
        if end_frame <= start_frame:
            end_frame = min(total_frames - 1, start_frame + int(fps * 5))

        step = max(1, (end_frame - start_frame) // max(1, num_samples))
        detected_x_positions = []

        for frame_idx in range(start_frame, end_frame, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # 1. Try face cascade if available
            found_face = False
            if self.cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                if len(faces) > 0:
                    largest = max(faces, key=lambda f: f[2] * f[3])
                    fx, fy, fw, fh = largest
                    detected_x_positions.append((fx + fw / 2.0) / video_width)
                    found_face = True

            # 2. Visual saliency / luminance center-of-mass fallback
            if not found_face:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Downsample for fast centroid calculation
                small = cv2.resize(gray, (160, 90))
                # Threshold high contrast / subject regions
                _, thresh = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                M = cv2.moments(thresh)
                if M["m00"] > 0:
                    cX = M["m10"] / M["m00"]
                    detected_x_positions.append(cX / 160.0)

        cap.release()

        if detected_x_positions:
            median_x = float(np.median(detected_x_positions))
            clamped_x = max(0.25, min(0.75, median_x))
            logger.info(f"Smart crop calculated subject offset: {clamped_x:.3f}")
            return clamped_x

        return 0.5

crop_detector = SmartCropDetector()
