import json
import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider
from app.utils.network import is_network_available

import re
import json
import httpx
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider

def clean_prompt_subject(prompt: str) -> str:
    """Strips command boilerplate to extract the authentic subject matter."""
    clean = prompt.strip().rstrip(".")
    # Remove command patterns like "Create a 20-second cinematic video of..."
    clean = re.sub(
        r'^(create|make|generate|produce|build)\s+(a|an)?\s*(\d+[- ]second|\d+s)?\s*(cinematic|engaging|fast-paced|viral|luxurious)?\s*(video|reel|short|youtube short|instagram reel)?\s*(of|about|featuring)?\s*',
        '',
        clean,
        flags=re.IGNORECASE
    ).strip()
    return clean or prompt.strip()

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic local AI planner for offline, demo, and zero-cost development.
    Intelligently deconstructs user prompt concepts into rich, tailored scenes.
    """
    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        subject = clean_prompt_subject(prompt)
        lower = subject.lower()

        # Domain-specific scripts
        if any(w in lower for w in ["burger", "patty", "cheeseburger"]):
            title = "The Ultimate Gourmet Burger"
            hook = "Hear that sizzle? This is what burger perfection looks like."
            core = "Handcrafted with a crispy sizzling patty, crisp fresh toppings, and gooey melted cheese."
            cta = "Tag a burger lover who needs to taste this right now!"
        elif any(w in lower for w in ["pizza", "cheese", "slice", "dough"]):
            title = "Artisan Wood-Fired Pizza"
            hook = "Look at that epic cheese pull. Real artisan pizza made right."
            core = "Fresh hand-kneaded dough, rich tomato reduction, and bubbly bubbling mozzarella."
            cta = "Save this reel for your next pizza night!"
        elif any(w in lower for w in ["fitness", "workout", "gym", "health", "exercise", "biometric"]):
            title = "Next-Gen AI Fitness"
            hook = "Stop guessing your workouts. Train with real-time biometric intelligence."
            core = "Precision tracking, adaptive heart rate metrics, and effortless peak performance."
            cta = "Tap the link in bio to transform your training today!"
        elif any(w in lower for w in ["tech", "keyboard", "gadget", "software", "code", "device"]):
            title = f"Future Tech: {subject[:30]}"
            hook = f"This innovation is redefining modern performance: {subject[:40]}."
            core = "Ultra-sleek industrial engineering designed for maximum speed and tactile feel."
            cta = "Follow for daily cutting-edge technology breakdowns!"
        elif any(w in lower for w in ["business", "finance", "money", "crypto"]):
            title = "Strategic Breakthrough"
            hook = f"Here is the game-changing insight about {subject[:30]}."
            core = "Unlock the scalable framework driving record performance and modern growth."
            cta = "Save this reel and share it with your team!"
        else:
            title = subject.split(".")[0][:40].title()
            hook = f"Discover the magic of {subject[:45]}."
            core = f"A closer look at how {subject[:45]} comes to life in stunning detail."
            cta = "Double-tap if you loved this and follow for more!"

        return {
            "title": title,
            "platform": platform,
            "duration_seconds": duration_seconds,
            "hook": hook,
            "core_message": core,
            "call_to_action": cta
        }

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        duration_per_scene = round(script_data.get("duration_seconds", 30.0) / max(1, num_scenes), 1)
        hook = script_data.get("hook", "Discover the future.")
        core = script_data.get("core_message", "Crafted with authentic detail.")
        cta = script_data.get("call_to_action", "Follow for more daily content.")
        title = script_data.get("title", "").lower()

        scenes = []
        if any(w in title for w in ["burger", "patty"]):
            templates = [
                ("Crispy thick beef patty sizzling violently on a fiery cast iron grill with smoke and grease droplets", "slow_push_in", "Hear that sizzle? That is pure flavor.", "SIZZLING PATTY", "hook"),
                ("Fresh crisp green lettuce and ripe red tomato slices being carefully placed onto a toasted golden brioche bun", "tracking_pan_right", "Crisp fresh lettuce and ripe vine tomatoes add the perfect crunch.", "FRESH TOPPINGS", "demonstration"),
                ("Thick melted golden cheddar cheese slowly dripping down the warm grilled burger patty", "slow_zoom_in", "Melted aged cheddar dripping with irresistible warmth.", "MELTED CHEESE", "proof"),
                ("Magnificent gourmet double cheeseburger fully assembled on a rustic wooden board, ready to serve", "pull_back_reveal", cta, "JUICY BURGER", "call_to_action"),
            ]
        elif any(w in title for w in ["pizza"]):
            templates = [
                ("Chef stretching fresh artisan dough and spooning rich aromatic tomato sauce in slow motion", "slow_push_in", "Fresh artisan dough crafted with passion.", "ARTISAN DOUGH", "hook"),
                ("Generous shreds of creamy fresh mozzarella and aromatic basil scattered over the pizza", "tracking_pan_right", "Creamy mozzarella and fresh fragrant herbs.", "FRESH CHEESE", "demonstration"),
                ("Golden bubbly pizza crust baking inside a blazing hot wood-fired stone oven", "slow_zoom_in", "Wood-fired stone baking for that irresistible char.", "WOOD-FIRED OVEN", "proof"),
                ("Extreme close up of a steaming slice being lifted with a long stretchy melted cheese pull", "pull_back_reveal", cta, "PERFECT SLICE", "call_to_action"),
            ]
        elif any(w in title for w in ["fitness", "workout", "gym", "biometric"]):
            templates = [
                ("Futuristic sleek biometric fitness tracker sensor glowing on wrist with pulsating neon ring", "slow_push_in", hook, "AI BIOMETRICS", "hook"),
                ("Athlete intensely training with real-time biometric stats overlay showing pulse and cadence", "tracking_pan_right", "Real-time AI biometrics tracking your every heartbeat.", "PEAK PERFORMANCE", "demonstration"),
                ("Macro shot of sleek waterproof sensor reflecting sunlight during intense cardio workout", "slow_zoom_in", "Engineered to withstand your most demanding routines.", "PROVEN ACCURACY", "proof"),
                ("Confident athlete checking positive recovery metrics on modern smartwatch screen, high energy vibe", "pull_back_reveal", cta, "TRANSFORM TODAY", "call_to_action"),
            ]
        else:
            clean_title = script_data.get("title", "Experience")
            templates = [
                (f"Dynamic high-impact opening macro shot of {clean_title}, dramatic {style} lighting, shallow depth of field", "slow_push_in", hook, "DISCOVER", "hook"),
                (f"Close-up detailed demonstration of {clean_title} in action, cinematic volumetric lighting, 8k {style}", "tracking_pan_right", core, "IN ACTION", "demonstration"),
                (f"Vibrant lifestyle shot showing real-world beauty of {clean_title}, natural lens flare, {style} atmosphere", "slow_zoom_in", f"Every detail of {clean_title} engineered for perfection.", "PRECISION", "proof"),
                (f"Sleek cinematic closing shot highlighting {clean_title}, neon backlighting, dynamic reflections", "pull_back_reveal", cta, "LEARN MORE", "call_to_action"),
            ]

        # Fit into requested num_scenes
        for i in range(1, num_scenes + 1):
            idx = (i - 1) % len(templates)
            prompt_text, cam, narration, caption, purpose = templates[idx]
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
        # Handle OAuth2 tokens (AQ. / ya29.) vs standard AI Studio API keys (AIzaSy...)
        if self.api_key.startswith("AIzaSy"):
            headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
            url = f"{self.base_url}/{endpoint}?key={self.api_key}"
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            url = f"{self.base_url}/{endpoint}"
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

    def _call_gemini_api(self, prompt_text: str, is_json: bool = True) -> Optional[Any]:
        models = [
            "models/gemini-2.5-flash:generateContent",
            "models/gemini-1.5-flash:generateContent",
            "models/gemini-flash-latest:generateContent"
        ]
        for endpoint in models:
            headers, url = self._get_headers_and_url(endpoint)
            payload = {
                "contents": [{
                    "parts": [{"text": prompt_text}]
                }]
            }
            if is_json:
                payload["generationConfig"] = {"response_mime_type": "application/json"}
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return self._clean_json_response(raw_text) if is_json else raw_text
                    else:
                        logger.info(f"Gemini API {endpoint} returned status {resp.status_code}")
            except Exception as e:
                logger.debug(f"Gemini API {endpoint} connection attempt: {e}")
        return None

    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        sys_instruction = (
            f"You are an expert short-form viral scriptwriter for {platform}. "
            f"Return ONLY valid JSON with keys: 'title', 'platform', 'duration_seconds', 'hook', 'core_message', 'call_to_action'."
        )
        prompt_text = f"{sys_instruction}\nUser Prompt: {prompt}\nTarget Duration: {duration_seconds}s"
        result = self._call_gemini_api(prompt_text, is_json=True)
        if result and isinstance(result, dict) and "hook" in result:
            return result
        logger.info("Using deterministic script director fallback")
        return self._mock.generate_script(prompt, duration_seconds, platform)

    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        sys_instruction = (
            f"Generate a {num_scenes}-scene storyboard in {style} style for {script_data.get('platform', 'reels')}. "
            "Return ONLY a JSON array of objects with keys: 'scene_number', 'duration_seconds', 'purpose', 'visual_prompt', 'camera_movement', 'narration', 'caption', 'transition'."
        )
        prompt_text = f"{sys_instruction}\nScript Context: {json.dumps(script_data)}"
        result = self._call_gemini_api(prompt_text, is_json=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result
        logger.info("Using deterministic storyboard planner fallback")
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

