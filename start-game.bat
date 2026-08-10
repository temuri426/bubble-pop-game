@echo off
title Bubble Pop Game Launcher
echo Starting Bubble Pop Game...
echo.

REM Change to the game directory
cd /d "C:\Users\temuri\bubble-pop-game"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Starting HTTP server on http://localhost:8080
echo.

REM Start Python HTTP server in background
start "BubblePopServer" /min python -m http.server 8080

REM Wait a moment for server to start
timeout /t 2 /nobreak >nul

REM Open the game in default browser
start "" "http://localhost:8080"

echo.
echo Game opened in your browser!
echo.
echo To stop the server, close the "BubblePopServer" window
echo or press Ctrl+C in that window.
echo.
pause