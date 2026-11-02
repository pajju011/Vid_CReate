from typing import Dict, Any
from app.core.config import settings
from app.providers.base import (
    BaseLLMProvider, BaseVideoProvider, BaseAudioProvider, BaseTranscriptionProvider
)
from app.providers.llm.llm_providers import MockLLMProvider, GeminiLLMProvider
from app.providers.video.video_providers import (
    MockVideoProvider, LumaVideoProvider, RunwayVideoProvider, KlingVideoProvider, PikaVideoProvider
)
from app.providers.audio.audio_providers import MockAudioProvider, ElevenLabsAudioProvider, OpenAIAudioProvider
from app.providers.transcription.transcription_providers import MockTranscriptionProvider, WhisperAPITranscriptionProvider

class ProviderRegistry:
    @staticmethod
    def get_llm_provider() -> BaseLLMProvider:
        if settings.LLM_PROVIDER == "gemini" and settings.LLM_API_KEY:
            return GeminiLLMProvider(api_key=settings.LLM_API_KEY)
        return MockLLMProvider()

    @staticmethod
    def get_video_provider() -> BaseVideoProvider:
        if settings.VIDEO_PROVIDER == "luma" and settings.VIDEO_API_KEY:
            return LumaVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif settings.VIDEO_PROVIDER == "runway" and settings.VIDEO_API_KEY:
            return RunwayVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif settings.VIDEO_PROVIDER == "kling" and settings.VIDEO_API_KEY:
            return KlingVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif settings.VIDEO_PROVIDER == "pika" and settings.VIDEO_API_KEY:
            return PikaVideoProvider(api_key=settings.VIDEO_API_KEY)
        return MockVideoProvider()

    @staticmethod
    def get_audio_provider() -> BaseAudioProvider:
        if settings.AUDIO_PROVIDER == "elevenlabs" and settings.AUDIO_API_KEY:
            return ElevenLabsAudioProvider(api_key=settings.AUDIO_API_KEY)
        elif settings.AUDIO_PROVIDER == "openai" and settings.AUDIO_API_KEY:
            return OpenAIAudioProvider(api_key=settings.AUDIO_API_KEY)
        return MockAudioProvider()

    @staticmethod
    def get_transcription_provider() -> BaseTranscriptionProvider:
        if settings.TRANSCRIPTION_PROVIDER == "whisper" and settings.TRANSCRIPTION_API_KEY:
            return WhisperAPITranscriptionProvider(api_key=settings.TRANSCRIPTION_API_KEY)
        return MockTranscriptionProvider()

    @staticmethod
    def get_status() -> Dict[str, Any]:
        return {
            "demo_mode": settings.DEMO_MODE,
            "llm": {
                "configured_provider": settings.LLM_PROVIDER,
                "is_active": settings.LLM_PROVIDER == "mock" or bool(settings.LLM_API_KEY),
                "is_real_api": bool(settings.LLM_API_KEY),
                "model_info": "Google Gemini 1.5 Flash" if settings.LLM_PROVIDER == "gemini" and settings.LLM_API_KEY else "ClipForge Deterministic Planner (Demo)"
            },
            "video": {
                "configured_provider": settings.VIDEO_PROVIDER,
                "is_active": settings.VIDEO_PROVIDER == "mock" or bool(settings.VIDEO_API_KEY),
                "is_real_api": bool(settings.VIDEO_API_KEY),
                "model_info": "Luma Dream Machine API" if settings.VIDEO_PROVIDER == "luma" and settings.VIDEO_API_KEY else "ClipForge Local Synthesizer (Demo)"
            },
            "audio": {
                "configured_provider": settings.AUDIO_PROVIDER,
                "is_active": settings.AUDIO_PROVIDER == "mock" or bool(settings.AUDIO_API_KEY),
                "is_real_api": bool(settings.AUDIO_API_KEY),
                "model_info": "ElevenLabs / OpenAI TTS" if settings.AUDIO_API_KEY else "ClipForge Tone Audio Synthesizer (Demo)"
            },
            "transcription": {
                "configured_provider": settings.TRANSCRIPTION_PROVIDER,
                "is_active": settings.TRANSCRIPTION_PROVIDER == "mock" or bool(settings.TRANSCRIPTION_API_KEY),
                "is_real_api": bool(settings.TRANSCRIPTION_API_KEY),
                "model_info": "OpenAI Whisper-1 API" if settings.TRANSCRIPTION_API_KEY else "ClipForge Segment Transcriber (Demo)"
            }
        }

providers = ProviderRegistry()

