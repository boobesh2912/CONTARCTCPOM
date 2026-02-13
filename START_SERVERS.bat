@echo off
echo ========================================
echo  MediGuardian - Flask + React Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [1/4] Starting Backend (Flask API)...
cd backend
start cmd /k "python api.py"
cd ..

echo [2/4] Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul

echo [3/4] Starting Frontend (React)...
cd frontend
start cmd /k "npm run dev"
cd ..

echo [4/4] Done!
echo.
echo ========================================
echo  MediGuardian is starting!
echo ========================================
echo.
echo Backend API:  http://localhost:5000
echo Frontend App: http://localhost:3000
echo.
echo Two terminal windows have opened:
echo  - Window 1: Flask API (backend)
echo  - Window 2: React Dev Server (frontend)
echo.
echo Press Ctrl+C in each window to stop the servers
echo.
pause
