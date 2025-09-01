#!/bin/bash
echo "Setting up EscapeRoom Assistant..."

# Check if Python 3.11+ is available
python3 --version | grep -E "3\.(1[1-9]|[2-9][0-9])" > /dev/null
if [ $? -ne 0 ]; then
    echo "Error: Python 3.11+ is required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if pyaudio installation succeeded (common issue on macOS)
python -c "import pyaudio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Audio installation failed. Installing with Homebrew..."
    brew install portaudio
    pip install pyaudio
fi

echo "Setup complete!"
echo "To run: source venv/bin/activate && python escape_ai.py"