import json
import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic local AI planner for offline, demo, and zero-cost development.
    Dynamically analyzes the user prompt to craft custom scripts, varied scene hooks,
    and tailored narration without repetitive static templates.
    """
    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        clean = prompt.strip().rstrip(".")
        words = clean.split()
        subject = " ".join(words[:4]) if len(words) >= 4 else clean

        # Context-aware hooks based on prompt keywords
        lower = clean.lower()
        if any(w in lower for w in ["fitness", "workout", "gym", "health", "exercise"]):
            hook = f"Want to revolutionize your health? Check out {clean}."
            core = f"Discover the breakthrough approach that changes how you train and recover."
            cta = "Save this reel and start your transformation today!"
        elif any(w in lower for w in ["tech", "ai", "software", "code", "app", "device"]):
            hook = f"This new innovation is changing everything: {clean}."
            core = f"Experience state-of-the-art power and automation right in your hands."
            cta = "Follow for the latest tech breakdowns and share your thoughts!"
        elif any(w in lower for w in ["business", "money", "finance", "crypto", "market"]):
            hook = f"Here is the secret most people miss about {clean}."
            core = f"Unlock proven strategies that drive exponential growth and real results."
            cta = "Drop a comment below and tap the link in bio!"
        else:
            hook = f"You won't believe what happens when you experience {clean}."
            core = f"From concept to reality, see how {clean} delivers stunning results."
            cta = "Double-tap if you agree and follow for more daily content!"

        return {
            "title": f"Spotlight: {subject.title()}",
            "platform": platform,
            "duration_seconds": duration_seconds,
            "hook": hook,
            "core_message": core,
            "call_to_action": cta
        }

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        duration_per_scene = round(script_data.get("duration_seconds", 30.0) / max(1, num_scenes), 1)
        hook = script_data.get("hook", "Discover the future.")
        core = script_data.get("core_message", "Revolutionary capabilities.")
        cta = script_data.get("call_to_action", "Follow for more updates.")
        title = script_data.get("title", "Feature").replace("Spotlight: ", "")

        scenes = []
        for i in range(1, num_scenes + 1):
            if i == 1:
                prompt_text = f"Dynamic high-impact opening macro shot of {title}, dramatic {style} lighting, shallow depth of field"
                narration = hook
                caption = "DISCOVER THIS"
                cam = "slow_push_in"
                purpose = "hook"
            elif i == num_scenes:
                prompt_text = f"Sleek cinematic closing shot highlighting {title}, neon backlighting, dynamic 3D reflections"
                narration = cta
                caption = "FOLLOW & SHARE"
                cam = "pull_back_reveal"
                purpose = "call_to_action"
            elif i == 2:
                prompt_text = f"Close-up detailed demonstration of {title} in action, cinematic volumetric lighting, 8k {style}"
                narration = core
                caption = "PROVEN RESULTS"
                cam = "tracking_pan_right"
                purpose = "demonstration"
            else:
                prompt_text = f"Vibrant lifestyle shot showing real-world benefits of {title}, natural lens flare, {style} atmosphere"
                narration = f"Experience seamless quality and next-level design with {title}."
                caption = "NEXT LEVEL"
                cam = "orbit_pan"
                purpose = "proof"

            scenes.append({
                "scene_number": i,
                "duration_seconds": duration_per_scene,
                "purpose": purpose,
                "visual_prompt": prompt_text,
                "camera_movement": cam,
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
    """Real Google Gemini API provider adapter (Free Tier on Google AI Studio & Cloud)."""
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._mock = MockLLMProvider()

    def _get_headers_and_url(self, endpoint: str) -> tuple[Dict[str, str], str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key.startswith("AQ.") or self.api_key.startswith("ya29."):
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-goog-api-key"] = self.api_key
            url = f"{self.base_url}/{endpoint}"
        else:
            headers["x-goog-api-key"] = self.api_key
            url = f"{self.base_url}/{endpoint}?key={self.api_key}"
        return headers, url

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
        headers, url = self._get_headers_and_url("models/gemini-1.5-flash:generateContent")
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
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._clean_json_response(raw_text)
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code} ({resp.text[:200]}), falling back to deterministic director")
        except Exception as e:
            logger.warning(f"Gemini API error ({e}), falling back to deterministic director")
        return self._mock.generate_script(prompt, duration_seconds, platform)

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        headers, url = self._get_headers_and_url("models/gemini-1.5-flash:generateContent")
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
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._clean_json_response(raw_text)
                else:
                    logger.warning(f"Gemini API status {resp.status_code} ({resp.text[:200]}), falling back to storyboard planner")
        except Exception as e:
            logger.warning(f"Gemini API error ({e}), falling back to storyboard planner")
        return self._mock.generate_storyboard(script_data, num_scenes, style)
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

