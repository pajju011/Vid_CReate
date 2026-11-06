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
    """Real Google Gemini API provider adapter (Free Tier on Google AI Studio)."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._mock = MockLLMProvider()

    def _clean_json_response(self, text: str) -> Any:
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean = "\n".join(lines).strip()
        return json.loads(clean)

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
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._clean_json_response(raw_text)
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code}, falling back to deterministic director")
        except Exception as e:
            logger.warning(f"Gemini API error ({e}), falling back to deterministic director")
        return self._mock.generate_script(prompt, duration_seconds, platform)

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
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._clean_json_response(raw_text)
                else:
                    logger.warning(f"Gemini API status {resp.status_code}, falling back to storyboard planner")
        except Exception as e:
            logger.warning(f"Gemini API error ({e}), falling back to storyboard planner")
        return self._mock.generate_storyboard(script_data, num_scenes, style)

    def analyze_transcript(self, transcript_text: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._mock.analyze_transcript(transcript_text, segments)

    def rank_clips(self, candidate_clips: List[Dict[str, Any]], target_platform: str) -> List[Dict[str, Any]]:
        return self._mock.rank_clips(candidate_clips, target_platform)

class OllamaLLMProvider(BaseLLMProvider):
    """
    Local Ollama LLM provider adapter.
    100% Offline, Strict Local privacy tier compliant.
    Connects to local Ollama daemon (default: http://localhost:11434).
    """
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        self._mock = MockLLMProvider()

    def _clean_json_response(self, text: str) -> Any:
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        return json.loads(clean)

    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        prompt_text = (
            f"You are an expert short-form viral scriptwriter for {platform}. "
            f"Generate a script for: {prompt}. Duration: {duration_seconds}s. "
            f"Respond ONLY with valid JSON having keys: title, platform, duration_seconds, hook, core_message, call_to_action."
        )
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt_text, "stream": False, "format": "json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return self._clean_json_response(data.get("response", "{}"))
        except Exception as e:
            logger.info(f"Ollama local LLM offline or unreachable ({e}), using deterministic local director")
        return self._mock.generate_script(prompt, duration_seconds, platform)

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        prompt_text = (
            f"Generate a {num_scenes}-scene storyboard in {style} style for {script_data.get('platform', 'reels')}. "
            f"Script: {json.dumps(script_data)}. "
            f"Respond ONLY with a JSON array of scene objects with keys: scene_number, duration_seconds, purpose, visual_prompt, camera_movement, narration, caption, transition."
        )
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt_text, "stream": False, "format": "json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    res = self._clean_json_response(data.get("response", "[]"))
                    if isinstance(res, list) and len(res) > 0:
                        return res
        except Exception as e:
            logger.info(f"Ollama storyboard generation fallback: {e}")
        return self._mock.generate_storyboard(script_data, num_scenes, style)

    def analyze_transcript(self, transcript_text: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._mock.analyze_transcript(transcript_text, segments)

    def rank_clips(self, candidate_clips: List[Dict[str, Any]], target_platform: str) -> List[Dict[str, Any]]:
        return self._mock.rank_clips(candidate_clips, target_platform)

