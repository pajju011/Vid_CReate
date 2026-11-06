# ClipForge AI — Video Automation Studio

> **AI-powered Prompt-to-Video and Long-Video-to-Shorts production agent built for Instagram Reels and YouTube Shorts.**

ClipForge AI is an end-to-end automated video production platform featuring two flagship workflows:
1. **Workflow A: Prompt-to-Video**: Natural language prompt &rarr; structured script & storyboard &rarr; AI asset generation &rarr; FFmpeg assembly & audio mixing &rarr; QC &rarr; 9:16 / 16:9 MP4 export.
2. **Workflow B: Video-to-Shorts / Reels**: Upload long video &rarr; FFprobe validation &rarr; speech transcription & word timestamps &rarr; scene change detection & candidate clip scoring &rarr; smart vertical cropping (subject/face tracking, center crop, or blurred background) &rarr; animated subtitle burning &rarr; export.

---

## Architecture Overview

```
ClipForge AI Architecture
├── Frontend (React + Vite + TypeScript + Tailwind CSS)
│   ├── Create Studio (Segmented Prompt-to-Video and Video-to-Shorts modes)
│   ├── Interactive Storyboard Editor (Scene re-ordering, duration & prompt adjustments)
│   ├── Real-Time WebSocket Streaming & Checkpoint Controls (Pause, Resume, Cancel)
│   ├── Candidate Clips Inspector (Viral score breakdown, start/end boundary trimmer)
│   ├── 9:16 Vertical Video Player (HTTP 206 Byte-Range streaming & MP4 download)
│   └── Privacy Gateway & Storage Settings (Strict Local, Private Hybrid, Cloud Assisted)
│
├── Backend (FastAPI + SQLAlchemy + Pydantic v2 + WebSockets)
│   ├── REST API & WebSocket (/api/projects, /api/generation, /api/ws/jobs/{id}, /api/privacy, /api/storage)
│   ├── Privacy-Aware Model Router (Strict Local, Private Hybrid, Cloud Assisted with transfer audit logging)
│   ├── Multi-Provider Adapters (Google Veo 2, Runway Gen-3, Luma Dream Machine, Kling AI, ByteDance Seedance, Adobe Firefly, Ollama, Edge-TTS, ElevenLabs, Whisper)
│   ├── Consistency Engine (Character visual anchor locking, lighting continuity & camera motion planning)
│   ├── Checkpoint Recovery Engine (Scene-by-scene checkpointing, graceful pause & resume without rework)
│   └── Multi-Threaded Queue with Concurrency Throttling & Exponential Backoff Retries
│
├── Video Processing Engine (FFmpeg & OpenCV)
│   ├── Image-to-Video Ken Burns Motion Engine (Dynamic subpixel pan & zoom interpolation)
│   ├── Smart Vertical Cropping (Face & subject detection with temporal smoothing)
│   ├── Blurred Background Padding ([bg_src]boxblur + [fg_src]overlay)
│   ├── Timed Subtitle Burning (ASS & SRT with Bold Yellow, Clean Minimal, Creator Box presets)
│   └── Audio Engine (Voiceover synthesis, sidechain dynamic audio ducking, AAC encoding)
│
├── External Local Storage System
│   ├── Master Storage: D:/AI_Video_Storage (renders, uploads, drafts, thumbnails, cache)
│   ├── Temporary Workspace: D:/AI_Video_Temp (processing chunks with automatic job cleanup)
│   └── Strict Media Isolation: Zero generated video or media files stored inside repository/codebase
│
└── Technical Quality Control (FFprobe validation, aspect ratio, duration, audio stream checks, auto-regeneration)
```

---

## Quick Start (Single Launcher)

On Windows, simply run the included batch file:

```cmd
run.bat
```

This single command will:
1. Verify Python virtual environment and Node.js.
2. Ensure external storage directories (`D:\AI_Video_Storage` and `D:\AI_Video_Temp`).
3. Launch the FastAPI backend on `http://127.0.0.1:8000`.
4. Launch the Vite frontend on `http://localhost:5173`.
5. Open your default web browser automatically.

---

## Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.10+ (tested on Python 3.11, 3.12, 3.14)
- **Node.js**: v18+ (tested on Node v20, v24)
- **FFmpeg & FFprobe**: Installed and available on system PATH

---

## Installation & Manual Setup

### 1. Set Up Backend

```powershell
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 2. Set Up Frontend

```powershell
cd frontend
npm install
cd ..
```

### 3. Configure Environment Variables

```powershell
cp .env.example .env
```

---

## Running Automated Tests

Run the full backend, video processing, privacy gateway, and external storage test suite:

```powershell
$env:PYTHONPATH='backend'; .\venv\Scripts\python.exe -m pytest -v
```

All 19 automated test cases verify:
- FFprobe metadata extraction & stream inspection (`test_ffprobe.py`)
- Multi-factor hook & duration clip ranking (`test_clip_ranking.py`)
- ASS and SRT timed subtitle formatting (`test_subtitles.py`)
- Technical QC aspect ratio and duration verification (`test_qc.py`)
- Full End-to-End Video-to-Shorts processing (`test_e2e_pipeline.py`)
- Full End-to-End Prompt-to-Video generation pipeline (`test_prompt_to_video.py`)
- External storage isolation & zero media in workspace (`test_external_storage.py`)
- Privacy gateway tiers & model router audit logging (`test_privacy_and_checkpoint.py`)
- Scene-by-scene checkpoint recovery and pause/resume (`test_privacy_and_checkpoint.py`)

---

## Privacy-Aware Model Router

ClipForge AI includes a strict 3-tier privacy governance engine:

| Privacy Tier | Behavior | Permitted Providers |
|---|---|---|
| **Strict Local** | 100% offline. Zero external API calls. Everything generated locally. | Ollama (Local LLM), Edge-TTS, Local FFmpeg / OpenCV |
| **Private Hybrid** | Default. Metadata & files stay local; only vetted requests go to approved cloud APIs. | Vetted allowlist with approval & audit logging |
| **Cloud Assisted** | Multi-provider cloud models enabled with full concurrency. | Google Veo 2, Runway Gen-3, Luma Dream Machine, Kling AI, Seedance, Adobe Firefly, ElevenLabs, Whisper |

Every transfer attempt is vetted through the centralized `PrivacyGateway` and committed to the `transfer_audit_logs` database table. A global **Cloud Transfer Kill Switch** allows instant locking of all network transfers with one click.

---

## External Media Storage Isolation

Generated media, audio tracks, and temporary processing chunks are stored **strictly outside the project codebase**:

- **Permanent Media Storage**: `D:/AI_Video_Storage` (`renders/`, `uploads/`, `drafts/`, `thumbnails/`, `cache/`)
- **Temporary Processing Workspace**: `D:/AI_Video_Temp` (`processing/`, `chunks/`)
- Temporary files are automatically cleaned up after job completion or failure.
- Final MP4 exports remain permanently in external storage until deleted by the user.
