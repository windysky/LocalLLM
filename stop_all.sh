#!/bin/bash

# Stop only LocalLLM services (preserves other applications)

echo "🛑 Stopping LocalLLM Services..."
echo "================================"

# Stop using PIDs if files exist
if [ -f locallm_api.pid ]; then
    API_PID=$(cat locallm_api.pid)
    echo "Stopping LocalLLM API server (PID: $API_PID)..."
    kill $API_PID 2>/dev/null
    rm -f locallm_api.pid
fi

if [ -f locallm_web.pid ]; then
    WEB_PID=$(cat locallm_web.pid)
    echo "Stopping LocalLLM web interface (PID: $WEB_PID)..."
    kill $WEB_PID 2>/dev/null
    rm -f locallm_web.pid
fi

# Only stop processes with exact path matches to avoid affecting other apps
echo "Cleaning up LocalLLM processes..."

# Stop LocalLLM API server (exact match)
pkill -f "/home/juhur/PROJECTS/LocalLLM/cli/start_server.py" 2>/dev/null

# Stop LocalLLM web interface (exact match)
pkill -f "/home/juhur/PROJECTS/LocalLLM/web/app.py" 2>/dev/null

# Check if port 8000 is still in use by LocalLLM
if lsof -ti:8000 | xargs ps -p | grep -q "cli/start_server.py" 2>/dev/null; then
    echo "Force stopping LocalLLM on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
fi

# Check if port 8080 is still in use by LocalLLM
if lsof -ti:8080 | xargs ps -p | grep -q "web/app.py" 2>/dev/null; then
    echo "Force stopping LocalLLM on port 8080..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null
fi

echo "✅ LocalLLM services stopped!"
echo "Note: Other applications (including port 5000) are preserved"