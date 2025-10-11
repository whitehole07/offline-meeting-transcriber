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
SAMPLE_RATE = 16000
CHANNELS = 2  # Stereo for mic + system audio
CHUNK_SIZE = 1024
RECORDING_FORMAT = "wav"

# Whisper settings
WHISPER_MODEL = "medium"  # base, small, medium, large
WHISPER_LANGUAGE = "it"

# Diarization settings
DIARIZATION_MIN_SPEAKERS = 1
DIARIZATION_MAX_SPEAKERS = 10

# Hugging Face token for accessing gated models
HF_TOKEN = os.getenv("HF_TOKEN")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
