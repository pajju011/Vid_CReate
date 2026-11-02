@echo off
title ClipForge AI - Backend API (Port 8000)

cd /d "%~dp0backend"

if not exist "..\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .\venv
    pause
    exit /b 1
)

echo Starting ClipForge AI Backend on http://127.0.0.1:8000 ...
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause

