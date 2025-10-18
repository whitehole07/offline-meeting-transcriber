import sys
import time
import wave
import logging
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
        logging.warning("pyaudiowpatch not found. Install it for better Windows audio support:")
        logging.warning("  pip install pyaudiowpatch")
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
        
        # Audio format tracking
        self.sys_sample_rate = 48000  # System audio sample rate
        self.mic_sample_rate = 16000  # Microphone sample rate
        self.sys_channels = 1          # System audio channels
        self.mic_channels = 1          # Microphone channels
        
        # Synchronization tracking
        self.start_time = None         # Recording start timestamp
        self.mic_start_time = None     # Mic stream start time
        self.sys_start_time = None     # Sys stream start time
        
    def start_recording(self, no_mic=False):
        """Start recording microphone and/or system audio"""
        if self.is_recording:
            logging.warning("Already recording!")
            return
            
        if no_mic:
            logging.info("Starting system audio recording only...")
        else:
            logging.info("Starting recording with microphone and system audio...")
            
        # Reset data BEFORE starting streams to ensure sync
        self.sys_audio_data, self.mic_audio_data = [], []
        
        # Check system audio availability
        self._check_system_audio()
        
        # IMPORTANT: Set recording flag BEFORE starting streams
        # This ensures callbacks start capturing immediately when streams begin
        self.is_recording = True
        
        # Start both streams as close together as possible for better sync
        if not no_mic:
            self._start_mic_audio()
        else:
            self.mic_stream = None
            logging.info("Microphone recording disabled")
        
        self._start_system_audio()
        
        logging.info("Recording started. Press Ctrl+C to stop.")
        logging.info("Note: Audio streams may have slight timing differences at start/end")
        
    def _check_system_audio(self):
        """Check if system audio recording is available"""
        try:
            if sys.platform == "win32":
                # Windows: Check for WASAPI loopbacks
                with pyaudio.PyAudio() as pa:
                    try:
                        pa.get_default_wasapi_loopback()
                    except Exception as e:
                        logging.warning("System audio loopback not available on Windows")
                        logging.warning("Make sure you have audio drivers installed and WASAPI-enabled Windows version")
            else:
                # Linux: Check for available input devices (Speaker/default/pipewire)
                devices = sd.query_devices()
                found_device = False
                for dev in devices:
                    name_lower = dev['name'].lower()
                    if dev['max_input_channels'] > 0 and ('speaker' in name_lower or 'default' in name_lower or 'pipewire' in name_lower):
                        found_device = True
                        logging.info(f"Found system audio device: {dev['name']}")
                        break
                if not found_device:
                    logging.warning("No suitable audio input device found")
                    logging.warning("Make sure PulseAudio/PipeWire is running")
        except Exception as e:
            logging.warning(f"Could not check system audio: {e}")
    
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
            logging.info(f"System audio status: {status}")
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
            logging.info(f"Microphone audio status: {status}")
        if self.is_recording:
            # sounddevice returns numpy array directly
            self.mic_audio_data.append(indata.copy())
            
    def _start_system_audio(self):
        """Start system audio recording using cross-platform methods"""
        try:
            if sys.platform == "win32":
                # Windows: Use PyAudio with WASAPI loopback
                lb = self.pa.get_default_wasapi_loopback()
                self.sys_sample_rate = int(lb["defaultSampleRate"])
                self.sys_channels = max(1, int(lb["maxInputChannels"]))
                input_index = lb["index"]
                
                logging.info(f"System audio: {self.sys_sample_rate} Hz, {self.sys_channels} channel(s)")
                
                self.sys_stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=self.sys_channels,
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
                        logging.info(f"Using system audio device: {dev['name']}")
                        break
                
                # Fallback to default or pipewire device
                if not system_device:
                    for idx, dev in enumerate(devices):
                        name_lower = dev['name'].lower()
                        if dev['max_input_channels'] > 0 and ('default' in name_lower or 'pipewire' in name_lower):
                            system_device = dev
                            system_index = idx
                            logging.info(f"Using system audio device: {dev['name']}")
                            break
                
                if not system_device:
                    raise RuntimeError("No suitable audio device found for system audio recording")
                
                # Start sounddevice input stream
                self.sys_channels = min(2, system_device['max_input_channels'])
                
                logging.info(f"System audio: {self.sys_sample_rate} Hz, {self.sys_channels} channel(s)")
                
                self.sys_stream = sd.InputStream(
                    device=system_index,
                    channels=self.sys_channels,
                    samplerate=self.sys_sample_rate,
                    dtype=np.int16,
                    callback=self._sys_audio_callback_sd,
                    blocksize=CHUNK_SIZE
                )
                self.sys_stream.start()
                
        except Exception as e:
            logging.warning(f"Could not start system audio recording: {e}")

    def _start_mic_audio(self):
        """Start mic audio recording using cross-platform methods"""
        try:
            if sys.platform == "win32":
                # Windows: Use PyAudio
                dev = self.pa.get_default_input_device_info()
                self.mic_sample_rate = int(dev["defaultSampleRate"])
                self.mic_channels = max(1, int(dev["maxInputChannels"]))
                
                logging.info(f"Microphone: {self.mic_sample_rate} Hz, {self.mic_channels} channel(s)")
                
                self.mic_stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=self.mic_channels,
                    rate=self.mic_sample_rate,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    stream_callback=self._mic_audio_callback_pyaudio
                )
                self.mic_stream.start_stream()
            else:
                # Linux: Use sounddevice
                self.mic_channels = 1  # Mono for mic
                logging.info(f"Microphone: {self.mic_sample_rate} Hz, {self.mic_channels} channel")
                
                self.mic_stream = sd.InputStream(
                    channels=self.mic_channels,
                    samplerate=self.mic_sample_rate,
                    dtype=np.int16,
                    callback=self._mic_audio_callback_sd,
                    blocksize=CHUNK_SIZE
                )
                self.mic_stream.start()
                
        except Exception as e:
            logging.warning(f"Could not start mic audio recording: {e}")
            
    def stop_recording(self):
        """Stop recording and save audio"""
        if not self.is_recording:
            logging.warning("Not currently recording!")
            return
            
        logging.info("Stopping recording...")
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
                logging.info("Processing microphone and system audio...")
                self._combine_audio()
                logging.info(f"Combined audio saved to {RECORDING_FILE}")
                logging.info(f" → {self.sys_sample_rate} Hz (system audio rate)")
            elif self.mic_audio_data:
                # Only microphone audio
                logging.info("Processing microphone audio...")
                mic_audio = np.concatenate(self.mic_audio_data, axis=0)
                self._save_audio_int16(mic_audio, RECORDING_FILE, self.mic_sample_rate, self.mic_channels)
                logging.info(f"Microphone audio saved to {RECORDING_FILE}")
                logging.info(f" → {self.mic_channels} channel(s), 16-bit, {self.mic_sample_rate} Hz")
            elif self.sys_audio_data:
                # Only system audio
                logging.info("Processing system audio...")
                sys_audio = np.concatenate(self.sys_audio_data, axis=0)
                self._save_audio_int16(sys_audio, RECORDING_FILE, self.sys_sample_rate, self.sys_channels)
                logging.info(f"System audio saved to {RECORDING_FILE}")
                logging.info(f" → {self.sys_channels} channel(s), 16-bit, {self.sys_sample_rate} Hz")
            else:
                logging.warning("No audio was recorded!")
        except Exception as e:
            logging.error(f"Error saving audio: {e}")
            
        logging.info("Recording stopped.")
        
    def _save_audio_int16(self, audio_data, filename, sample_rate=48000, channels=1):
        """Save audio data (already in int16 format) to WAV file"""
        
        # Determine actual channel count from data shape
        if len(audio_data.shape) > 1:
            actual_channels = audio_data.shape[1]
        else:
            actual_channels = 1
        
        # Use provided channels or detected channels
        output_channels = channels if channels > 0 else actual_channels
        
        with wave.open(str(filename), 'wb') as wav_file:
            wav_file.setnchannels(output_channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
            
    def _combine_audio(self):
        """Combine microphone and system audio"""
        try:
            # Concatenate all mic and system audio chunks
            mic_audio = np.concatenate(self.mic_audio_data, axis=0)
            sys_audio = np.concatenate(self.sys_audio_data, axis=0)
            
            logging.debug(f"  Mic shape before: {mic_audio.shape}, channels: {self.mic_channels}")
            logging.debug(f"  Sys shape before: {sys_audio.shape}, channels: {self.sys_channels}")
            
            # Convert to 1D mono arrays (flatten multi-channel data)
            if len(mic_audio.shape) > 1:
                if mic_audio.shape[1] == 2:
                    # Stereo: average the two channels
                    logging.debug(f"  Converting mic from stereo to mono")
                    mic_audio = mic_audio.mean(axis=1).astype(np.int16)
                elif mic_audio.shape[1] == 1:
                    # Already mono but 2D: flatten it
                    logging.debug(f"  Flattening mic audio")
                    mic_audio = mic_audio.flatten()
            elif self.mic_channels == 2:
                # 1D interleaved stereo [L, R, L, R, ...] - reshape and average
                logging.debug(f"  Deinterleaving mic stereo to mono")
                mic_audio = mic_audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            if len(sys_audio.shape) > 1:
                if sys_audio.shape[1] == 2:
                    # Stereo: average the two channels
                    logging.debug(f"  Converting sys from stereo to mono")
                    sys_audio = sys_audio.mean(axis=1).astype(np.int16)
                elif sys_audio.shape[1] == 1:
                    # Already mono but 2D: flatten it
                    logging.debug(f"  Flattening sys audio")
                    sys_audio = sys_audio.flatten()
            elif self.sys_channels == 2:
                # 1D interleaved stereo [L, R, L, R, ...] - reshape and average
                logging.debug(f"  Deinterleaving sys stereo to mono")
                sys_audio = sys_audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            logging.debug(f"  Mic shape after: {mic_audio.shape}")
            logging.debug(f"  Sys shape after: {sys_audio.shape}")
            
            # Calculate actual recording durations
            mic_duration = len(mic_audio) / self.mic_sample_rate
            sys_duration = len(sys_audio) / self.sys_sample_rate
            logging.debug(f"  Mic duration: {mic_duration:.2f}s")
            logging.debug(f"  Sys duration: {sys_duration:.2f}s")
            
            # Resample mic to match system audio sample rate FIRST
            if self.mic_sample_rate != self.sys_sample_rate:
                logging.debug(f"  Resampling mic: {self.mic_sample_rate} Hz -> {self.sys_sample_rate} Hz")
                mic_audio_float = mic_audio.astype(np.float32) / 32768.0
                mic_audio = librosa.resample(
                    mic_audio_float, 
                    orig_sr=self.mic_sample_rate, 
                    target_sr=self.sys_sample_rate
                )
                mic_audio = (mic_audio * 32767).astype(np.int16)
                logging.debug(f"  Mic shape after resampling: {mic_audio.shape}")
            
            # Now both are at the same sample rate - align by duration
            # Use the shorter duration to avoid padding with silence
            target_duration = min(mic_duration, sys_duration)
            target_samples = int(target_duration * self.sys_sample_rate)
            
            logging.debug(f"  Target duration: {target_duration:.2f}s ({target_samples} samples)")
            
            # Trim both to the same length (use shorter duration)
            mic_audio = mic_audio[:target_samples]
            sys_audio = sys_audio[:target_samples]
            
            logging.debug(f"  Final aligned - Mic: {len(mic_audio)}, Sys: {len(sys_audio)}")
            
            # Simple mixing - convert to float for mixing, then back to int16
            logging.debug(f"  Mixing audio (50/50 blend)")
            mic_float = mic_audio.astype(np.float32)
            sys_float = sys_audio.astype(np.float32)
            combined = ((mic_float + sys_float) / 2).astype(np.int16)
            
            logging.debug(f"  Final combined shape: {combined.shape}")
            
            # Save combined audio at system audio sample rate (mono after mixing)
            self._save_audio_int16(combined, RECORDING_FILE, self.sys_sample_rate, channels=1)
            
        except Exception as e:
            logging.warning(f"Could not combine audio: {e}")
            # Fallback: save audios separately
            if self.mic_audio_data:
                mic_audio = np.concatenate(self.mic_audio_data, axis=0)
                self._save_audio_int16(mic_audio, str(RECORDING_FILE).replace(".wav", "_mic.wav"), self.mic_sample_rate, self.mic_channels)
            if self.sys_audio_data:
                sys_audio = np.concatenate(self.sys_audio_data, axis=0)
                self._save_audio_int16(sys_audio, str(RECORDING_FILE).replace(".wav", "_sys.wav"), self.sys_sample_rate, self.sys_channels)