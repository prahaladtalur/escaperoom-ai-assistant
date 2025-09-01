# EscapeRoom Assistant - Standalone Applications

## Mac Application (Ready!)

**Location:** `dist/EscapeRoom Assistant.app`

**How to use:**
1. Double-click `EscapeRoom Assistant.app` 
2. Browser opens automatically to the web interface
3. Type or use voice to describe puzzle problems

## Windows Application

**To build on Windows:**
1. Copy entire `puzzles` folder to Windows computer
2. Install Python 3.11+ on Windows
3. Open Command Prompt in the puzzles folder
4. Run: `python build_windows_simple.py`
5. Windows executable will be in `dist/` folder

**Or use the batch file:**
1. Double-click `build_windows.bat`
2. Executable will be created in `dist/` folder

## Distribution

**Mac:** Share the `EscapeRoom Assistant.app` file
**Windows:** Share the `.exe` file from the `dist/` folder

Both applications:
- Include all puzzle data
- Work offline (except for Gemini API calls)
- Open web browser automatically
- No installation required