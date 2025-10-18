#!/usr/bin/env python3
"""
Comprehensive import test for meeting-agent
Tests all modules and dependencies to identify issues
"""

import sys
import warnings
import traceback

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def test_import(module_name, import_statement=None):
    """Test importing a module and report results"""
    try:
        if import_statement:
            exec(import_statement)
        else:
            __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except Exception as e:
        print(f"❌ {module_name}: {e}")
        return False

def test_config_imports():
    """Test all config imports"""
    print("\n🔧 Testing Config Imports:")
    print("-" * 40)
    
    config_imports = [
        "RECORDING_FILE",
        "TRANSCRIPTION_FILE", 
        "DIARIZED_FILE",
        "WHISPER_MODEL",
        "WHISPER_LANGUAGE",
        "SAMPLE_RATE",
        "WHISPER_MODEL_PATH",
        "DIARIZATION_MODEL_PATH"
    ]
    
    success_count = 0
    for var in config_imports:
        try:
            exec(f"from config import {var}")
            print(f"✅ {var}")
            success_count += 1
        except Exception as e:
            print(f"❌ {var}: {e}")
    
    print(f"\nConfig imports: {success_count}/{len(config_imports)} successful")
    return success_count == len(config_imports)

def test_core_dependencies():
    """Test core Python dependencies"""
    print("\n📦 Testing Core Dependencies:")
    print("-" * 40)
    
    core_modules = [
        "json",
        "sys", 
        "warnings",
        "logging",
        "pathlib",
        "numpy",
        "librosa",
        "os"
    ]
    
    success_count = 0
    for module in core_modules:
        if test_import(module):
            success_count += 1
    
    print(f"\nCore dependencies: {success_count}/{len(core_modules)} successful")
    return success_count == len(core_modules)

def test_audio_dependencies():
    """Test audio processing dependencies"""
    print("\n🎵 Testing Audio Dependencies:")
    print("-" * 40)
    
    audio_modules = [
        ("faster_whisper", "from faster_whisper import WhisperModel"),
        ("pyannote.audio", "from pyannote.audio import Pipeline"),
        ("sounddevice", "import sounddevice as sd"),
        ("torch", "import torch"),
        ("torchaudio", "import torchaudio")
    ]
    
    success_count = 0
    for module_name, import_stmt in audio_modules:
        if test_import(module_name, import_stmt):
            success_count += 1
    
    print(f"\nAudio dependencies: {success_count}/{len(audio_modules)} successful")
    return success_count == len(audio_modules)

def test_platform_specific():
    """Test platform-specific imports"""
    print("\n🖥️  Testing Platform-Specific Imports:")
    print("-" * 40)
    
    if sys.platform == "win32":
        print("Windows detected - testing Windows-specific modules:")
        windows_modules = [
            ("pyaudiowpatch", "import pyaudiowpatch as pyaudio"),
            ("pyaudio", "import pyaudio")
        ]
        
        success_count = 0
        for module_name, import_stmt in windows_modules:
            if test_import(module_name, import_stmt):
                success_count += 1
        
        print(f"Windows modules: {success_count}/{len(windows_modules)} successful")
        return success_count > 0
    else:
        print("Linux/Mac detected - testing Unix-specific modules:")
        unix_modules = [
            ("sounddevice", "import sounddevice as sd")
        ]
        
        success_count = 0
        for module_name, import_stmt in unix_modules:
            if test_import(module_name, import_stmt):
                success_count += 1
        
        print(f"Unix modules: {success_count}/{len(unix_modules)} successful")
        return success_count > 0

def test_main_modules():
    """Test main application modules"""
    print("\n🚀 Testing Main Application Modules:")
    print("-" * 40)
    
    main_modules = [
        ("config", "import config"),
        ("recorder", "from recorder import AudioRecorder"),
        ("transcriber", "from transcriber import MeetingTranscriber"),
        ("cli", "import cli")
    ]
    
    success_count = 0
    for module_name, import_stmt in main_modules:
        if test_import(module_name, import_stmt):
            success_count += 1
    
    print(f"\nMain modules: {success_count}/{len(main_modules)} successful")
    return success_count == len(main_modules)

def test_class_instantiation():
    """Test creating instances of main classes"""
    print("\n🏗️  Testing Class Instantiation:")
    print("-" * 40)
    
    try:
        from recorder import AudioRecorder
        recorder = AudioRecorder()
        print("✅ AudioRecorder instance created")
        recorder_success = True
    except Exception as e:
        print(f"❌ AudioRecorder: {e}")
        recorder_success = False
    
    try:
        from transcriber import MeetingTranscriber
        transcriber = MeetingTranscriber()
        print("✅ MeetingTranscriber instance created")
        transcriber_success = True
    except Exception as e:
        print(f"❌ MeetingTranscriber: {e}")
        transcriber_success = False
    
    return recorder_success and transcriber_success

def test_environment_variables():
    """Test environment variables"""
    print("\n🌍 Testing Environment Variables:")
    print("-" * 40)
    
    import os
    from dotenv import load_dotenv
    
    # Load .env file
    load_dotenv()
    
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("✅ HF_TOKEN found in environment")
        return True
    else:
        print("⚠️  HF_TOKEN not found in environment (optional)")
        return True

def main():
    """Run all import tests"""
    print("🧪 Meeting Agent - Comprehensive Import Test")
    print("=" * 50)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Core Dependencies", test_core_dependencies),
        ("Audio Dependencies", test_audio_dependencies),
        ("Platform-Specific", test_platform_specific),
        ("Config Imports", test_config_imports),
        ("Environment Variables", test_environment_variables),
        ("Main Modules", test_main_modules),
        ("Class Instantiation", test_class_instantiation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
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
        print("🎉 All tests passed! The application should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Set HF_TOKEN environment variable if needed")
        print("- Check platform-specific dependencies")

if __name__ == "__main__":
    main()
