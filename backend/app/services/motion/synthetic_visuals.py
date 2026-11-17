"""
Synthetic Cinematic Keyframe Generator
Produces rich, layered 1080x1920 visuals with dynamic lighting, particle effects,
and domain silhouettes when network diffusion is offline or restricted.
"""
import cv2
import numpy as np
from pathlib import Path

def create_synthetic_keyframe(prompt: str, width: int = 1080, height: int = 1920, seed: int = 42) -> np.ndarray:
    np.random.seed(seed)
    lower = prompt.lower()
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # 1. Base Radial Gradient Lighting
    y_coords, x_coords = np.ogrid[:height, :width]
    cx, cy = width // 2, int(height * 0.45)

    is_redbull = any(w in lower for w in ["redbull", "red bull", "energy drink", "can", "wings", "adrenaline"])
    is_burger = any(w in lower for w in ["burger", "patty", "grill", "sizzle", "cheese", "food"])
    is_fitness = any(w in lower for w in ["fitness", "workout", "gym", "athlete", "biometric"])

    if is_redbull:
        # High-energy Electric Blue & Deep Crimson/Gold
        c_center = np.array([240, 160, 20], dtype=np.float32)  # Electric Blue/Cyan (BGR)
        c_rim = np.array([30, 20, 180], dtype=np.float32)       # Vivid Red
        c_dark = np.array([15, 8, 25], dtype=np.float32)        # Deep Charcoal
    elif is_burger:
        # Warm Amber, Fiery Orange & Dark Iron
        c_center = np.array([30, 120, 255], dtype=np.float32)  # Fiery Amber (BGR)
        c_rim = np.array([10, 40, 160], dtype=np.float32)       # Deep Crimson
        c_dark = np.array([10, 15, 25], dtype=np.float32)       # Charcoal
    else:
        # Modern Cyber Tech / Indigo
        c_center = np.array([220, 120, 50], dtype=np.float32)
        c_rim = np.array([160, 40, 120], dtype=np.float32)
        c_dark = np.array([20, 10, 15], dtype=np.float32)

    dist = np.sqrt((x_coords - cx) ** 2 + ((y_coords - cy) * 0.7) ** 2)
    max_d = np.sqrt(cx ** 2 + (cy * 0.7) ** 2)
    norm_dist = np.clip(dist / max_d, 0.0, 1.0)[:, :, np.newaxis]

    # Blend 3-stop background
    bg = (1.0 - norm_dist) * c_center + norm_dist * c_rim
    vignette = np.clip(1.3 - norm_dist * 0.7, 0.2, 1.0)
    img = np.clip(bg * vignette, 0, 255).astype(np.uint8)

    # 2. Add Background Motion Streaks & Volumetric Light Rays
    for _ in range(12):
        angle = np.random.uniform(-0.4, 0.4)
        x_start = np.random.randint(0, width)
        length = np.random.randint(600, 1400)
        thickness = np.random.randint(2, 6)
        x_end = int(x_start + length * np.sin(angle))
        y_end = int(height * 0.8)
        color = (int(c_center[0] * 0.8), int(c_center[1] * 0.8), int(c_center[2] * 0.8))
        cv2.line(img, (x_start, 0), (x_end, y_end), color, thickness, cv2.LINE_AA)

    # Blur background beams
    img = cv2.GaussianBlur(img, (45, 45), 0)

    # 3. Draw Foreground Hero Subject
    overlay = img.copy()
    if is_redbull:
        # Metallic Slim Energy Can Silhouette
        can_w, can_h = int(width * 0.38), int(height * 0.42)
        can_x1 = (width - can_w) // 2
        can_y1 = cy - can_h // 2
        can_x2 = can_x1 + can_w
        can_y2 = can_y1 + can_h

        # Can body
        cv2.rectangle(overlay, (can_x1, can_y1 + 40), (can_x2, can_y2 - 20), (190, 195, 205), -1)
        # Metallic bevels
        cv2.ellipse(overlay, (cx, can_y1 + 40), (can_w // 2, 25), 0, 0, 360, (230, 235, 245), -1)
        cv2.ellipse(overlay, (cx, can_y2 - 20), (can_w // 2, 25), 0, 0, 360, (140, 145, 155), -1)

        # Red Bull Signature Diagonal Color Blocks (Silver, Blue, Red)
        pts_blue = np.array([[can_x1, can_y1 + 100], [can_x2, can_y1 + 40], [can_x2, can_y1 + 220], [can_x1, can_y1 + 280]])
        cv2.fillPoly(overlay, [pts_blue], (160, 40, 20))
        pts_red = np.array([[can_x1, can_y1 + 280], [can_x2, can_y1 + 220], [can_x2, can_y1 + 380], [can_x1, can_y1 + 440]])
        cv2.fillPoly(overlay, [pts_red], (30, 25, 210))

        # Can Rim Highlight
        cv2.line(overlay, (can_x1 + 15, can_y1 + 50), (can_x1 + 15, can_y2 - 30), (255, 255, 255), 8, cv2.LINE_AA)
        cv2.line(overlay, (can_x2 - 15, can_y1 + 50), (can_x2 - 15, can_y2 - 30), (255, 230, 180), 6, cv2.LINE_AA)

        # Condensation Frost Droplets & Sparks
        for _ in range(150):
            fx = np.random.randint(can_x1, can_x2)
            fy = np.random.randint(can_y1 + 40, can_y2 - 20)
            r = np.random.randint(2, 6)
            cv2.circle(overlay, (fx, fy), r, (255, 255, 255), -1)

        # Lightning energy arcs
        for _ in range(4):
            pts = []
            lx, ly = cx + np.random.randint(-150, 150), can_y1 + np.random.randint(-50, 50)
            for step in range(6):
                pts.append((int(lx), int(ly)))
                lx += np.random.randint(-40, 40)
                ly += np.random.randint(60, 110)
            for p_i in range(len(pts) - 1):
                cv2.line(overlay, pts[p_i], pts[p_i + 1], (255, 255, 200), 3, cv2.LINE_AA)

    elif is_burger:
        # Gourmet Burger Silhouette
        bw, bh = int(width * 0.55), int(height * 0.28)
        # Brioche Bun Top
        cv2.ellipse(overlay, (cx, cy - 60), (bw // 2, 80), 0, 180, 360, (40, 140, 220), -1)
        # Sizzling Patty
        cv2.rectangle(overlay, (cx - bw // 2, cy - 20), (cx + bw // 2, cy + 40), (25, 40, 70), -1)
        # Melted Cheese Layer
        pts_cheese = np.array([
            [cx - bw // 2, cy - 10], [cx - bw // 3, cy + 50], [cx - bw // 6, cy],
            [cx + bw // 8, cy + 65], [cx + bw // 3, cy + 5], [cx + bw // 2, cy - 10]
        ])
        cv2.fillPoly(overlay, [pts_cheese], (30, 200, 255))
        # Bun Bottom
        cv2.ellipse(overlay, (cx, cy + 60), (bw // 2, 45), 0, 0, 360, (35, 120, 200), -1)

    # Smooth Alpha Blend
    cv2.addWeighted(overlay, 0.88, img, 0.12, 0, img)

    # 4. Cinematic Lens Flare in Top-Left / Center
    flare_center = (cx - 120, cy - 220)
    for r, alpha in [(300, 0.08), (180, 0.14), (80, 0.25), (25, 0.6)]:
        flare_mask = np.zeros_like(img)
        cv2.circle(flare_mask, flare_center, r, (255, 245, 220), -1)
        flare_mask = cv2.GaussianBlur(flare_mask, (61, 61), 0)
        img = cv2.addWeighted(img, 1.0, flare_mask, alpha, 0)

    # 5. Vignette border
    border_mask = cv2.normalize(norm_dist, None, 0, 1, cv2.NORM_MINMAX)
    if len(border_mask.shape) == 2:
        border_mask = border_mask[:, :, np.newaxis]
    img = (img.astype(np.float32) * (1.0 - border_mask * 0.35)).astype(np.uint8)

    return img
