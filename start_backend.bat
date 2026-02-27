@echo off
REM Sentient-Grid Backend Launcher
REM Runs the streaming backend in the background on Windows

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to the workspace directory
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Parse command-line arguments (pass them through to the backend)
set ARGS=%*

REM Start the backend in a new window with logging
echo Starting Sentient-Grid Backend...
echo Log file: sentient_grid_backend.log
echo.

REM Run with output redirected to log file
python stream_backend.py %ARGS% >> sentient_grid_backend.log 2>&1

REM Alternative: Run in a separate window (uncomment below to use instead)
REM start "Sentient-Grid Backend" python stream_backend.py %ARGS%

echo Backend started. Check sentient_grid_backend.log for output.
