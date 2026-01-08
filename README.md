# Offline Meeting Transcriber

> Privacy-first, AI-powered meeting transcription with speaker diarization, completely offline!

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Offline](https://img.shields.io/badge/Offline-100%25-red.svg)](#privacy-and-security)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](#platform-specific-notes)

Transform your meetings into searchable, speaker-labeled transcripts without sending any data to the cloud. This tool combines advanced speech recognition with speaker diarization to create professional meeting records.

## Features

- **100% Offline** - No internet required, complete privacy
- **Dual Audio Capture** - Records both microphone and system audio
- **Speaker Diarization** - Automatically identifies different speakers
- **Multi-language Support** - Configurable language detection
- **Cross-platform** - Works on Windows and Linux
- **Fast Processing** - Optimized for CPU inference
- **Multiple Output Formats** - Plain text and speaker-labeled transcripts
- **Easy Setup** - Simple CLI interface

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git LFS (for downloading models)
- Audio input device (microphone)
- ~2GB free disk space for models

### Installation

#### Quick Install (Recommended)

**Linux/Mac:**
```bash
git clone https://github.com/whitehole07/offline-meeting-transcriber.git
cd offline-meeting-transcriber
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
git clone https://github.com/whitehole07/offline-meeting-transcriber.git
cd offline-meeting-transcriber
install.bat
```

The installation script will automatically:
- Create a virtual environment
- Install all Python dependencies
- Download Whisper model (~1.5GB) via git LFS
- Download SpeechBrain speaker model (~100MB) via git LFS
- Set up the complete environment
- Test the installation

#### Manual Installation

If you prefer to install manually:

1. **Clone the repository**
   ```bash
   git clone https://github.com/whitehole07/offline-meeting-transcriber.git
   cd offline-meeting-transcriber
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download models**
   - **Whisper Model**: `Systran/faster-whisper-medium` (~1.5GB)
     - Speech-to-text transcription model
     - Optimized for CPU inference
     - Supports multiple languages
   - **SpeechBrain Model**: `speechbrain/spkrec-ecapa-voxceleb` (~100MB)
     - Speaker diarization model
     - ECAPA-TDNN architecture
     - Trained on VoxCeleb dataset

#### Model Details and Manual Download

If you need to download models manually:

**Whisper Model (`Systran/faster-whisper-medium`)**:
```bash
git clone https://huggingface.co/Systran/faster-whisper-medium models/faster-whisper-medium
```
- **Purpose**: Converts speech to text
- **Architecture**: Transformer-based encoder-decoder
- **Size**: ~1.5GB
- **Languages**: 99 languages supported
- **Optimization**: CPU-optimized version of OpenAI Whisper

**SpeechBrain Model (`speechbrain/spkrec-ecapa-voxceleb`)**:
```bash
git clone https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb models/spkrec-ecapa-voxceleb
```
- **Purpose**: Identifies different speakers in audio
- **Architecture**: ECAPA-TDNN (Extended Context Aggregation)
- **Size**: ~100MB
- **Training**: VoxCeleb dataset (1M+ utterances from 7K+ speakers)
- **Features**: Speaker embedding extraction and clustering

### Usage

#### Start Recording
```bash
# Record with microphone + system audio
python cli.py start

# Record system audio only (no microphone)
python cli.py start --no-mic
```

#### Stop Recording and Process
Press `Ctrl+C` to stop recording and automatically process the audio.

## Output Files

After processing, you'll find these files in `output/YYYYMMDD/`:

- `recording_HHMMSS.wav` - Original audio recording
- `transcription_HHMMSS.txt` - Plain text transcription
- `diarized_HHMMSS.txt` - Speaker-labeled transcription

### Example Output

**Plain Transcription:**
```
When you become fascist or communist or anarchist in those years, you can also simply be someone who never reasons...
```

**Diarized Transcription:**
```
SPEAKER_01 (00:00-01:10): When you become fascist or communist or anarchist in those years, you can also simply be someone who never reasons and therefore it's true yes I go with my friends and beat up those others...

SPEAKER_00 (01:10-02:14): We're not doing that well, no we're not doing that well guys, if it goes well you make me laugh...
```

## Configuration

Edit `config.py` to customize:

```python
WHISPER_MODEL = "medium"  # base, small, medium, large
WHISPER_LANGUAGE = "en"   # Language code
```

## Troubleshooting

**Model download fails:**
```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('medium')"
```

**Poor transcription quality:**
- Ensure clear audio input
- Check microphone levels
- Try different Whisper model sizes
- Verify language setting matches audio

**Recording doesn't stop:**
- Press `Ctrl+C` to stop recording and process audio
- The system will automatically transcribe and diarize after stopping

**Installation issues:**
- Make sure you have Python 3.8+ installed
- Ensure you have Git LFS installed (required for model downloads)
  - **Linux/Mac**: `git lfs install` (after installing git-lfs package)
  - **Windows**: Install Git LFS from https://git-lfs.github.io
- Ensure you have internet connection for model downloads
- If models fail to download, try running the installation script again
- Check that you have sufficient disk space (~2GB for models)
- On Windows, make sure you're running the batch file as administrator if needed
- If git clone fails, try: `git lfs pull` in the model directories

### Platform-Specific Notes

**Windows:**
- Requires `pyaudiowpatch` for system audio capture
- WASAPI loopback support needed
- May need audio driver updates

**Linux:**
- Requires PulseAudio or PipeWire
- May need additional audio packages
- Check device permissions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [SpeechBrain](https://speechbrain.github.io/) - Speaker diarization
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio I/O

## Project Stats

![GitHub stars](https://img.shields.io/github/stars/whitehole07/offline-meeting-transcriber?style=social)
![GitHub forks](https://img.shields.io/github/forks/whitehole07/offline-meeting-transcriber?style=social)
![GitHub issues](https://img.shields.io/github/issues/whitehole07/offline-meeting-transcriber)
![GitHub pull requests](https://img.shields.io/github/issues-pr/whitehole07/offline-meeting-transcriber)

---

**Found a bug?** [Open an issue](https://github.com/whitehole07/offline-meeting-transcriber/issues)

**Have a feature request?** [Start a discussion](https://github.com/whitehole07/offline-meeting-transcriber/discussions)
