import httpx
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseAudioProvider
from app.utils.sample_media import create_sample_audio_track

class MockAudioProvider(BaseAudioProvider):
    """Local deterministic audio generator for voiceover and background music."""
    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        words = len(text.split())
        duration = max(2.0, round(words / 2.3, 1))
        return create_sample_audio_track(output_path, duration=duration, track_type="narration")

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
