import sounddevice as sd
import pyaudiowpatch as pyaudio
import numpy as np
import wave
import sys
from config import CHUNK_SIZE, RECORDING_FILE, OUTPUT_DIR

class AudioRecorder:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.is_recording = False
        self.sys_audio_data = []
        self.mic_audio_data = []
        self.sys_stream = None
        self.mic_stream = None

        # maybe deprecated
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
        self.sys_audio_data, self.mic_audio_data = [], []
        
        # Check system audio availability
        self._check_system_audio()
        
        # Start microphone recording (unless disabled)
        if not no_mic:
            self._start_mic_audio()
        else:
            self.mic_stream = None
            print("Microphone recording disabled")
        
        # Start system audio recording
        self._start_system_audio()
        
        print("Recording started. Press Ctrl+C to stop.")
        
    def _check_system_audio(self):
        """Check if system audio recording is available"""
        try:
            if sys.platform == "win32":
                # Windows: Check for WASAPI loopbacks
                with pyaudio.PyAudio() as pa:
                    try:
                        pa.get_default_wasapi_loopback()
                    except Exception as e:
                        print("Warning: System audio loopback not available on Windows")
                        print("Make sure you have audio drivers installed and WASAPI-enabled Windows version")
            else:
                # Linux: Check for PulseAudio
                raise RuntimeError("Linux compatibility not yet available")
        except Exception as e:
            print(f"Warning: Could not check system audio: {e}")
    
    def _sys_audio_callback(self, indata, frames, time, status):
        """Callback for system audio"""
        if self.is_recording:
            self.sys_audio_data.append(indata.copy())
    
    def _mic_audio_callback(self, indata, frames, time, status):
        """Callback for microphone audio"""
        if self.is_recording:
            self.mic_audio_data.append(indata.copy())
            
    def _start_system_audio(self):
        """Start system audio recording using cross-platform methods"""
        try:
            if sys.platform == "win32":
                lb = self.pa.get_default_wasapi_loopback()
                rate = int(lb["defaultSampleRate"])
                channels = max(1, int(lb["maxInputChannels"]))
                
                self.sys_stream = self.pa.open(
                    format=pyaudio.paInt16, 
                    channels=channels, 
                    rate=rate,
                    input=True,
                    input_device_index=lb["index"],
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self.sys_audio_callback
                )

                self.sys_stream.start_stream()

                # Give it a moment to start
                import time
                time.sleep(0.5)
            else:
                raise RuntimeError("Linux compatibility not yet available")
                
        except Exception as e:
            print(f"Warning: Could not start system audio recording: {e}")

    def _start_mic_audio(self):
        """Start mic audio recording using cross-platform methods"""
        try:
            # Use the default input device's native settings
            dev = self.pa.get_default_input_device_info()
            rate = int(dev["defaultSampleRate"])
            # Prefer mono if available; fall back to 2 if needed
            channels = max(1, int(dev["maxInputChannels"]))
            
            # Start stream
            self.mic_stram = self.pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.mic_audio_callback
            )

            self.mic_stream.start_stream()

            # Give it a moment to start
            import time
            time.sleep(0.5)
                
        except Exception as e:
            print(f"Warning: Could not start mic audio recording: {e}")
            
    def stop_recording(self):
        """Stop recording and save audio"""
        if not self.is_recording:
            print("Not currently recording!")
            return
            
        print("Stopping recording...")
        self.is_recording = False
        
        # Stop microphone recording
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            
        # Stop system audio recording
        if self.sys_stream:
            self.sys_stream.stop_stream()
            self.sys_stream.close()

        # giv eany last callback a moment to finish pushing frames
        import time
        time.sleep(0.05)
            
        # Handle audio saving based on what was recorded
        self._combine_audio()

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
            
    def _load_audio(self, filename):
        """Load audio from WAV file"""
        with wave.open(str(filename), 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            return audio.astype(np.float32) / 32767.0
