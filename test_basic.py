#!/usr/bin/env python3
"""
Basic functionality test for meeting-agent
Quick test to verify core functionality works
"""

import sys
import warnings
import os
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")

def test_basic_imports():
    """Test basic imports"""
    print("🧪 Testing Basic Imports...")
    
    try:
        from config import RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE
        print("✅ Config imports successful")
        
        from recorder import AudioRecorder
        print("✅ AudioRecorder import successful")
        
        from transcriber import MeetingTranscriber
        print("✅ MeetingTranscriber import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_class_creation():
    """Test creating class instances"""
    print("\n🏗️  Testing Class Creation...")
    
    try:
        from recorder import AudioRecorder
        from transcriber import MeetingTranscriber
        
        recorder = AudioRecorder()
        print("✅ AudioRecorder instance created")
        
        transcriber = MeetingTranscriber()
        print("✅ MeetingTranscriber instance created")
        
        return True
    except Exception as e:
        print(f"❌ Class creation failed: {e}")
        return False

def test_config_values():
    """Test config values"""
    print("\n⚙️  Testing Config Values...")
    
    try:
        from config import (
            RECORDING_FILE, TRANSCRIPTION_FILE, DIARIZED_FILE,
            WHISPER_MODEL, WHISPER_LANGUAGE, SAMPLE_RATE
        )
        
        print(f"✅ Recording file: {RECORDING_FILE}")
        print(f"✅ Transcription file: {TRANSCRIPTION_FILE}")
        print(f"✅ Diarized file: {DIARIZED_FILE}")
        print(f"✅ Whisper model: {WHISPER_MODEL}")
        print(f"✅ Language: {WHISPER_LANGUAGE}")
        print(f"✅ Sample rate: {SAMPLE_RATE}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_environment():
    """Test environment setup"""
    print("\n🌍 Testing Environment...")
    
    print(f"✅ Platform: {sys.platform}")
    print(f"✅ Python: {sys.version.split()[0]}")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (optional)")
    
    # Check HF_TOKEN
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("✅ HF_TOKEN found in environment")
    else:
        print("⚠️  HF_TOKEN not found (optional)")
    
    return True

def main():
    """Run basic tests"""
    print("🚀 Meeting Agent - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Class Creation", test_class_creation),
        ("Config Values", test_config_values),
        ("Environment", test_environment)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 Basic functionality test passed!")
        print("The application should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nTo run more detailed tests:")
        print("- Linux/Mac: python test_imports.py")
        print("- Windows: python test_windows_imports.py")

if __name__ == "__main__":
    main()
