#!/bin/bash

# Offline Meeting Transcriber - Installation Script
# This script sets up the complete environment for the meeting transcriber

set -e  # Exit on any error

echo "🎙️  Offline Meeting Transcriber - Installation Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

print_success "Python $PYTHON_VERSION found"

# Check if pip is installed
print_status "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3."
    exit 1
fi

print_success "pip3 found"

# Check if git is installed
print_status "Checking git installation..."
if ! command -v git &> /dev/null; then
    print_error "git is not installed. Please install git."
    exit 1
fi

print_success "git found"

# Check if git lfs is installed
print_status "Checking git lfs installation..."
if ! command -v git-lfs &> /dev/null; then
    print_error "git lfs is not installed. Please install git lfs."
    print_error "Linux: sudo apt install git-lfs (Ubuntu/Debian) or sudo yum install git-lfs (RHEL/CentOS)"
    print_error "Mac: brew install git-lfs"
    print_error "Windows: Download from https://git-lfs.github.io"
    exit 1
fi

print_success "git lfs found"

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip
print_success "pip upgraded"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create models directory
print_status "Creating models directory..."
mkdir -p models
print_success "Models directory created"

# Download Whisper model
print_status "Downloading Whisper model (this may take a while)..."
WHISPER_MODEL="medium"
WHISPER_MODEL_PATH="models/faster-whisper-${WHISPER_MODEL}"

if [ -d "$WHISPER_MODEL_PATH" ]; then
    print_warning "Whisper model already exists. Skipping download."
else
    # Download using git clone
    git clone https://huggingface.co/Systran/faster-whisper-${WHISPER_MODEL} ${WHISPER_MODEL_PATH}
    print_success "Whisper model downloaded"
fi

# Download SpeechBrain speaker diarization model
print_status "Downloading SpeechBrain speaker diarization model..."
DIARIZATION_MODEL_PATH="models/spkrec-ecapa-voxceleb"

if [ -d "$DIARIZATION_MODEL_PATH" ]; then
    print_warning "Speaker diarization model already exists. Skipping download."
else
    # Download using git clone
    git clone https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb ${DIARIZATION_MODEL_PATH}
    print_success "Speaker diarization model downloaded"
fi

# Create output directory
print_status "Creating output directory..."
mkdir -p output
print_success "Output directory created"

# Test installation
print_status "Testing installation..."
python3 -c "
try:
    from src.recorder import AudioRecorder
    from src.transcriber import MeetingTranscriber
    from src.speaker_diarizer import SpeakerDiarizer
    print('✅ All modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"
print_success "Installation test passed"

# Make CLI executable
chmod +x cli.py

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start recording: python cli.py start"
echo "3. Press Ctrl+C to stop recording and process audio"
echo ""
echo "📁 Files created:"
echo "  - venv/ (virtual environment)"
echo "  - models/faster-whisper-medium/ (Whisper model)"
echo "  - models/spkrec-ecapa-voxceleb/ (Speaker diarization model)"
echo "  - output/ (output directory)"
echo ""
echo "🔧 Configuration:"
echo "  Edit config.py to customize settings like language, model size, etc."
echo ""
print_success "Ready to transcribe meetings offline!"
