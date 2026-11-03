import httpx
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseAudioProvider
from app.utils.sample_media import create_sample_audio_track
from app.utils.network import is_network_available

class EdgeTTSAudioProvider(BaseAudioProvider):
    """
    Real Neural AI Voiceover synthesizer powered by Microsoft Edge Neural TTS.
    100% Free, zero API key required, crystal-clear studio human voices.
    """
    VOICE_MAP = {
        "energetic_male": "en-US-ChristopherNeural",
        "deep_male": "en-US-GuyNeural",
        "warm_female": "en-US-JennyNeural",
        "professional_female": "en-US-AriaNeural",
        "tech_host": "en-US-BrianNeural"
    }

    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        if is_network_available():
            voice_id = self.VOICE_MAP.get(voice, "en-US-ChristopherNeural")
            temp_mp3 = output_path.with_suffix(".mp3")
            try:
                import edge_tts
                import asyncio

                async def _run_tts():
                    communicate = edge_tts.Communicate(text, voice_id)
                    await communicate.save(str(temp_mp3))

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(asyncio.wait_for(_run_tts(), timeout=8.0))
                loop.close()

                if temp_mp3.exists() and temp_mp3.stat().st_size > 500:
                    if output_path.suffix.lower() == ".wav":
                        from app.utils.ffmpeg import run_ffmpeg
                        args = ["-y", "-i", str(temp_mp3), "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", str(output_path)]
                        run_ffmpeg(args)
                        temp_mp3.unlink(missing_ok=True)
                    else:
                        if temp_mp3 != output_path:
                            import shutil
                            shutil.move(str(temp_mp3), str(output_path))
                    logger.info(f"Edge-TTS synthesized real neural voiceover successfully ({output_path})")
                    return True
            except Exception as e:
                logger.warning(f"Edge-TTS network error ({e}), using local fallback")

        words = len(text.split())
        duration = max(2.0, round(words / 2.3, 1))
        return create_sample_audio_track(output_path, duration=duration, track_type="narration")

    def generate_music(self, mood: str, duration_seconds: float, output_path: Path) -> bool:
        return create_sample_audio_track(output_path, duration=duration_seconds, track_type="music")

class MockAudioProvider(BaseAudioProvider):
    """Local audio generator that uses Edge-TTS for real voice and ambient music."""
    def __init__(self):
        self._edge = EdgeTTSAudioProvider()

    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        return self._edge.generate_voiceover(text, voice, output_path)

    def generate_music(self, mood: str, duration_seconds: float, output_path: Path) -> bool:
        return create_sample_audio_track(output_path, duration=duration_seconds, track_type="music")

class ElevenLabsAudioProvider(BaseAudioProvider):
    """Real ElevenLabs Text-to-Speech provider adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        voice_id = "pNInz6obpgDQGcFmaJgB" if "male" in voice.lower() else "21m00Tcm4TlvDq8ikWAM"
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                output_path.write_bytes(resp.content)
                return True
            else:
                logger.error(f"ElevenLabs TTS error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"ElevenLabs error: {resp.status_code} - {resp.text}")

    def generate_music(self, mood: str, duration_seconds: float, output_path: Path) -> bool:
        return MockAudioProvider().generate_music(mood, duration_seconds, output_path)

class OpenAIAudioProvider(BaseAudioProvider):
    """Real OpenAI TTS adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        voice_name = "onyx" if "male" in voice.lower() else "nova"
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_name
        }
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                output_path.write_bytes(resp.content)
                return True
            else:
                raise RuntimeError(f"OpenAI TTS error: {resp.status_code} - {resp.text}")

    def generate_music(self, mood: str, duration_seconds: float, output_path: Path) -> bool:
        return MockAudioProvider().generate_music(mood, duration_seconds, output_path)
