@echo off
echo Building Windows application...

call venv\Scripts\activate
pip install pyinstaller

pyinstaller --onefile --windowed ^
    --name "EscapeRoom Assistant" ^
    --add-data "puzzles.csv;." ^
    --add-data ".env;." ^
    --add-data "templates;templates" ^
    --hidden-import=pandas ^
    --hidden-import=google.generativeai ^
    --hidden-import=flask ^
    --hidden-import=speech_recognition ^
    --hidden-import=pyaudio ^
    --hidden-import=dotenv ^
    app_launcher.py

echo Windows app built in dist\ folder
pause