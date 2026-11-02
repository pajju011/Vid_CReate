import json
import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic local AI planner for offline, demo, and zero-cost development.
    Produces high-quality, structured storyboards and viral clip selections.
    """
    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        return {
            "title": f"Viral Short: {prompt[:30].strip()}",
            "platform": platform,
            "duration_seconds": duration_seconds,
            "hook": f"Stop scrolling! Here is what you need to know about {prompt[:40]}.",
            "core_message": f"Discover how {prompt} is transforming everything right now.",
            "call_to_action": "Follow for more daily insights and drop your thoughts below!"
        }

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        duration_per_scene = round(script_data.get("duration_seconds", 30.0) / max(1, num_scenes), 1)
        purposes = ["hook", "problem", "solution", "demonstration", "call_to_action"]

        scenes = []
        for i in range(1, num_scenes + 1):
            purpose = purposes[(i - 1) % len(purposes)]
            if purpose == "hook":
                prompt_text = f"Cinematic ultra-detailed macro opening shot, high energy {style} lighting"
                narration = script_data.get("hook", "Stop scrolling and check this out.")
                caption = "STOP SCROLLING!"
            elif purpose == "call_to_action":
                prompt_text = f"Sleek dynamic outro shot with 3D glowing graphics, {style} aesthetic"
                narration = script_data.get("call_to_action", "Follow for more and share!")
                caption = "FOLLOW FOR MORE!"
            else:
                prompt_text = f"Fast-paced visual showing key benefits, smooth camera pan, {style} visual style"
                narration = "Witness the seamless power and efficiency in action."
                caption = "NEXT-GEN PERFORMANCE"

            scenes.append({
                "scene_number": i,
                "duration_seconds": duration_per_scene,
                "purpose": purpose,
                "visual_prompt": prompt_text,
                "camera_movement": "slow_push_in" if i % 2 == 1 else "tracking_pan",
                "narration": narration,
                "caption": caption,
                "transition": "fade"
            })
        return scenes

    def analyze_transcript(self, transcript_text: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "topic": "Key Insight",
                "summary": "High engagement core revelation in speech",
                "start_time": 0.0,
                "end_time": min(28.0, float(len(segments) * 3))
            }
        ]

    def rank_clips(self, candidate_clips: List[Dict[str, Any]], target_platform: str) -> List[Dict[str, Any]]:
        return sorted(candidate_clips, key=lambda c: c.get("score", 0.0), reverse=True)

class GeminiLLMProvider(BaseLLMProvider):
    """Real Google Gemini API provider adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        sys_instruction = (
            f"You are an expert short-form viral scriptwriter for {platform}. "
            f"Return ONLY valid JSON with keys: 'title', 'platform', 'duration_seconds', 'hook', 'core_message', 'call_to_action'."
        )
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{sys_instruction}\nUser Prompt: {prompt}\nTarget Duration: {duration_seconds}s"
                }]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Gemini API error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Gemini API returned error: {resp.status_code} - {resp.text}")
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        sys_instruction = (
            f"Generate a {num_scenes}-scene storyboard in {style} style for {script_data.get('platform', 'reels')}. "
            "Return ONLY a JSON array of objects with keys: 'scene_number', 'duration_seconds', 'purpose', 'visual_prompt', 'camera_movement', 'narration', 'caption', 'transition'."
        )
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{sys_instruction}\nScript Context: {json.dumps(script_data)}"
                }]
            }],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API returned error: {resp.status_code} - {resp.text}")
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

    def analyze_transcript(self, transcript_text: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return MockLLMProvider().analyze_transcript(transcript_text, segments)

    def rank_clips(self, candidate_clips: List[Dict[str, Any]], target_platform: str) -> List[Dict[str, Any]]:
        return MockLLMProvider().rank_clips(candidate_clips, target_platform)
