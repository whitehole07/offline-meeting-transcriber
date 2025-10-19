@echo off
REM Offline Meeting Transcriber - Windows Installation Script
REM This script sets up the complete environment for the meeting transcriber

echo 🎙️  Offline Meeting Transcriber - Installation Script
echo ==================================================
echo.

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if pip is installed
echo [INFO] Checking pip installation...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip.
    pause
    exit /b 1
)

echo [SUCCESS] pip found

REM Check if git is installed
echo [INFO] Checking git installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git is not installed. Please install git from https://git-scm.com
    pause
    exit /b 1
)

echo [SUCCESS] git found

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)
echo [SUCCESS] pip upgraded

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed

REM Create models directory
echo [INFO] Creating models directory...
if not exist "models" mkdir models
echo [SUCCESS] Models directory created

REM Download Whisper model
echo [INFO] Downloading Whisper model (this may take a while)...
set WHISPER_MODEL=medium
set WHISPER_MODEL_PATH=models\faster-whisper-%WHISPER_MODEL%

if exist "%WHISPER_MODEL_PATH%" (
    echo [WARNING] Whisper model already exists. Skipping download.
) else (
    REM Download using git clone
    git clone https://huggingface.co/Systran/faster-whisper-%WHISPER_MODEL% %WHISPER_MODEL_PATH%
    
    if errorlevel 1 (
        echo [ERROR] Failed to download Whisper model.
        pause
        exit /b 1
    )
    echo [SUCCESS] Whisper model downloaded
)

REM Download SpeechBrain speaker diarization model
echo [INFO] Downloading SpeechBrain speaker diarization model...
set DIARIZATION_MODEL_PATH=models\spkrec-ecapa-voxceleb

if exist "%DIARIZATION_MODEL_PATH%" (
    echo [WARNING] Speaker diarization model already exists. Skipping download.
) else (
    REM Download using git clone
    git clone https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb %DIARIZATION_MODEL_PATH%
    
    if errorlevel 1 (
        echo [ERROR] Failed to download speaker diarization model.
        pause
        exit /b 1
    )
    echo [SUCCESS] Speaker diarization model downloaded
)

REM Create output directory
echo [INFO] Creating output directory...
if not exist "output" mkdir output
echo [SUCCESS] Output directory created

REM Test installation
echo [INFO] Testing installation...
python -c "try: from src.recorder import AudioRecorder; from src.transcriber import MeetingTranscriber; from src.speaker_diarizer import SpeakerDiarizer; print('✅ All modules imported successfully'); except ImportError as e: print(f'❌ Import error: {e}'); exit(1)"
if errorlevel 1 (
    echo [ERROR] Installation test failed.
    pause
    exit /b 1
)
echo [SUCCESS] Installation test passed

echo.
echo 🎉 Installation completed successfully!
echo.
echo 📋 Next steps:
echo 1. Double-click meeting-agent.bat to start recording
echo 2. Or run: python cli.py start
echo 3. Press Ctrl+C to stop recording and process audio
echo.
echo 📁 Files created:
echo   - venv\ (virtual environment)
echo   - models\faster-whisper-medium\ (Whisper model)
echo   - models\spkrec-ecapa-voxceleb\ (Speaker diarization model)
echo   - output\ (output directory)
echo.
echo 🔧 Configuration:
echo   Edit config.py to customize settings like language, model size, etc.
echo.
echo [SUCCESS] Ready to transcribe meetings offline!
echo.
pause
