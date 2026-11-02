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
│   ├── Candidate Clips Inspector (Viral score breakdown, start/end boundary trimmer)
│   ├── 9:16 Vertical Video Player (Real-time playback, download MP4, fullscreen)
│   └── Provider & Engine Manager (Cloud API keys & local engine diagnostics)
│
├── Backend (FastAPI + SQLAlchemy + Pydantic v2)
│   ├── REST API (/api/projects, /api/uploads, /api/generation, /api/videos, /api/clips, /api/jobs)
│   ├── Multi-Provider Adapters (Google Gemini, OpenAI, Luma Dream Machine, ElevenLabs, Whisper)
│   ├── Local Deterministic Engine (Offline FFmpeg synthesis & local mock planner)
│   └── Multi-Threaded Background Queue / Celery + Redis
│
├── Video Processing Engine (FFmpeg & OpenCV)
│   ├── Smart Vertical Cropping (Face & subject detection with temporal smoothing)
│   ├── Blurred Background Padding ([bg_src]boxblur + [fg_src]overlay)
│   ├── Timed Subtitle Burning (ASS & SRT with Bold Yellow, Clean Minimal, Creator Box presets)
│   └── Audio Engine (Voiceover synthesis, background music ducking, AAC encoding)
│
└── Technical Quality Control (FFprobe validation, aspect ratio, duration, audio stream checks)
```

---

## Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.10+ (tested on Python 3.11, 3.12, 3.14)
- **Node.js**: v18+ (tested on Node v24)
- **FFmpeg & FFprobe**: Installed and available on system PATH

---

## Installation & Setup

### 1. Clone & Set Up Backend

```powershell
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
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

Copy the example environment configuration:

```powershell
cp .env.example .env
```

---

## Running the Application

### 1. Start the Backend API Server

```powershell
# Activate virtual environment if not already active
.\venv\Scripts\activate

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the Frontend Development Studio

In a separate terminal:

```powershell
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## Running Automated Tests

Run the full backend and video processing test suite:

```powershell
# Run all tests with verbose output
.\venv\Scripts\python.exe -m pytest -v
```

All 11 automated test cases verify:
- FFprobe metadata extraction & stream inspection (`test_ffprobe.py`)
- Multi-factor hook & duration clip ranking (`test_clip_ranking.py`)
- ASS and SRT timed subtitle formatting (`test_subtitles.py`)
- Technical QC aspect ratio and duration verification (`test_qc.py`)
- Full End-to-End Video-to-Shorts processing (`test_e2e_pipeline.py`)
- Full End-to-End Prompt-to-Video generation pipeline (`test_prompt_to_video.py`)

---

## How to Test the Workflows

### Testing Workflow A: Prompt to Video

1. Open the UI at `http://localhost:5173`.
2. Click **Create New Video** &rarr; select **Workflow A: Prompt to Video**.
3. Choose one of the preset prompts or type your own:
   - Example: *"Create a 30-second cinematic Instagram Reel about an AI fitness tracker with high energy visuals and call to action."*
4. Click **Generate Storyboard First** to view and customize scene durations, prompts, and narration.
5. Click **Generate & Render Full Video**.
6. The live job progress modal will display real stages (*Planning* &rarr; *Generating Assets* &rarr; *Assembling* &rarr; *Quality Checking* &rarr; *Completed*).
7. View the final vertical 9:16 MP4 in the video player and click **Download Final MP4**.

### Testing Workflow B: Video to Shorts / Reels

1. Open the UI and select **Workflow B: Video to Shorts**.
2. Drag and drop any landscape video (MP4, MOV, or WebM).
3. The video metadata (resolution, duration, codecs) is displayed.
4. Select target clip length (e.g., 30s) and crop mode (*Smart Crop*, *Center Crop*, or *Blurred Background*).
5. Click **Analyze Speech & Find Viral Clips**.
6. View the scored candidate clips with opening hooks and duration breakdowns.
7. Adjust the start/end trimmer sliders if desired.
8. Click **Render 9:16 Short**.
9. Preview and download the individual rendered short MP4 with burned subtitles!

---

## Configuring Cloud AI Providers

ClipForge AI operates seamlessly offline using deterministic local synthesis. When cloud API keys are added to `.env`, ClipForge automatically transitions to cloud providers:

| Provider Type | Supported Cloud Adapters | Environment Variables |
|---|---|---|
| **LLM Planner** | Google Gemini 1.5 Flash, OpenAI GPT-4o | `LLM_PROVIDER=gemini`<br>`LLM_API_KEY=your_key` |
| **Video Generation** | Luma Dream Machine, Runway Gen-2 | `VIDEO_PROVIDER=luma`<br>`VIDEO_API_KEY=your_key` |
| **Audio Voiceover** | ElevenLabs Multilingual v2, OpenAI TTS-1 | `AUDIO_PROVIDER=elevenlabs`<br>`AUDIO_API_KEY=your_key` |
| **Speech-to-Text** | OpenAI Whisper-1 | `TRANSCRIPTION_PROVIDER=whisper`<br>`TRANSCRIPTION_API_KEY=your_key` |

---

## Known Limitations & Production Notes

1. **Local Mode Audio Tone**: In offline demo mode, synthetic audio tracks use deterministic tones so that video generation and audio mixing can be tested completely without external network dependencies.
2. **Video Provider Rate Limits**: When using cloud video generation APIs (such as Luma or Runway), generation jobs are processed asynchronously; progress polling respects provider rate limits.
3. **Database**: By default, SQLite is used for zero-latency local development. For production horizontal scaling, set `DATABASE_URL=postgresql://...` and run Celery workers via Docker Compose.
