#!/bin/bash
# Script to update JavaScript files in Docker container

echo "Updating files in Docker container 'smartcursor'..."

# Update auth.js
docker cp static/js/auth.js smartcursor:/app/static/js/auth.js
echo "✅ Updated auth.js"

# Update app.js
docker cp static/js/app.js smartcursor:/app/static/js/app.js
echo "✅ Updated app.js"

# Restart container to ensure changes take effect
echo "Restarting container..."
docker restart smartcursor

echo ""
echo "✅ All files updated! Container restarted."
echo "Please wait a few seconds for the container to start, then refresh your browser."

