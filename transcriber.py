import json
import sys
from pathlib import Path
import numpy as np
import librosa
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from config import RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_MODEL, HF_TOKEN, SAMPLE_RATE
from config import WHISPER_MODEL_PATH
from config import DIARIZATION_MODEL_PATH

class MeetingTranscriber:
    def __init__(self):
        self.whisper_model = None
        self.diarization_pipeline = None
        
    def _load_whisper_model(self):
        """Load whisper model"""
        if self.whisper_model is None:
            try:
                print(f"Loading Whisper model ({WHISPER_MODEL})...")
                model_path = WHISPER_MODEL_PATH or r"./models/faster-whisper-medium/"
                self.whisper_model = WhisperModel(model_path, local_files_only=True, device="cpu", compute_type="int8")
                print("Whisper model loaded successfully")
            except Exception as e:
                print(f"Error loading Whisper model: {e}")
                return False
        return True
        
    def transcribe_and_diarize(self):
        """Transcribe audio and perform speaker diarization"""
        if not RECORDING_FILE.exists():
            print(f"Error: Recording file {RECORDING_FILE} not found!")
            return False
            
        print("Starting transcription...")
        
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
        print(f"Transcription saved to {TRANSCRIPTION_FILE}")
        
        # Perform diarization
        print("Starting speaker diarization...")
        diarization_result = self._diarize_audio()
        
        # Combine transcription and diarization
        if diarization_result:
            combined_result = self._combine_transcription_diarization(transcription, transcription_segments, diarization_result)
            with open(DIARIZED_FILE, 'w', encoding='utf-8') as f:
                json.dump(combined_result, f, indent=2, ensure_ascii=False)
            print(f"Diarized transcription saved to {DIARIZED_FILE}")
        else:
            # Fallback: simple segmentation
            simple_result = self._simple_segmentation(transcription)
            with open(DIARIZED_FILE, 'w', encoding='utf-8') as f:
                json.dump(simple_result, f, indent=2, ensure_ascii=False)
            print(f"Simple segmentation saved to {DIARIZED_FILE}")
            
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
            print(f"Transcription error: {e}")
            return None
            
    def _diarize_audio(self):
        """Perform speaker diarization using pyannote.audio and merge consecutive segments of the same speaker"""
        try:
            # Initialize diarization pipeline
            if not hasattr(self, 'diarization_pipeline') or self.diarization_pipeline is None:
                print("Loading diarization model...")
                model_path=DIARIZATION_MODEL_PATH or r"./models/models--pyannote--speaker-diarization-3.1/"
                self.diarization_pipeline = Pipeline.from_pretrained(model_path)

            # Perform diarization
            print("Performing speaker diarization...")
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
            print(f"Diarization error: {e}")
            print("Falling back to simple segmentation...")
            return None

            
    def _simple_segmentation(self, transcription):
        """Simple segmentation when diarization fails"""
        # Split transcription into sentences
        sentences = transcription.split('. ')
        
        # Create simple segments (assuming single speaker for now)
        segments = []
        current_time = 0.0
        time_per_sentence = 3.0  # Rough estimate: 3 seconds per sentence
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                segments.append({
                    "start": current_time,
                    "end": current_time + time_per_sentence,
                    "speaker": "Speaker_1",
                    "text": sentence.strip()
                })
                current_time += time_per_sentence
                
        return {
            "segments": segments,
            "transcription": transcription
        }
        
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
            print(f"Warning: Could not align transcription with diarization: {e}")
            # Fallback: return diarization segments without text alignment
            return {
                "transcription": transcription,
                "segments": diarization_segments,
                "speakers": list(set(seg["speaker"] for seg in diarization_segments))
            }
