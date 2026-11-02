@echo off
setlocal enabledelayedexpansion

title ClipForge AI - Automated Video Production Agent

echo ====================================================================
echo.
echo           ClipForge AI - Video Production Agent Launcher
echo.
echo ====================================================================
echo.

cd /d "%~dp0"

:: 1. Verify Python Virtual Environment
if not exist "%~dp0venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found at .\venv
    echo Please make sure the venv directory exists and Python is installed.
    echo.
    pause
    exit /b 1
)

:: 2. Verify Node / npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 'npm' was not found in your system PATH.
    echo Please install Node.js (https://nodejs.org/) to run the frontend.
    echo.
    pause
    exit /b 1
)

:: 3. Ensure External Storage Directories on D: Drive
if exist "D:\" (
    if not exist "D:\AI_Video_Storage" (
        echo [INFO] Creating external media storage directory: D:\AI_Video_Storage
        mkdir "D:\AI_Video_Storage" 2>nul
    )
    if not exist "D:\AI_Video_Temp" (
        echo [INFO] Creating external temporary directory: D:\AI_Video_Temp
        mkdir "D:\AI_Video_Temp" 2>nul
    )
) else (
    echo [WARNING] D: drive not detected. Fallback storage in %%TEMP%% will be used.
)

:: 4. Check frontend dependencies
if not exist "%~dp0frontend\node_modules" (
    echo [INFO] Installing frontend dependencies (one-time setup)...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

echo.
echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "ClipForge AI - Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Starting Vite Frontend on http://localhost:5173 ...
start "ClipForge AI - Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo ====================================================================
echo ClipForge AI is running!
echo.
echo   - Web UI:           http://localhost:5173
echo   - Backend API Docs: http://127.0.0.1:8000/docs
echo   - Storage Location: D:\AI_Video_Storage
echo   - Temp Processing:  D:\AI_Video_Temp
echo.
echo Close the individual terminal windows to stop the servers.
echo ====================================================================
echo.
pause

