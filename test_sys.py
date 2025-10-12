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

lb = pa.get_default_wasapi_loopback()
rate = int(lb["defaultSampleRate"])
channels = max(1, int(lb["maxInputChannels"]))

stream = pa.open(format=FMT, channels=channels, rate=rate,
                    input=True, input_device_index=lb["index"],
                    frames_per_buffer=CHUNK, stream_callback=audio_callback)

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
wf.setnchannels(channels)
wf.setsampwidth(sample_size)
wf.setframerate(rate)
wf.writeframes(b''.join(frames))
wf.close()
