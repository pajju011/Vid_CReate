import json
import httpx
from pathlib import Path
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseTranscriptionProvider

class MockTranscriptionProvider(BaseTranscriptionProvider):
    """
    Deterministic speech-to-text transcriber with word and segment timestamps.
    Used for local testing, demo mode, and offline operation.
    """
    def transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        segments = [
            {
                "start": 0.0,
                "end": 4.5,
                "text": "Have you ever wondered what the future of AI video creation really looks like?",
                "words": [
                    {"word": "Have", "start": 0.0, "end": 0.3},
                    {"word": "you", "start": 0.3, "end": 0.5},
                    {"word": "ever", "start": 0.5, "end": 0.8},
                    {"word": "wondered", "start": 0.8, "end": 1.3},
                    {"word": "what", "start": 1.4, "end": 1.6},
                    {"word": "the", "start": 1.6, "end": 1.8},
                    {"word": "future", "start": 1.8, "end": 2.2},
                    {"word": "of", "start": 2.2, "end": 2.4},
                    {"word": "AI", "start": 2.4, "end": 2.8},
                    {"word": "video", "start": 2.8, "end": 3.2},
                    {"word": "creation", "start": 3.2, "end": 3.7},
                    {"word": "really", "start": 3.7, "end": 4.0},
                    {"word": "looks", "start": 4.0, "end": 4.3},
                    {"word": "like?", "start": 4.3, "end": 4.5}
                ]
            },
            {
                "start": 5.0,
                "end": 9.2,
                "text": "Most creators spend hours trimming clips and fixing subtitles manually.",
                "words": [
                    {"word": "Most", "start": 5.0, "end": 5.3},
                    {"word": "creators", "start": 5.3, "end": 5.8},
                    {"word": "spend", "start": 5.8, "end": 6.1},
                    {"word": "hours", "start": 6.1, "end": 6.5},
                    {"word": "trimming", "start": 6.5, "end": 7.0},
                    {"word": "clips", "start": 7.0, "end": 7.4},
                    {"word": "and", "start": 7.4, "end": 7.6},
                    {"word": "fixing", "start": 7.6, "end": 8.0},
                    {"word": "subtitles", "start": 8.0, "end": 8.6},
                    {"word": "manually.", "start": 8.6, "end": 9.2}
                ]
            },
            {
                "start": 9.8,
                "end": 14.5,
                "text": "With automated agents, full viral videos can now be produced in seconds.",
                "words": [
                    {"word": "With", "start": 9.8, "end": 10.1},
                    {"word": "automated", "start": 10.1, "end": 10.7},
                    {"word": "agents,", "start": 10.7, "end": 11.2},
                    {"word": "full", "start": 11.2, "end": 11.5},
                    {"word": "viral", "start": 11.5, "end": 11.9},
                    {"word": "videos", "start": 11.9, "end": 12.4},
                    {"word": "can", "start": 12.4, "end": 12.6},
                    {"word": "now", "start": 12.6, "end": 12.9},
                    {"word": "be", "start": 12.9, "end": 13.1},
                    {"word": "produced", "start": 13.1, "end": 13.7},
                    {"word": "in", "start": 13.7, "end": 13.9},
                    {"word": "seconds.", "start": 13.9, "end": 14.5}
                ]
            }
        ]
        full_text = " ".join(s["text"] for s in segments)
        return {
            "text": full_text,
            "language": "en",
            "segments": segments
        }

class WhisperAPITranscriptionProvider(BaseTranscriptionProvider):
    """Real OpenAI Whisper API adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        with httpx.Client(timeout=120.0) as client:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_path.name, f, "audio/wav")}
                data = {
                    "model": "whisper-1",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": ["word", "segment"]
                }
                resp = client.post(url, headers=headers, data=data, files=files)
                if resp.status_code != 200:
                    logger.error(f"Whisper API error ({resp.status_code}): {resp.text}")
                    raise RuntimeError(f"Whisper API error: {resp.status_code} - {resp.text}")
                res = resp.json()

        formatted_segments = []
        for s in res.get("segments", []):
            formatted_segments.append({
                "start": float(s.get("start", 0.0)),
                "end": float(s.get("end", 0.0)),
                "text": s.get("text", "").strip(),
                "words": s.get("words", [])
            })

        return {
            "text": res.get("text", ""),
            "language": res.get("language", "en"),
            "segments": formatted_segments
        }
