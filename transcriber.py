import json
import sys
import warnings
import logging
from pathlib import Path
import numpy as np
import librosa
# Heavy modules will be imported lazily when needed
from config import (
    RECORDING_FILE, 
    TRANSCRIPTION_FILE, 
    DIARIZED_FILE, 
    WHISPER_MODEL, 
    WHISPER_LANGUAGE, 
    WHISPER_MODEL, 
    SAMPLE_RATE,
    WHISPER_MODEL_PATH,
    DIARIZATION_MODEL_PATH
)
from speaker_diarizer import SpeakerDiarizer

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
# warnings.filterwarnings("ignore", category=UserWarning, module="speechbrain")
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")

# Set up logging
logger = logging.getLogger(__name__)

class MeetingTranscriber:
    def __init__(self):
        self.whisper_model = None
        self.diarization_pipeline = None
        self.speaker_diarizer = None
        
    def _load_whisper_model(self):
        """Load whisper model (lazy import)"""
        if self.whisper_model is None:
            try:
                # Import faster-whisper only when needed
                from faster_whisper import WhisperModel
                
                logger.info(f"Loading Whisper model ({WHISPER_MODEL})...")
                self.whisper_model = WhisperModel(WHISPER_MODEL_PATH, local_files_only=True, device="cpu", compute_type="int8")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                return False
        return True
        
    def transcribe_and_diarize(self):
        """Transcribe audio and perform speaker diarization"""
        if not RECORDING_FILE.exists():
            logger.error(f"Recording file {RECORDING_FILE} not found!")
            return False
            
        logger.info("Starting transcription...")
        
        # Load whisper model
        if not self._load_whisper_model():
            return False
            
        # Transcribe with faster-whisper
        transcription, transcription_segments = self._transcribe_audio()
        if not transcription:
            return False
            
        # Save transcription
        with open(TRANSCRIPTION_FILE, 'w', encoding='utf-8') as f:
            f.write(transcription)
        logger.info(f"Transcription saved to {TRANSCRIPTION_FILE}")
        
        # Perform diarization using our new SpeakerDiarizer with transcription segments
        logger.info("Starting speaker diarization...")
        diarization_result = self._diarize_audio(transcription_segments)
        
        # Save diarization results
        if diarization_result:
            # Save text format
            txt_file = DIARIZED_FILE.with_suffix('.txt')
            self._save_diarization_txt(diarization_result, txt_file)
            logger.info(f"Diarized transcription (text format) saved to {txt_file}")
        else:
            logger.warning("Diarization failed - saving plain transcription")
            with open(TRANSCRIPTION_FILE, 'w', encoding='utf-8') as f:
                f.write(transcription)
            logger.info(f"Transcription saved to {TRANSCRIPTION_FILE}")
            
        return True
        
    def _transcribe_audio(self):
        """Transcribe audio using faster-whisper"""
        try:
            # Load audio
            audio, sr = librosa.load(str(RECORDING_FILE), sr=SAMPLE_RATE)
            
            # Transcribe with timestamps
            segments, info = self.whisper_model.transcribe(
                audio,
                language=WHISPER_LANGUAGE,
                task="transcribe",
                beam_size=5,
                best_of=5
            )
            
            # Convert to list of segments (segment-level, not word-level)
            transcription_segments, transcription_parts = [], []
            for segment in segments:
                transcription_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                transcription_parts.append(segment.text.strip())
                
            return " ".join(transcription_parts), transcription_segments
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
            
    def _diarize_audio(self, transcription_segments):
        """Perform speaker diarization using our new SpeakerDiarizer with provided transcription segments"""
        try:
            # Initialize SpeakerDiarizer
            if self.speaker_diarizer is None:
                logger.info("Loading speaker diarization model...")
                self.speaker_diarizer = SpeakerDiarizer(DIARIZATION_MODEL_PATH, DIARIZATION_MODEL_PATH, gap_tolerance=2.0)

            # Perform diarization using transcription segments
            logger.info("Performing speaker diarization...")
            segments = self.speaker_diarizer.diarize(str(RECORDING_FILE), transcription_segments)
            
            if not segments:
                logger.warning("No segments found by diarizer")
                return None

            # Convert to the format expected by the rest of the code
            merged_segments = []
            for segment in segments:
                merged_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "speaker": segment["speaker"],
                    "text": segment.get("text", "")
                })

            logger.info(f"Found {len(merged_segments)} diarized segments")
            return merged_segments

        except Exception as e:
            logger.error(f"Diarization error: {e}")
            return None
        
    
    def _save_diarization_txt(self, diarization_segments, txt_file):
        """Save diarization in text format: {SPEAKER} {time start}-{time end}: {transcription}"""
        try:
            with open(txt_file, 'w', encoding='utf-8') as f:
                for segment in diarization_segments:
                    speaker = segment.get("speaker", "UNKNOWN")
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    
                    # Format time as MM:SS or HH:MM:SS
                    start_formatted = self._format_time(start_time)
                    end_formatted = self._format_time(end_time)
                    
                    # Write in the requested format
                    f.write(f"{speaker} ({start_formatted}-{end_formatted}): {text}\n\n")
            
        except Exception as e:
            logger.error(f"Error saving diarization text file: {e}")
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
