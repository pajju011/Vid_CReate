from typing import Dict, Any
from app.core.config import settings
from app.providers.base import (
    BaseLLMProvider, BaseVideoProvider, BaseAudioProvider, BaseTranscriptionProvider
)
from app.providers.llm.llm_providers import MockLLMProvider, GeminiLLMProvider
from app.providers.video.video_providers import (
    MockVideoProvider, PollinationsVideoProvider, LumaVideoProvider, RunwayVideoProvider, KlingVideoProvider, PikaVideoProvider
)
from app.providers.audio.audio_providers import (
    MockAudioProvider, EdgeTTSAudioProvider, ElevenLabsAudioProvider, OpenAIAudioProvider
)
from app.providers.transcription.transcription_providers import MockTranscriptionProvider, WhisperAPITranscriptionProvider

class ProviderRegistry:
    @staticmethod
    def get_llm_provider() -> BaseLLMProvider:
        if (settings.LLM_PROVIDER == "gemini" or not settings.LLM_PROVIDER) and settings.LLM_API_KEY:
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
        elif settings.VIDEO_PROVIDER in ("pollinations", "free_ai"):
            return PollinationsVideoProvider()
        return MockVideoProvider()

    @staticmethod
    def get_audio_provider() -> BaseAudioProvider:
        if settings.AUDIO_PROVIDER == "elevenlabs" and settings.AUDIO_API_KEY:
            return ElevenLabsAudioProvider(api_key=settings.AUDIO_API_KEY)
        elif settings.AUDIO_PROVIDER == "openai" and settings.AUDIO_API_KEY:
            return OpenAIAudioProvider(api_key=settings.AUDIO_API_KEY)
        elif settings.AUDIO_PROVIDER in ("edge_tts", "free_tts"):
            return EdgeTTSAudioProvider()
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
                "model_info": "Google Gemini 1.5 Flash (Free Key Configured)" if settings.LLM_API_KEY else "ClipForge Deterministic AI Director"
            },
            "video": {
                "configured_provider": settings.VIDEO_PROVIDER,
                "is_active": True,
                "is_real_api": bool(settings.VIDEO_API_KEY) or settings.VIDEO_PROVIDER in ("pollinations", "mock"),
                "model_info": (
                    "Luma Dream Machine API" if settings.VIDEO_PROVIDER == "luma" and settings.VIDEO_API_KEY
                    else "Runway Gen-3 API" if settings.VIDEO_PROVIDER == "runway" and settings.VIDEO_API_KEY
                    else "Pollinations Flux.1 AI Visuals + Ken Burns Motion (Free)"
                )
            },
            "audio": {
                "configured_provider": settings.AUDIO_PROVIDER,
                "is_active": True,
                "is_real_api": bool(settings.AUDIO_API_KEY) or settings.AUDIO_PROVIDER in ("edge_tts", "mock"),
                "model_info": (
                    "ElevenLabs Studio TTS" if settings.AUDIO_API_KEY and settings.AUDIO_PROVIDER == "elevenlabs"
                    else "OpenAI TTS-1" if settings.AUDIO_API_KEY and settings.AUDIO_PROVIDER == "openai"
                    else "Microsoft Edge Neural Voice (Free Studio Quality TTS)"
                )
            },
            "transcription": {
                "configured_provider": settings.TRANSCRIPTION_PROVIDER,
                "is_active": True,
                "is_real_api": bool(settings.TRANSCRIPTION_API_KEY),
                "model_info": "OpenAI Whisper-1 API" if settings.TRANSCRIPTION_API_KEY else "ClipForge High-Precision Speech Transcriber"
            }
        }

providers = ProviderRegistry()

