import sys
import time
import wave
import numpy as np
import sounddevice as sd
import librosa
from config import CHUNK_SIZE, RECORDING_FILE

# Platform-specific imports
# Windows: Use pyaudiowpatch for WASAPI loopback support
# Linux: Use sounddevice for PulseAudio/PipeWire support
if sys.platform == "win32":
    try:
        import pyaudiowpatch as pyaudio
    except ImportError:
        print("Warning: pyaudiowpatch not found. Install it for better Windows audio support:")
        print("  pip install pyaudiowpatch")
        pyaudio = None
else:
    pyaudio = None  # Not used on Linux

class AudioRecorder:
    """Cross-platform audio recorder for meetings with system and microphone audio capture."""
    
    def __init__(self):
        # Platform-specific audio backend
        self.pa = pyaudio.PyAudio() if sys.platform == "win32" and pyaudio else None
        
        # Recording state
        self.is_recording = False
        self.sys_audio_data = []
        self.mic_audio_data = []
        self.sys_stream = None
        self.mic_stream = None
        
        # Sample rates (default values)
        self.sys_sample_rate = 48000  # System audio sample rate
        self.mic_sample_rate = 16000  # Microphone sample rate
        
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
                # Linux: Check for available input devices (Speaker/default/pipewire)
                devices = sd.query_devices()
                found_device = False
                for dev in devices:
                    name_lower = dev['name'].lower()
                    if dev['max_input_channels'] > 0 and ('speaker' in name_lower or 'default' in name_lower or 'pipewire' in name_lower):
                        found_device = True
                        print(f"Found system audio device: {dev['name']}")
                        break
                if not found_device:
                    print("Warning: No suitable audio input device found")
                    print("Make sure PulseAudio/PipeWire is running")
        except Exception as e:
            print(f"Warning: Could not check system audio: {e}")
    
    def _sys_audio_callback_pyaudio(self, indata, frame_count, time_info, status):
        """Callback for system audio (PyAudio on Windows)"""
        if self.is_recording:
            # PyAudio returns bytes, convert to numpy array
            if isinstance(indata, bytes):
                audio_array = np.frombuffer(indata, dtype=np.int16)
                self.sys_audio_data.append(audio_array)
            else:
                self.sys_audio_data.append(indata.copy())
        return (indata, pyaudio.paContinue)
    
    def _sys_audio_callback_sd(self, indata, frames, time, status):
        """Callback for system audio (sounddevice on Linux)"""
        if status:
            print(f"System audio status: {status}")
        if self.is_recording:
            # sounddevice returns numpy array directly
            self.sys_audio_data.append(indata.copy())
    
    def _mic_audio_callback_pyaudio(self, indata, frame_count, time_info, status):
        """Callback for microphone audio (PyAudio on Windows)"""
        if self.is_recording:
            # PyAudio returns bytes, convert to numpy array
            if isinstance(indata, bytes):
                audio_array = np.frombuffer(indata, dtype=np.int16)
                self.mic_audio_data.append(audio_array)
            else:
                self.mic_audio_data.append(indata.copy())
        return (indata, pyaudio.paContinue)
    
    def _mic_audio_callback_sd(self, indata, frames, time, status):
        """Callback for microphone audio (sounddevice on Linux)"""
        if status:
            print(f"Microphone audio status: {status}")
        if self.is_recording:
            # sounddevice returns numpy array directly
            self.mic_audio_data.append(indata.copy())
            
    def _start_system_audio(self):
        """Start system audio recording using cross-platform methods"""
        try:
            if sys.platform == "win32":
                # Windows: Use PyAudio with WASAPI loopback
                lb = self.pa.get_default_wasapi_loopback()
                self.sys_sample_rate = int(lb["defaultSampleRate"])  # Store sample rate
                channels = max(1, int(lb["maxInputChannels"]))
                input_index = lb["index"]
                
                print(f"System audio: {self.sys_sample_rate} Hz, {channels} channel(s)")
                
                self.sys_stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=self.sys_sample_rate,
                    input=True,
                    input_device_index=input_index,
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self._sys_audio_callback_pyaudio
                )
                self.sys_stream.start_stream()
            else:
                # Linux: Use sounddevice with speaker device for loopback
                # Note: Direct monitor devices aren't visible through ALSA API
                # We'll use the Speaker device which PipeWire can loop back
                devices = sd.query_devices()
                system_device = None
                system_index = None
                
                # Try to find Speaker device (which has input channels via PipeWire loopback)
                for idx, dev in enumerate(devices):
                    name_lower = dev['name'].lower()
                    if dev['max_input_channels'] > 0 and 'speaker' in name_lower:
                        system_device = dev
                        system_index = idx
                        print(f"Using system audio device: {dev['name']}")
                        break
                
                # Fallback to default or pipewire device
                if not system_device:
                    for idx, dev in enumerate(devices):
                        name_lower = dev['name'].lower()
                        if dev['max_input_channels'] > 0 and ('default' in name_lower or 'pipewire' in name_lower):
                            system_device = dev
                            system_index = idx
                            print(f"Using system audio device: {dev['name']}")
                            break
                
                if not system_device:
                    raise RuntimeError("No suitable audio device found for system audio recording")
                
                # Start sounddevice input stream
                channels = min(2, system_device['max_input_channels'])
                
                print(f"System audio: {self.sys_sample_rate} Hz, {channels} channel(s)")
                
                self.sys_stream = sd.InputStream(
                    device=system_index,
                    channels=channels,
                    samplerate=self.sys_sample_rate,
                    dtype=np.int16,
                    callback=self._sys_audio_callback_sd,
                    blocksize=CHUNK_SIZE
                )
                self.sys_stream.start()
                
            # Give it a moment to start
            time.sleep(0.5)
                
        except Exception as e:
            print(f"Warning: Could not start system audio recording: {e}")

    def _start_mic_audio(self):
        """Start mic audio recording using cross-platform methods"""
        try:
            if sys.platform == "win32":
                # Windows: Use PyAudio
                dev = self.pa.get_default_input_device_info()
                self.mic_sample_rate = int(dev["defaultSampleRate"])  # Store sample rate
                channels = max(1, int(dev["maxInputChannels"]))
                
                print(f"Microphone: {self.mic_sample_rate} Hz, {channels} channel(s)")
                
                self.mic_stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=self.mic_sample_rate,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self._mic_audio_callback_pyaudio
                )
                self.mic_stream.start_stream()
            else:
                # Linux: Use sounddevice
                print(f"Microphone: {self.mic_sample_rate} Hz, 1 channel")
                
                self.mic_stream = sd.InputStream(
                    channels=1,  # Mono for mic
                    samplerate=self.mic_sample_rate,
                    dtype=np.int16,
                    callback=self._mic_audio_callback_sd,
                    blocksize=CHUNK_SIZE
                )
                self.mic_stream.start()

            # Give it a moment to start
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
            if sys.platform == "win32":
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            else:
                self.mic_stream.stop()
                self.mic_stream.close()
            
        # Stop system audio recording
        if self.sys_stream:
            if sys.platform == "win32":
                self.sys_stream.stop_stream()
                self.sys_stream.close()
            else:
                self.sys_stream.stop()
                self.sys_stream.close()

        # Give any last callback a moment to finish pushing frames
        time.sleep(0.05)
            
        # Handle audio saving based on what was recorded
        try:
            if self.mic_audio_data and self.sys_audio_data:
                # Both mic and system audio - combine them
                print("Processing microphone and system audio...")
                self._combine_audio()
                print(f"Combined audio saved to {RECORDING_FILE}")
                print(f"  Sample rate: {self.sys_sample_rate} Hz (system audio rate)")
            elif self.mic_audio_data:
                # Only microphone audio
                print("Processing microphone audio...")
                mic_audio = np.concatenate(self.mic_audio_data, axis=0)
                self._save_audio_int16(mic_audio, RECORDING_FILE, self.mic_sample_rate)
                print(f"Microphone audio saved to {RECORDING_FILE}")
                print(f"  Sample rate: {self.mic_sample_rate} Hz")
            elif self.sys_audio_data:
                # Only system audio
                print("Processing system audio...")
                sys_audio = np.concatenate(self.sys_audio_data, axis=0)
                self._save_audio_int16(sys_audio, RECORDING_FILE, self.sys_sample_rate)
                print(f"System audio saved to {RECORDING_FILE}")
                print(f"  Sample rate: {self.sys_sample_rate} Hz")
            else:
                print("No audio was recorded!")
        except Exception as e:
            print(f"Error saving audio: {e}")
            
        print("Recording stopped.")
        
    def _save_audio_int16(self, audio_data, filename, sample_rate=48000):
        """Save audio data (already in int16 format) to WAV file"""
        
        # Flatten if multi-channel (convert to mono)
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1).astype(np.int16)
        
        with wave.open(str(filename), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
            
    def _combine_audio(self):
        """Combine microphone and system audio"""
        try:
            # Concatenate all mic and system audio chunks
            mic_audio = np.concatenate(self.mic_audio_data, axis=0)
            sys_audio = np.concatenate(self.sys_audio_data, axis=0)
            
            # Flatten to mono if multi-channel
            if len(mic_audio.shape) > 1:
                mic_audio = mic_audio.mean(axis=1).astype(np.int16)
            if len(sys_audio.shape) > 1:
                sys_audio = sys_audio.mean(axis=1).astype(np.int16)
            
            # Resample to match sample rates if needed
            if self.mic_sample_rate != self.sys_sample_rate:
                # Resample mic to match system audio
                mic_audio_float = mic_audio.astype(np.float32) / 32768.0
                mic_audio = librosa.resample(
                    mic_audio_float, 
                    orig_sr=self.mic_sample_rate, 
                    target_sr=self.sys_sample_rate
                )
                mic_audio = (mic_audio * 32767).astype(np.int16)
            
            # Make sure both arrays are the same length (pad shorter one with zeros)
            max_len = max(len(mic_audio), len(sys_audio))
            if len(mic_audio) < max_len:
                mic_audio = np.pad(mic_audio, (0, max_len - len(mic_audio)))
            if len(sys_audio) < max_len:
                sys_audio = np.pad(sys_audio, (0, max_len - len(sys_audio)))
            
            # Simple mixing - convert to float for mixing, then back to int16
            mic_float = mic_audio.astype(np.float32)
            sys_float = sys_audio.astype(np.float32)
            combined = ((mic_float + sys_float) / 2).astype(np.int16)
            
            # Save combined audio at system audio sample rate
            self._save_audio_int16(combined, RECORDING_FILE, self.sys_sample_rate)
            
        except Exception as e:
            print(f"Warning: Could not combine audio: {e}")
            # Fallback: save audios separately
            if self.mic_audio_data:
                mic_audio = np.concatenate(self.mic_audio_data, axis=0)
                self._save_audio_int16(mic_audio, str(RECORDING_FILE).replace(".wav", "_mic.wav"), self.mic_sample_rate)
            if self.sys_audio_data:
                sys_audio = np.concatenate(self.sys_audio_data, axis=0)
                self._save_audio_int16(sys_audio, str(RECORDING_FILE).replace(".wav", "_sys.wav"), self.sys_sample_rate)