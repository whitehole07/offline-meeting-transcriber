import json
import sys
import warnings
import logging
from pathlib import Path
import numpy as np
import librosa
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from config import RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_MODEL, HF_TOKEN, SAMPLE_RATE
from config import WHISPER_MODEL_PATH
from config import DIARIZATION_MODEL_PATH

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
        
    def _load_whisper_model(self):
        """Load whisper model"""
        if self.whisper_model is None:
            try:
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
        
        # Perform diarization
        logger.info("Starting speaker diarization...")
        diarization_result = self._diarize_audio()
        
        # Combine transcription and diarization
        if diarization_result:
            combined_result = self._combine_transcription_diarization(transcription, transcription_segments, diarization_result)
            
            # Save JSON format
            # with open(DIARIZED_FILE, 'w', encoding='utf-8') as f:
            #     json.dump(combined_result, f, indent=2, ensure_ascii=False)
            # print(f"Diarized transcription (JSON format) saved to {DIARIZED_FILE}")
            
            # Save text format
            txt_file = DIARIZED_FILE.with_suffix('.txt')
            self._save_diarization_txt(combined_result, txt_file)
            logger.info(f"Diarized transcription (text format) saved to {txt_file}")
        else:
            logger.warning("Diarization failed - skipping speaker identification")
            
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
                best_of=5,
                word_timestamps=True
            )
            
            # Convert to list of segments with one word each
            transcription_segments, transcription_parts = [], []
            for segment in segments:
                if hasattr(segment, "words"):  # ensure word-level info exists
                    for word_info in segment.words:
                        transcription_segments.append({
                            "start": word_info.start,
                            "end": word_info.end,
                            "text": word_info.word.strip()
                        })
                else:
                    # fallback to segment-level if no word info
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
            
    def _diarize_audio(self):
        """Perform speaker diarization using pyannote.audio and merge consecutive segments of the same speaker"""
        try:
            # Initialize diarization pipeline
            if not hasattr(self, 'diarization_pipeline') or self.diarization_pipeline is None:
                logger.info("Loading diarization model...")
                self.diarization_pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL_PATH)

            # Perform diarization
            logger.info("Performing speaker diarization...")
            diarization = self.diarization_pipeline(str(RECORDING_FILE))

            # Convert to list of merged segments
            merged_segments = []
            prev_segment = None

            for turn, speaker in diarization.speaker_diarization:
                if prev_segment and prev_segment['speaker'] == speaker:
                    # extend the previous segment
                    prev_segment['end'] = float(turn.end)
                else:
                    # start a new segment
                    prev_segment = {
                        "start": float(turn.start),
                        "end": float(turn.end),
                        "speaker": speaker
                    }
                    merged_segments.append(prev_segment)

            return merged_segments

        except Exception as e:
            logger.error(f"Diarization error: {e}")
            return None
        
    def _combine_transcription_diarization(self, transcription, transcription_segments, diarization_segments):
        """Combine transcription with diarization results"""
        try:
            # Align transcription segments with diarization segments
            aligned_segments = []
            
            for diarization_seg in diarization_segments:
                start_time = diarization_seg["start"]
                end_time = diarization_seg["end"]
                speaker = diarization_seg["speaker"]
                
                # Find transcription segments that overlap with this diarization segment
                overlapping_text = []
                for trans_seg in transcription_segments:
                    trans_start = trans_seg.get("start", 0)
                    trans_end = trans_seg.get("end", 0)
                    trans_text = trans_seg.get("text", "").strip()
                    
                    # Check for overlap
                    if (trans_start < end_time and trans_end > start_time and trans_text):
                        overlapping_text.append(trans_text)
                
                # Combine overlapping text
                combined_text = " ".join(overlapping_text).strip()
                
                if combined_text:  # Only add segments with text
                    aligned_segments.append({
                        "start": start_time,
                        "end": end_time,
                        "speaker": speaker,
                        "text": combined_text
                    })
            
            result = {
                "transcription": transcription,
                "segments": aligned_segments,
                "speakers": list(set(seg["speaker"] for seg in aligned_segments))
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Could not align transcription with diarization: {e}")
            # Fallback: return diarization segments without text alignment
            return {
                "transcription": transcription,
                "segments": diarization_segments,
                "speakers": list(set(seg["speaker"] for seg in diarization_segments))
            }
    
    def _save_diarization_txt(self, combined_result, txt_file):
        """Save diarization in text format: {SPEAKER} {time start}-{time end}: {transcription}"""
        try:
            with open(txt_file, 'w', encoding='utf-8') as f:
                segments = combined_result.get("segments", [])
                
                for segment in segments:
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
