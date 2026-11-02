@echo off
title ClipForge AI - Frontend (Port 5173)

cd /d "%~dp0frontend"

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 'npm' was not found in your system PATH.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

echo Starting ClipForge AI Frontend on http://localhost:5173 ...
call npm run dev
pause

