# ClipForge AI — Agent Architecture & Production Contracts

ClipForge AI employs a modular agentic architecture where AI reasoning is applied strictly where intelligence and semantic evaluation are needed, while video rendering, audio ducking, and spatial cropping are handled deterministically via FFmpeg and OpenCV.

---

## 1. Creative Planner Agent (`creative_planner.py`)

### Role
Acts as the Executive Video Director. Understands the user's high-level natural language prompt, target social media platform constraints (Instagram Reels vs YouTube Shorts), pacing, and tone.

### Input
- `prompt`: String
- `target_platform`: "instagram_reels" | "youtube_shorts"
- `duration_seconds`: Float (15s to 60s)
- `visual_style`: "cinematic" | "commercial" | "anime" | "3d_render"

### Output Contract
```json
{
  "title": "Fitness Tracker Reel",
  "platform": "instagram_reels",
  "duration_seconds": 30.0,
  "hook": "Stop scrolling and see the future of fitness.",
  "core_message": "Real-time AI biometrics tracking in your pocket.",
  "call_to_action": "Follow and tap the link in bio!"
}
```

---

## 2. Storyboard Agent (`storyboard_agent.py`)

### Role
Translates the conceptual script into a concrete scene-by-scene storyboard. Assigns scene duration, purpose (hook, problem, demonstration, proof, CTA), camera movements, visual generation prompts, voiceover text, and burned subtitle text.

### Output Contract
Array of `StructuredScenePlan`:
```json
[
  {
    "scene_number": 1,
    "duration_seconds": 5.0,
    "purpose": "hook",
    "visual_prompt": "Cinematic macro shot of glowing futuristic biometric sensor, dramatic lighting",
    "camera_movement": "slow_push_in",
    "narration": "Meet the device that changes fitness forever.",
    "caption": "MEET THE FUTURE OF FITNESS",
    "transition": "fade"
  }
]
```

---

## 3. Clip Selection & Viral Ranking Agent (`clip_ranker.py`)

### Role
Analyzes transcripts and scene boundaries from long-form uploaded videos. Identifies standalone moments, evaluates curiosity and hook potential, aligns cuts to speech pauses, and computes normalized ranking scores.

### Multi-Factor Ranking Formulation
$$Score = w_1 \cdot S_{hook} + w_2 \cdot S_{duration} + w_3 \cdot S_{coherence} + w_4 \cdot S_{density}$$

- **$S_{hook}$**: Scored via question structure ("why", "how", "what if"), curiosity triggers, and emotional markers.
- **$S_{duration}$**: Gaussian penalty centered on optimal platform duration (25–35 seconds).
- **$S_{coherence}$**: Rewards complete sentence starts and terminal punctuation.
- **Boundary Snapping**: Start and end timestamps snap to speech pause timestamps to avoid cutting words or mid-syllable phonemes.

---

## 4. Smart Vertical Cropping Engine (`crop_detector.py`)

### Role
Converts horizontal landscape video (16:9) into vertical (9:16) format for Reels and Shorts without geometric distortion.

### Modes
1. **Smart Tracking**: Samples frames across clip segment, computes normalized horizontal center of the primary subject, applies temporal median smoothing, and centers the 1080x1920 crop window.
2. **Blurred Background**: Scales original footage to fit 1080x1920 while preserving aspect ratio, layers it over a boxblurred, scaled background fill.
3. **Center Crop**: Crops the middle 1080 horizontal pixels across 1920 height.

---

## 5. Technical Quality Control Agent (`qc_service.py`)

### Role
Inspects final rendered media before preview or download delivery.

### Technical Validations
- Video and audio streams present and decodable.
- Aspect ratio matches target ($9:16$ vertical format).
- Duration conforms to requested bounds.
- No corrupt frames or missing audio tracks.
- Output reported via structured JSON report with status: `"passed"` or `"needs_revision"`.

