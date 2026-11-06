from typing import Dict, Any
from app.core.config import settings
from app.core.privacy import privacy_gateway
from app.providers.base import (
    BaseLLMProvider, BaseVideoProvider, BaseAudioProvider, BaseTranscriptionProvider
)
from app.providers.llm.llm_providers import MockLLMProvider, GeminiLLMProvider, OllamaLLMProvider
from app.providers.video.video_providers import (
    MockVideoProvider, PollinationsVideoProvider, LumaVideoProvider, RunwayVideoProvider,
    KlingVideoProvider, PikaVideoProvider, GoogleVeoVideoProvider, SeedanceVideoProvider,
    AdobeFireflyVideoProvider
)
from app.providers.video.omni_provider import OmniForgeVideoProvider
from app.providers.video.gemini_omni_provider import GeminiOmniVideoProvider
from app.providers.audio.audio_providers import (
    MockAudioProvider, EdgeTTSAudioProvider, ElevenLabsAudioProvider, OpenAIAudioProvider
)
from app.providers.transcription.transcription_providers import MockTranscriptionProvider, WhisperAPITranscriptionProvider

class ProviderRegistry:
    @staticmethod
    def get_llm_provider() -> BaseLLMProvider:
        # Check Strict Local policy
        if privacy_gateway.privacy_mode == "strict_local":
            if settings.LLM_PROVIDER == "ollama":
                return OllamaLLMProvider()
            return MockLLMProvider()

        # Check cloud transfer authorization
        if (settings.LLM_PROVIDER == "gemini" or not settings.LLM_PROVIDER) and settings.LLM_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("gemini", "llm_script", "Generate script & storyboard")
            if allowed:
                return GeminiLLMProvider(api_key=settings.LLM_API_KEY)

        if settings.LLM_PROVIDER == "ollama":
            return OllamaLLMProvider()

        return MockLLMProvider()

    @staticmethod
    def get_video_provider() -> BaseVideoProvider:
        # Check Strict Local policy
        if privacy_gateway.privacy_mode == "strict_local":
            return OmniForgeVideoProvider()

        provider_name = (settings.VIDEO_PROVIDER or "omni").lower()

        if provider_name in ("gemini_omni", "gemini_video"):
            key = settings.VIDEO_API_KEY or settings.LLM_API_KEY
            if key:
                allowed, _ = privacy_gateway.can_transfer_to_cloud("gemini", "video_generation", "Gemini Omni generation")
                if allowed:
                    return GeminiOmniVideoProvider(api_key=key)

        if provider_name == "veo" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("veo", "video_generation", "Google Veo 2 generation")
            if allowed:
                return GoogleVeoVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "luma" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("luma", "video_generation", "Luma Dream Machine generation")
            if allowed:
                return LumaVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "runway" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("runway", "video_generation", "Runway Gen-3 generation")
            if allowed:
                return RunwayVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "kling" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("kling", "video_generation", "Kling AI generation")
            if allowed:
                return KlingVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "seedance" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("seedance", "video_generation", "Seedance AI generation")
            if allowed:
                return SeedanceVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "firefly" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("firefly", "video_generation", "Adobe Firefly Video generation")
            if allowed:
                return AdobeFireflyVideoProvider(api_key=settings.VIDEO_API_KEY)
        elif provider_name == "pika" and settings.VIDEO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("pika", "video_generation", "Pika AI generation")
            if allowed:
                return PikaVideoProvider(api_key=settings.VIDEO_API_KEY)

        # Default to the master all-in-one OmniForge Engine
        return OmniForgeVideoProvider()

    @staticmethod
    def get_audio_provider() -> BaseAudioProvider:
        if privacy_gateway.privacy_mode == "strict_local":
            return EdgeTTSAudioProvider()

        if settings.AUDIO_PROVIDER == "elevenlabs" and settings.AUDIO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("elevenlabs", "tts_voiceover", "ElevenLabs speech synthesis")
            if allowed:
                return ElevenLabsAudioProvider(api_key=settings.AUDIO_API_KEY)
        elif settings.AUDIO_PROVIDER == "openai" and settings.AUDIO_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("openai", "tts_voiceover", "OpenAI TTS synthesis")
            if allowed:
                return OpenAIAudioProvider(api_key=settings.AUDIO_API_KEY)
        elif settings.AUDIO_PROVIDER in ("edge_tts", "free_tts"):
            return EdgeTTSAudioProvider()

        return MockAudioProvider()

    @staticmethod
    def get_transcription_provider() -> BaseTranscriptionProvider:
        if privacy_gateway.privacy_mode == "strict_local":
            return MockTranscriptionProvider()

        if settings.TRANSCRIPTION_PROVIDER == "whisper" and settings.TRANSCRIPTION_API_KEY:
            allowed, _ = privacy_gateway.can_transfer_to_cloud("whisper", "audio_transcription", "Whisper speech transcription")
            if allowed:
                return WhisperAPITranscriptionProvider(api_key=settings.TRANSCRIPTION_API_KEY)

        return MockTranscriptionProvider()

    @staticmethod
    def get_status() -> Dict[str, Any]:
        return {
            "demo_mode": settings.DEMO_MODE,
            "privacy": privacy_gateway.get_status(),
            "llm": {
                "configured_provider": settings.LLM_PROVIDER,
                "is_active": settings.LLM_PROVIDER in ("mock", "ollama") or bool(settings.LLM_API_KEY),
                "is_real_api": bool(settings.LLM_API_KEY) or settings.LLM_PROVIDER == "ollama",
                "model_info": (
                    "Google Gemini 1.5 Flash (Free Key Configured)" if settings.LLM_API_KEY
                    else "Local Ollama LLM (Offline)" if settings.LLM_PROVIDER == "ollama"
                    else "ClipForge Deterministic AI Director"
                )
            },
            "video": {
                "configured_provider": settings.VIDEO_PROVIDER,
                "is_active": True,
                "is_real_api": bool(settings.VIDEO_API_KEY) or settings.VIDEO_PROVIDER in ("omni", "pollinations", "mock", None),
                "model_info": (
                    "Google Veo 2 API" if settings.VIDEO_PROVIDER == "veo" and settings.VIDEO_API_KEY
                    else "Luma Dream Machine API" if settings.VIDEO_PROVIDER == "luma" and settings.VIDEO_API_KEY
                    else "Runway Gen-3 API" if settings.VIDEO_PROVIDER == "runway" and settings.VIDEO_API_KEY
                    else "Kling AI 1.5 API" if settings.VIDEO_PROVIDER == "kling" and settings.VIDEO_API_KEY
                    else "ByteDance Seedance API" if settings.VIDEO_PROVIDER == "seedance" and settings.VIDEO_API_KEY
                    else "Adobe Firefly Video API" if settings.VIDEO_PROVIDER == "firefly" and settings.VIDEO_API_KEY
                    else "OmniForge Master Video Engine (Multi-Tier Flux.1 + Camera Physics + Premier Cloud)"
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
