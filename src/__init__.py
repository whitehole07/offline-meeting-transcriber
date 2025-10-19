"""
Offline Meeting Transcriber - Core Modules

This package contains the core functionality for offline meeting transcription
and speaker diarization.
"""

from .recorder import AudioRecorder
from .transcriber import MeetingTranscriber
from .speaker_diarizer import SpeakerDiarizer

__all__ = ['AudioRecorder', 'MeetingTranscriber', 'SpeakerDiarizer']
