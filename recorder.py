import sounddevice as sd
import numpy as np
import wave
import threading
import subprocess
import sys
from pathlib import Path
from config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE, RECORDING_FILE, OUTPUT_DIR

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_data = []
        self.mic_stream = None
        self.system_audio_process = None
        self.system_audio_file = OUTPUT_DIR / "system_audio.wav"
        
    def start_recording(self, no_mic=False):
        """Start recording microphone and/or system audio"""
        if self.is_recording:
            print("Already recording!")
            return
            
        if no_mic:
            print("Starting system audio recording only...")
        else:
            print("Starting recording with microphone and system audio...")
            
        self.is_recording = True
        self.audio_data = []
        
        # Check system audio availability
        self._check_system_audio()
        
        # Start microphone recording (unless disabled)
        if not no_mic:
            self.mic_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,  # Mono for mic
                dtype=np.float32,
                callback=self._audio_callback
            )
            self.mic_stream.start()
        else:
            self.mic_stream = None
            print("Microphone recording disabled")
        
        # Start system audio recording (platform-specific)
        self._start_system_audio()
        
        print("Recording started. Press Ctrl+C to stop.")
        
    def _check_system_audio(self):
        """Check if system audio recording is available"""
        try:
            if sys.platform == "win32":
                # Windows: Check for WASAPI
                result = subprocess.run(["ffmpeg", "-f", "wasapi", "-list_devices", "true", "-i", "dummy"], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    print("Warning: System audio not available on Windows")
                    print("Make sure you have audio drivers installed and FFmpeg supports WASAPI")
            else:
                # Linux: Check for PulseAudio
                result = subprocess.run(["pactl", "list", "sources", "short"], 
                                     capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    print("Warning: PulseAudio not available")
                    print("Install PulseAudio: sudo apt install pulseaudio")
                else:
                    print("System audio check passed")
        except Exception as e:
            print(f"Warning: Could not check system audio: {e}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for microphone audio"""
        if self.is_recording:
            self.audio_data.append(indata.copy())
            
    def _start_system_audio(self):
        """Start system audio recording using platform-specific methods"""
        try:
            if sys.platform == "win32":
                # Windows: Use ffmpeg with wasapi
                cmd = [
                    "ffmpeg", "-f", "wasapi", "-i", "0",  # Default system audio device
                    "-ar", str(SAMPLE_RATE),
                    "-ac", "1",  # Mono
                    "-y", str(self.system_audio_file)
                ]
            else:
                # Linux: Use pulseaudio/pipewire with monitor source
                cmd = [
                    "ffmpeg", "-f", "pulse", "-i", "default.monitor",
                    "-ar", str(SAMPLE_RATE),
                    "-ac", "1",  # Mono
                    "-y", str(self.system_audio_file)
                ]
            
            # Skip the problematic test and try direct recording
            
            self.system_audio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to start
            import time
            time.sleep(0.5)
            
            # Check if process is still running
            if self.system_audio_process.poll() is not None:
                stderr_output = self.system_audio_process.stderr.read().decode()
                print(f"Warning: System audio recording failed: {stderr_output}")
                print("Continuing with microphone only...")
                self.system_audio_process = None
                
        except Exception as e:
            print(f"Warning: Could not start system audio recording: {e}")
            print("Continuing with microphone only...")
            
    def stop_recording(self):
        """Stop recording and save audio"""
        if not self.is_recording:
            print("Not currently recording!")
            return
            
        print("Stopping recording...")
        self.is_recording = False
        
        # Stop microphone recording
        if self.mic_stream:
            self.mic_stream.stop()
            self.mic_stream.close()
            
        # Stop system audio recording
        if self.system_audio_process:
            self.system_audio_process.terminate()
            self.system_audio_process.wait()
            
        # Handle audio saving based on what was recorded
        if self.audio_data and self.system_audio_file.exists():
            # Both mic and system audio - combine them
            mic_audio = np.concatenate(self.audio_data, axis=0)
            self._save_audio(mic_audio, RECORDING_FILE)
            print(f"Microphone audio saved to {RECORDING_FILE}")
            self._combine_audio()
            print(f"Combined audio saved to {RECORDING_FILE}")
        elif self.audio_data:
            # Only microphone audio
            mic_audio = np.concatenate(self.audio_data, axis=0)
            self._save_audio(mic_audio, RECORDING_FILE)
            print(f"Microphone audio saved to {RECORDING_FILE}")
        elif self.system_audio_file.exists():
            # Only system audio - convert to final format
            self._save_system_audio_only()
            print(f"System audio saved to {RECORDING_FILE}")
        else:
            print("No audio was recorded!")
            
        print("Recording stopped.")
        
    def _save_system_audio_only(self):
        """Save system audio only (no microphone) with proper format conversion"""
        try:
            import librosa
            
            # Load system audio and convert to mono, 16kHz
            system_audio, sr = librosa.load(str(self.system_audio_file), sr=SAMPLE_RATE, mono=True)
            
            # Save as final recording
            self._save_audio(system_audio, RECORDING_FILE)
            
            # Clean up system audio file
            self.system_audio_file.unlink()
            
        except Exception as e:
            print(f"Warning: Could not process system audio: {e}")
            # Fallback: just copy the system audio file
            import shutil
            shutil.copy2(self.system_audio_file, RECORDING_FILE)
            self.system_audio_file.unlink()
        
    def _save_audio(self, audio_data, filename):
        """Save audio data to WAV file"""
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(str(filename), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_int16.tobytes())
            
    def _combine_audio(self):
        """Combine microphone and system audio"""
        try:
            # Load mic audio
            mic_audio = self._load_audio(RECORDING_FILE)
            
            # Load system audio
            system_audio = self._load_audio(self.system_audio_file)
            
            # Simple mixing
            combined_audio = (mic_audio + system_audio) / 2
            
            # Save combined audio
            self._save_audio(combined_audio, RECORDING_FILE)
            
            # Clean up system audio file
            self.system_audio_file.unlink()
            
        except Exception as e:
            print(f"Warning: Could not combine audio: {e}")
            print("Using microphone audio only.")
            
    def _load_audio(self, filename):
        """Load audio from WAV file"""
        with wave.open(str(filename), 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            return audio.astype(np.float32) / 32767.0
