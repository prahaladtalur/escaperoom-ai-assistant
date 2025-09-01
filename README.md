# EscapeRoom AI Assistant

A voice-activated puzzle hint system for escape rooms using AI-powered speech recognition and text-to-speech.

## Features

- **Voice Recognition**: Speak your puzzle questions naturally
- **AI Voice Responses**: High-quality OpenAI text-to-speech
- **Smart Puzzle Matching**: Uses Google Gemini AI to understand your queries
- **Sequential Hints**: Get one hint at a time to avoid spoilers
- **Web Interface**: Clean, modern chat interface
- **Session Management**: Tracks your progress per puzzle

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd puzzles
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   Create a `.env` file with:
   ```
   GOOGLE_API_KEY=your_google_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. **Run the application**
   ```bash
   python web_clean.py
   ```

Visit `http://127.0.0.1:5009` to use the web interface.

## API Keys Required

- **Google Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI API**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

## Files

- `web_clean.py` - Main web application with voice features
- `escape_ai.py` - Terminal-based voice assistant
- `puzzles.csv` - Puzzle database
- `templates/` - HTML templates (embedded in web_clean.py)

## Usage

1. Open the web interface
2. Click the microphone button or type your question
3. Ask about puzzles like: "I'm stuck on the mushroom puzzle in room 2"
4. Get one hint at a time - ask for more if needed
5. Toggle the 🔊 button to enable/disable AI voice responses