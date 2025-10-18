import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output" / datetime.now().strftime("%Y%m%d")
RECORDING_FILE = OUTPUT_DIR / f"recording_{datetime.now().strftime('%H%M%S')}.wav"
TRANSCRIPTION_FILE = OUTPUT_DIR / f"transcription_{datetime.now().strftime('%H%M%S')}.txt"
DIARIZED_FILE = OUTPUT_DIR / f"diarized_{datetime.now().strftime('%H%M%S')}.json"

# Audio settings
SAMPLE_RATE = 16000  # Default sample rate for audio processing
CHUNK_SIZE = 1024    # Buffer size for audio streaming
RECORDING_FORMAT = "wav"

# Whisper transcription settings
WHISPER_MODEL = "medium"     # Options: base, small, medium, large
WHISPER_LANGUAGE = "it"      # Language code for transcription
WHISPER_MODEL_PATH = f"./models/faster-whisper-{WHISPER_MODEL}/"  # Local model path
DIARIZATION_MODEL_PATH = "./models/spkrec-ecapa-voxceleb/"  # Pyannote custom diarization model path

# Speaker diarization settings
DIARIZATION_MIN_SPEAKERS = 1
DIARIZATION_MAX_SPEAKERS = 10

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
