#!/usr/bin/env python3
"""
Meeting Transcriber CLI
A lightweight tool for recording and transcribing meetings offline.
"""

import sys
import signal
import time
from recorder import AudioRecorder
from transcriber import MeetingTranscriber
from config import RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE

class MeetingTranscriberCLI:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = MeetingTranscriber()
        self.recording_started = False
        
    def start_recording(self, no_mic=False):
        """Start recording audio"""
        if self.recording_started:
            print("Recording already in progress!")
            return
            
        try:
            # Clean up any existing files
            for file_path in [RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE]:
                if file_path.exists():
                    file_path.unlink()
                    
            self.recorder.start_recording(no_mic=no_mic)
            self.recording_started = True
            
            # Set up signal handler for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Keep recording until interrupted
            try:
                while self.recording_started:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop_recording()
                
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording_started = False
            
    def stop_recording(self):
        """Stop recording and process audio"""
        if not self.recording_started:
            print("No recording in progress!")
            return
            
        self.recorder.stop_recording()
        self.recording_started = False
        
        # Process the recorded audio
        print("Processing audio...")
        success = self.transcriber.transcribe_and_diarize()
        
        if success:
            print("\nProcessing complete!")
            print(f"Files created:")
            print(f"  - {RECORDING_FILE}")
            print(f"  - {TRANSCRIPTION_FILE}")
            print(f"  - {DIARIZED_FILE}")
        else:
            print("Processing failed!")
            
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\nReceived signal {signum}")
        self.stop_recording()
        sys.exit(0)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: meeting-transcriber <start|stop> [--no-mic]")
        print("\nCommands:")
        print("  start  - Start recording audio")
        print("  stop   - Stop recording and process audio")
        print("\nOptions:")
        print("  --no-mic  - Record system audio only (no microphone)")
        sys.exit(1)
    cli = MeetingTranscriberCLI()
    command = sys.argv[1].lower()
    no_mic = "--no-mic" in sys.argv

    if command == "start":
        cli.start_recording(no_mic=no_mic)
    elif command == "stop":
        cli.stop_recording()
    else:
        print(f"Unknown command: {command}")
        print("Use 'start' or 'stop'")
        sys.exit(1)

if __name__ == "__main__":
    main()
