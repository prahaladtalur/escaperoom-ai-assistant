#!/usr/bin/env python3
import subprocess
import sys
import os

def build_windows():
    print("Building Windows application...")
    
    # Install PyInstaller if not already installed
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build command for Windows
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "EscapeRoom Assistant",
        "--add-data", "puzzles.csv;.",
        "--add-data", ".env;.",
        "--add-data", "templates;templates",
        "--hidden-import=pandas",
        "--hidden-import=google.generativeai",
        "--hidden-import=flask",
        "--hidden-import=speech_recognition",
        "--hidden-import=pyaudio",
        "--hidden-import=dotenv",
        "app_launcher.py"
    ]
    
    subprocess.run(cmd, check=True)
    print("Windows executable built in dist/ folder")

if __name__ == "__main__":
    build_windows()