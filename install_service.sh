#!/bin/bash
echo "Installing EscapeRoom AI Assistant as a background service..."

# Install dependencies first
./setup.sh

# Copy the launch agent to the correct location
cp com.escaperoom.ai.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.escaperoom.ai.plist

echo "✅ Service installed and started!"
echo "The EscapeRoom AI Assistant will now start automatically when you log in."
echo ""
echo "Commands:"
echo "  - Start service: launchctl start com.escaperoom.ai"
echo "  - Stop service:  launchctl stop com.escaperoom.ai"
echo "  - Uninstall:     ./uninstall_service.sh"
echo ""
echo "Logs are saved to:"
echo "  - Output: $(pwd)/escape_ai.log"
echo "  - Errors: $(pwd)/escape_ai_error.log"