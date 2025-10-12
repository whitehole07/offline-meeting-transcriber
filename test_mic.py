# pip install PyAudioWPatch
import pyaudiowpatch as pyaudio
import wave, math
import time

DUR = 10
CHUNK = 1024
FMT = pyaudio.paInt16
OUT = "loopback_record.wav"

frames = []
def audio_callback(in_data, frame_count, time_info, status):
    """Called automatically every time a new chunk of audio arrives."""
    # Store raw bytes (for writing directly to file later)
    frames.append(in_data)
    # You can also process the audio in real-time here:
    # audio = np.frombuffer(in_data, dtype=np.float32)
    return (None, pyaudio.paContinue)

pa = pyaudio.PyAudio()

# Use the default input device's native settings
dev = pa.get_default_input_device_info()
rate = int(dev["defaultSampleRate"])
# Prefer mono if available; fall back to 2 if needed
channels = 1 if dev.get("maxInputChannels", 1) >= 1 else 1

stream = pa.open(
    format=FMT,
    channels=channels,
    rate=rate,
    input=True,
    frames_per_buffer=CHUNK,
    stream_callback=audio_callback
)

stream.start_stream()

try:
    while stream.is_active():
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

stream.stop_stream()
stream.close()

sample_size = pa.get_sample_size(FMT)
pa.terminate()

wf = wave.open(OUT, 'wb')
wf.setnchannels(1)
wf.setsampwidth(sample_size)
wf.setframerate(rate)
wf.writeframes(b''.join(frames))
wf.close()