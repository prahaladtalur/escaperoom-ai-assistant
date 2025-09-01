#!/bin/bash
echo "Building Mac application..."

source venv/bin/activate
pip install pyinstaller

pyinstaller --onefile --windowed \
    --name "EscapeRoom Assistant" \
    --add-data "puzzles.csv:." \
    --add-data ".env:." \
    --add-data "templates:templates" \
    --hidden-import=pandas \
    --hidden-import=google.generativeai \
    --hidden-import=flask \
    --hidden-import=speech_recognition \
    --hidden-import=pyaudio \
    --hidden-import=dotenv \
    app_launcher.py

echo "Mac app built in dist/ folder"