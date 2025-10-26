def get_system_default_monitor():
    """
    Get the system default monitor device for audio loopback recording.
    
    **LINUX-SPECIFIC FUNCTION** - This function only works on Linux systems
    with PulseAudio or PipeWire audio servers. It will return None on Windows
    or macOS systems.
    
    This function attempts to find the system's default audio monitor device
    that can be used for recording system audio (what you hear). It tries
    multiple Linux audio systems in order of preference.
    
    Returns:
        str or None: The name of the monitor device if found, None otherwise.
                    The returned device name can be used with sounddevice
                    for system audio recording.
    
    Linux Audio Systems Supported:
        1. PulseAudio - Uses 'pactl info' to get default sink and appends '.monitor'
        2. PipeWire - Uses 'pw-record --list-targets' to find monitor devices
    
    Examples:
        >>> monitor = get_system_default_monitor()
        >>> if monitor:
        ...     print(f"Using monitor device: {monitor}")
        ... else:
        ...     print("No monitor device found")
    
    Notes:
        - **Linux only**: This function requires Linux with PulseAudio or PipeWire
        - PulseAudio: Returns format like "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
        - PipeWire: Returns the first available monitor device from the list
        - Returns None if neither audio system is available or no monitor found
        - Windows users should use pyaudiowpatch for system audio capture
        - macOS users should use different audio capture methods
    """
    # Try PulseAudio first
    import subprocess, re
    try:
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True)
        match = re.search(r"Default Sink: (.+)", result.stdout)
        if match:
            return f"{match.group(1)}.monitor"
    except FileNotFoundError:
        pass

    # Fallback to PipeWire
    try:
        result = subprocess.run(["pw-record", "--list-targets"], capture_output=True, text=True)
        monitors = [line.strip() for line in result.stdout.splitlines() if "monitor" in line]
        if monitors:
            return monitors[0]
    except FileNotFoundError:
        pass

    return None
    

def start_pulseaudio_loopback(callback, sample_rate=44100, channels=2, chunk_size=1024):
    """
    Start a PulseAudio-native system audio loopback stream.

    Args:
        callback (callable): Function that receives audio chunks as a NumPy array.
        sample_rate (int): Sample rate in Hz (default 44100).
        channels (int): Number of audio channels (default 2).
        chunk_size (int): Frames per chunk read from PulseAudio (default 1024).

    Returns:
        subprocess.Popen, threading.Thread: The parec process and reading thread.
    """
    import subprocess
    import logging
    import numpy as np
    import threading
    
    # Step 1: Get the default sink monitor
    monitor_name = get_system_default_monitor()
    if monitor_name is None:
        raise RuntimeError("No system default monitor found")
    logging.info(f"Using PulseAudio monitor: {monitor_name}")

    # Step 2: Start parec subprocess
    parec_cmd = [
        "parec",
        "--format=s16le",
        f"--rate={sample_rate}",
        f"--channels={channels}",
        monitor_name
    ]
    parec_proc = subprocess.Popen(parec_cmd, stdout=subprocess.PIPE)

    # Step 3: Thread to read audio chunks
    def audio_thread():
        bytes_per_frame = 2 * channels  # 16-bit = 2 bytes
        while True:
            data = parec_proc.stdout.read(chunk_size * bytes_per_frame)
            if not data:
                break
            audio_chunk = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
            callback(audio_chunk)

    thread = threading.Thread(target=audio_thread, daemon=True)
    thread.start()
    logging.info("PulseAudio loopback stream started")

    return parec_proc, thread