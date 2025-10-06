#!/usr/bin/env python3
"""
Setup script for meeting-transcriber
"""

from setuptools import setup, find_packages

setup(
    name="meeting-transcriber",
    version="1.0.0",
    description="A lightweight CLI tool for recording and transcribing meetings offline",
    author="Meeting Transcriber",
    py_modules=["cli", "recorder", "transcriber", "config"],
    install_requires=[
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pyannote.audio>=3.1.0",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "librosa>=0.10.0",
    ],
    entry_points={
        "console_scripts": [
            "meeting-transcriber=cli:main",
        ],
    },
    python_requires=">=3.10",
)
