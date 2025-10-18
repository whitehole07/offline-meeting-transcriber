#!/usr/bin/env python3
"""
Meeting Transcriber CLI
A lightweight tool for recording and transcribing meetings offline.
"""

import sys
import signal
import time
import logging
from recorder import AudioRecorder
# Heavy transcriber will be imported lazily when needed
from config import RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

class MeetingTranscriberCLI:
    """CLI interface for the meeting transcriber application."""
    
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = None  # Will be created lazily when needed
        self.recording_started = False
        
    def start_recording(self, no_mic=False):
        """Start recording audio"""
        if self.recording_started:
            logging.warning("Recording already in progress!")
            return
        
        # Show platform-specific information
        if sys.platform == "win32":
            logging.info("Windows detected - diarization will be disabled")
        else:
            logging.info("Linux/Mac detected - diarization will be enabled")
            
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
            logging.error(f"Error starting recording: {e}")
            self.recording_started = False
            
    def stop_recording(self):
        """Stop recording and process audio"""
        if not self.recording_started:
            logging.warning("No recording in progress!")
            return
            
        self.recorder.stop_recording()
        self.recording_started = False
        
        # TODO: Uncomment to enable transcription and diarization
        logging.info("Processing audio...")
        
        # Create transcriber lazily when needed
        if self.transcriber is None:
            from transcriber import MeetingTranscriber
            self.transcriber = MeetingTranscriber()
        
        success = self.transcriber.transcribe_and_diarize()
        success = True
        
        if success:
            logging.info("Processing complete!")
            logging.info(f"Files created:")
            logging.info(f" → {RECORDING_FILE}")
            logging.info(f" → {TRANSCRIPTION_FILE}")
            
            # Show diarization file only on non-Windows platforms
            if sys.platform != "win32":
                logging.info(f" → {DIARIZED_FILE}")
            else:
                logging.info(" → Diarization disabled on Windows")
        else:
            logging.error("Processing failed!")
            
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        logging.info(f"Received signal {signum}")
        self.stop_recording()
        sys.exit(0)

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python cli.py <start|stop> [--no-mic]")
        print("\nCommands:")
        print("  start     Start recording audio")
        print("  stop      Stop recording and process audio")
        print("\nOptions:")
        print("  --no-mic  Record system audio only (no microphone)")
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
