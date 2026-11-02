import re
from typing import Dict, Any, List, Optional
from app.core.logging import logger

class ConsistencyEngine:
    """
    Enforces character visual consistency, lighting continuity,
    and natural camera movement across multi-scene video generation.
    """

    CAMERA_PROGRESSION = [
        "slow_push_in",       # Scene 1: Hook / Intrigue
        "dynamic_tracking",   # Scene 2: Action / Demonstration
        "intense_close_up",   # Scene 3: Emotional / Core Feature
        "orbit_spin",         # Scene 4: Showcase
        "cinematic_pull_out"  # Outro / CTA
    ]

    NEGATIVE_PROMPT_DEFAULT = (
        "deformed, morphing, face distortion, extra limbs, frame jitter, flickering, "
        "changing attire, inconsistent face, low resolution, artifacts, blurry"
    )

    STYLE_LIGHTING_PRESETS = {
        "cinematic": "anamorphic lens flare, 35mm film grain, 8k photorealistic, dramatic volumetric lighting, shallow depth of field",
        "commercial": "crisp studio key lighting, vibrant saturated color grade, clean commercial aesthetic, ultra high definition",
        "anime": "vibrant Japanese anime style, clean line art, dynamic anime shading, rich cel-shaded color palette",
        "3d_render": "octane render, unreal engine 5, raytraced global illumination, metallic reflections, subsurface scattering"
    }

    def extract_visual_anchor(self, prompt: str, visual_style: str = "cinematic") -> Dict[str, str]:
        """
        Derives character / subject visual anchor from user prompt to prevent character drift.
        """
        lighting = self.STYLE_LIGHTING_PRESETS.get(visual_style, self.STYLE_LIGHTING_PRESETS["cinematic"])

        # Detect primary subject keywords
        subject = "featured protagonist"
        if re.search(r"\b(woman|girl|female)\b", prompt, re.I):
            subject = "confident 26-year-old woman with consistent facial features, athletic silhouette, modern styling"
        elif re.search(r"\b(man|guy|male)\b", prompt, re.I):
            subject = "charismatic 28-year-old man with consistent facial features, sharp jawline, modern athletic styling"
        elif re.search(r"\b(robot|ai|cyborg|mech)\b", prompt, re.I):
            subject = "sleek obsidian and chrome humanoid AI robot with consistent glowing neon amber accents and intricate mechanical joints"
        elif re.search(r"\b(shoe|sneaker|product|watch|device)\b", prompt, re.I):
            subject = "flagship futuristic product with glowing illuminated sensors, matte-black finish, exact consistent design details"

        return {
            "subject_anchor": subject,
            "lighting_anchor": lighting,
            "negative_prompt": self.NEGATIVE_PROMPT_DEFAULT
        }

    def enrich_storyboard_for_consistency(
        self,
        storyboard: List[Dict[str, Any]],
        visual_style: str = "cinematic",
        user_prompt: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Injects character anchors, camera continuity, and natural motion guidance into each scene.
        """
        anchor = self.extract_visual_anchor(user_prompt, visual_style)
        enriched = []

        total_scenes = len(storyboard)
        for idx, scene in enumerate(storyboard):
            s = dict(scene)
            scene_num = s.get("scene_number", idx + 1)
            purpose = s.get("purpose", "demonstration")

            # Assign progressive camera motion if not specified
            camera_motion = s.get("camera_movement")
            if not camera_motion or camera_motion == "static":
                camera_motion = self.CAMERA_PROGRESSION[(scene_num - 1) % len(self.CAMERA_PROGRESSION)]
            s["camera_movement"] = camera_motion

            # Motion scale (1-10) for natural motion
            if purpose == "hook":
                motion_strength = 7.5
            elif purpose == "call_to_action":
                motion_strength = 6.0
            else:
                motion_strength = 5.0
            s["motion_strength"] = motion_strength

            # Compose consistent prompt
            base_prompt = s.get("visual_prompt", "")
            consistent_prompt = (
                f"{base_prompt}, depicting {anchor['subject_anchor']}, "
                f"camera motion {camera_motion}, {anchor['lighting_anchor']}"
            )
            s["visual_prompt"] = consistent_prompt
            s["negative_prompt"] = anchor["negative_prompt"]
            s["consistency_anchor"] = anchor["subject_anchor"]

            enriched.append(s)

        logger.info(f"Enriched {total_scenes} scenes with character consistency anchor: '{anchor['subject_anchor'][:40]}...'")
        return enriched

consistency_engine = ConsistencyEngine()

