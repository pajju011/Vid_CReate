from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_script(self, prompt: str, duration_seconds: float, platform: str) -> Dict[str, Any]:
        """Generate structured script with hook, body, and CTA."""
        pass

    @abstractmethod
    def generate_storyboard(self, script_data: Dict[str, Any], num_scenes: int, style: str) -> List[Dict[str, Any]]:
        """Generate scene-by-scene storyboard."""
        pass

    @abstractmethod
    def analyze_transcript(self, transcript_text: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key highlights, viral hooks, and standalone topic moments."""
        pass

    @abstractmethod
    def rank_clips(self, candidate_clips: List[Dict[str, Any]], target_platform: str) -> List[Dict[str, Any]]:
        """Rank and score candidate short-form clips."""
        pass

class BaseVideoProvider(ABC):
    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit or synthesize a video generation."""
        pass

    @abstractmethod
    def generate_video_from_image(
        self,
        image_path: Path,
        prompt: str,
        duration_seconds: float,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """Animate a source character or product image into a motion video clip."""
        pass

    @abstractmethod
    def get_generation_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of remote generation job."""
        pass

    @abstractmethod
    def download_generated_video(self, video_url: str, destination_path: Path) -> bool:
        """Download remote generated video to local disk."""
        pass

    @abstractmethod
    def cancel_generation(self, job_id: str) -> bool:
        """Cancel ongoing generation job."""
        pass

class BaseImageProvider(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, aspect_ratio: str = "9:16", style: str = "cinematic") -> Dict[str, Any]:
        """Generate a still keyframe image for character anchoring or image-to-video."""
        pass

class BaseAudioProvider(ABC):
    @abstractmethod
    def generate_voiceover(self, text: str, voice: str, output_path: Path) -> bool:
        """Synthesize speech voiceover to audio file."""
        pass

    @abstractmethod
    def generate_music(self, mood: str, duration_seconds: float, output_path: Path) -> bool:
        """Synthesize or select licensed background music."""
        pass

class BaseTranscriptionProvider(ABC):
    @abstractmethod
    def transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribe audio file into structured segments with word timestamps."""
        pass
