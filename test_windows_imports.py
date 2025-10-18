#!/usr/bin/env python3
"""
Windows-specific import test for meeting-agent
Tests Windows compatibility and identifies torchaudio issues
"""

import sys
import warnings
import traceback

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def test_torchaudio_windows():
    """Test torchaudio specifically on Windows"""
    print("\n🔧 Testing TorchAudio on Windows:")
    print("-" * 40)
    
    if sys.platform != "win32":
        print("⚠️  Not running on Windows - skipping Windows-specific tests")
        return True
    
    try:
        import torchaudio
        print("✅ torchaudio imported successfully")
        
        # Test the problematic method
        try:
            backends = torchaudio.list_audio_backends()
            print(f"✅ list_audio_backends() works: {backends}")
            return True
        except AttributeError as e:
            print(f"❌ list_audio_backends() failed: {e}")
            print("This is the known Windows issue!")
            return False
        except Exception as e:
            print(f"⚠️  list_audio_backends() error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ torchaudio import failed: {e}")
        return False

def test_pyannote_windows():
    """Test pyannote.audio on Windows"""
    print("\n🎤 Testing PyAnnote on Windows:")
    print("-" * 40)
    
    if sys.platform != "win32":
        print("⚠️  Not running on Windows - skipping Windows-specific tests")
        return True
    
    try:
        from pyannote.audio import Pipeline
        print("✅ pyannote.audio imported successfully")
        
        # Try to create a pipeline (this might fail due to torchaudio issues)
        try:
            # This will likely fail on Windows due to torchaudio backend issues
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            print("✅ Pipeline created successfully")
            return True
        except Exception as e:
            print(f"❌ Pipeline creation failed: {e}")
            print("This is likely due to torchaudio backend issues")
            return False
            
    except ImportError as e:
        print(f"❌ pyannote.audio import failed: {e}")
        return False

def test_windows_audio_modules():
    """Test Windows-specific audio modules"""
    print("\n🎵 Testing Windows Audio Modules:")
    print("-" * 40)
    
    if sys.platform != "win32":
        print("⚠️  Not running on Windows - skipping Windows-specific tests")
        return True
    
    windows_modules = [
        ("pyaudiowpatch", "import pyaudiowpatch as pyaudio"),
        ("pyaudio", "import pyaudio")
    ]
    
    success_count = 0
    for module_name, import_stmt in windows_modules:
        try:
            exec(import_stmt)
            print(f"✅ {module_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    print(f"\nWindows audio modules: {success_count}/{len(windows_modules)} successful")
    return success_count > 0

def test_transcriber_windows():
    """Test transcriber specifically on Windows"""
    print("\n📝 Testing Transcriber on Windows:")
    print("-" * 40)
    
    if sys.platform != "win32":
        print("⚠️  Not running on Windows - skipping Windows-specific tests")
        return True
    
    try:
        from transcriber import MeetingTranscriber
        print("✅ MeetingTranscriber imported successfully")
        
        # Try to create instance
        transcriber = MeetingTranscriber()
        print("✅ MeetingTranscriber instance created")
        
        # Try to test diarization (this will likely fail on Windows)
        try:
            # This is where the torchaudio error usually occurs
            result = transcriber._diarize_audio()
            if result:
                print("✅ Diarization works!")
                return True
            else:
                print("⚠️  Diarization returned None (expected on Windows)")
                return False
        except Exception as e:
            print(f"❌ Diarization failed: {e}")
            print("This is the expected Windows torchaudio error")
            return False
            
    except Exception as e:
        print(f"❌ MeetingTranscriber error: {e}")
        return False

def main():
    """Run Windows-specific tests"""
    print("🪟 Windows Compatibility Test for Meeting Agent")
    print("=" * 50)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 50)
    
    if sys.platform != "win32":
        print("⚠️  This test is designed for Windows. Current platform:", sys.platform)
        print("Run test_imports.py for general compatibility testing.")
        return
    
    # Run Windows-specific tests
    tests = [
        ("Windows Audio Modules", test_windows_audio_modules),
        ("TorchAudio Windows", test_torchaudio_windows),
        ("PyAnnote Windows", test_pyannote_windows),
        ("Transcriber Windows", test_transcriber_windows)
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
    print("\n📊 Windows Test Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Windows tests passed!")
    else:
        print("⚠️  Some Windows tests failed.")
        print("\nCommon Windows fixes:")
        print("- Install pyaudiowpatch: pip install pyaudiowpatch")
        print("- Update torchaudio: pip install --upgrade torchaudio")
        print("- Use fallback diarization for Windows")
        print("- Check Windows audio drivers and WASAPI support")

if __name__ == "__main__":
    main()
