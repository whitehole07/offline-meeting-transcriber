#!/usr/bin/env python3
"""
Meeting Transcriber CLI
A lightweight tool for recording and transcribing meetings offline.
"""

import sys
import signal
import time
import logging
from src.recorder import AudioRecorder
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
        
        # Show platform information
        platform_name = "Windows" if sys.platform == "win32" else "Linux/Mac"
        logging.info(f"{platform_name} detected - diarization will be enabled")
            
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
                self._stop_and_process()
                
        except Exception as e:
            logging.error(f"Error starting recording: {e}")
            self.recording_started = False
            
    def _process_audio(self):
        """Process recorded audio with transcription and diarization"""
        logging.info("Processing audio...")
        
        # Create transcriber lazily when needed
        if self.transcriber is None:
            from src.transcriber import MeetingTranscriber
            self.transcriber = MeetingTranscriber()
        
        success = self.transcriber.transcribe_and_diarize()
        
        if success:
            logging.info("Processing complete!")
            logging.info(f"Files created:")
            logging.info(f" → {RECORDING_FILE}")
            logging.info(f" → {TRANSCRIPTION_FILE}")
            
            # Show diarization file
            logging.info(f" → {DIARIZED_FILE}")
        else:
            logging.error("Processing failed!")
            
    def _stop_and_process(self):
        """Stop recording and automatically process audio"""
        if not self.recording_started:
            logging.warning("No recording in progress!")
            return
            
        logging.info("Stopping recording...")
        self.recorder.stop_recording()
        self.recording_started = False
        
        # Automatically process the audio
        self._process_audio()
        
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        logging.info(f"Received signal {signum}")
        self._stop_and_process()
        sys.exit(0)

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python cli.py start [--no-mic]")
        print("\nCommands:")
        print("  start     Start recording audio (press Ctrl+C to stop and process)")
        print("\nOptions:")
        print("  --no-mic  Record system audio only (no microphone)")
        print("\nNote: Recording will automatically process when you press Ctrl+C")
        sys.exit(1)
    
    cli = MeetingTranscriberCLI()
    command = sys.argv[1].lower()
    no_mic = "--no-mic" in sys.argv

    if command == "start":
        cli.start_recording(no_mic=no_mic)
    else:
        print(f"Unknown command: {command}")
        print("Use 'start' to begin recording")
        sys.exit(1)

if __name__ == "__main__":
    main()
