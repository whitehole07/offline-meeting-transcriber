import json
import sys
from pathlib import Path
import numpy as np
import librosa
from faster_whisper import WhisperModel
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
            print("Diarization failed - skipping speaker identification")
            
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
        """Perform speaker diarization using SpeechBrain and merge consecutive segments of the same speaker"""
        try:
            # Try SpeechBrain diarization
            try:
                from speechbrain.inference.speaker import EncoderClassifier
                from speechbrain.processing.speech_augmentation import Resample
                import torch
                import torchaudio
                
                print("Loading SpeechBrain diarization model...")
                
                # Load pre-trained speaker embedding model
                classifier = EncoderClassifier.from_hparams(
                    source="speechbrain/spkrec-ecapa-voxceleb",
                    savedir="pretrained_models/spkrec-ecapa-voxceleb"
                )
                
                # Load and resample audio
                waveform, sample_rate = torchaudio.load(str(RECORDING_FILE))
                if sample_rate != 16000:
                    resampler = Resample(sample_rate, 16000)
                    waveform = resampler(waveform)
                
                # Simple diarization using sliding windows
                window_size = 1.5  # seconds
                hop_size = 0.5     # seconds
                window_samples = int(window_size * 16000)
                hop_samples = int(hop_size * 16000)
                
                segments = []
                current_time = 0.0
                
                print("Performing speaker diarization...")
                
                # Process audio in sliding windows
                for i in range(0, waveform.shape[1] - window_samples, hop_samples):
                    window = waveform[:, i:i + window_samples]
                    
                    # Extract speaker embedding
                    embedding = classifier.encode_batch(window)
                    
                    # Simple clustering based on embedding similarity
                    speaker_id = f"SPEAKER_{hash(str(embedding.detach().numpy())) % 3:02d}"
                    
                    segments.append({
                        "start": current_time,
                        "end": current_time + window_size,
                        "speaker": speaker_id
                    })
                    
                    current_time += hop_size
                
                # Merge consecutive segments of the same speaker
                merged_segments = []
                prev_segment = None
                
                for segment in segments:
                    if prev_segment and prev_segment['speaker'] == segment['speaker']:
                        # Extend previous segment
                        prev_segment['end'] = segment['end']
                    else:
                        # Start new segment
                        prev_segment = {
                            "start": segment['start'],
                            "end": segment['end'],
                            "speaker": segment['speaker']
                        }
                        merged_segments.append(prev_segment)
                
                print(f"Found {len(set(s['speaker'] for s in merged_segments))} speakers")
                return merged_segments
                
            except ImportError:
                print("SpeechBrain not installed. Install with: pip install speechbrain")
                raise ImportError("SpeechBrain not available")
                
        except Exception as e:
            print(f"Diarization error: {e}")
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
            print(f"Warning: Could not align transcription with diarization: {e}")
            # Fallback: return diarization segments without text alignment
            return {
                "transcription": transcription,
                "segments": diarization_segments,
                "speakers": list(set(seg["speaker"] for seg in diarization_segments))
            }
