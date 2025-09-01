#!/bin/bash
echo "Uninstalling EscapeRoom AI Assistant service..."

# Stop and unload the service
launchctl stop com.escaperoom.ai 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.escaperoom.ai.plist 2>/dev/null

# Remove the launch agent file
rm -f ~/Library/LaunchAgents/com.escaperoom.ai.plist

echo "✅ Service uninstalled successfully!"
echo "The EscapeRoom AI Assistant will no longer start automatically."