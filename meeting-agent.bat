@echo off
REM Meeting Agent - Windows Batch Script
REM This script allows you to run the meeting agent from anywhere

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Change to the meeting agent directory
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please make sure you're running this from the meeting-agent directory.
    echo Expected location: %SCRIPT_DIR%
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in virtual environment!
    echo Please make sure the virtual environment is properly set up.
    pause
    exit /b 1
)

REM Run the meeting agent
echo Starting Meeting Agent...
echo Press Ctrl+C to stop recording and process audio
echo.
python cli.py start

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Meeting Agent encountered an error.
    pause
)
