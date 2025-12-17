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

# Stop Ollama only if we started it
if [ -f locallm_ollama.pid ]; then
    OLLAMA_PID=$(cat locallm_ollama.pid)
    echo "Stopping Ollama daemon started by this script (PID: $OLLAMA_PID)..."
    kill $OLLAMA_PID 2>/dev/null
    rm -f locallm_ollama.pid
fi

# Only stop processes with exact path matches to avoid affecting other apps
echo "Cleaning up LocalLLM processes..."

# Stop LocalLLM API server (match by script name)
pkill -f "cli/start_server.py" 2>/dev/null

# Stop LocalLLM web interface (match by script name)
pkill -f "web/app.py" 2>/dev/null

# Check if port 8000 is still in use by LocalLLM
API_PORT_PIDS=$(lsof -ti:8000 2>/dev/null | tr '\n' ' ')
if [ -n "$API_PORT_PIDS" ]; then
    if echo "$API_PORT_PIDS" | xargs -r ps -p 2>/dev/null | grep -q "cli/start_server.py"; then
        echo "Force stopping LocalLLM on port 8000..."
        echo "$API_PORT_PIDS" | xargs -r kill -9 2>/dev/null
    fi
fi

# Check if port 8080 is still in use by LocalLLM
WEB_PORT_PIDS=$(lsof -ti:8080 2>/dev/null | tr '\n' ' ')
if [ -n "$WEB_PORT_PIDS" ]; then
    if echo "$WEB_PORT_PIDS" | xargs -r ps -p 2>/dev/null | grep -q "web/app.py"; then
        echo "Force stopping LocalLLM on port 8080..."
        echo "$WEB_PORT_PIDS" | xargs -r kill -9 2>/dev/null
    fi
fi

# Optionally stop Ollama on its default port if we started it (best-effort, guarded above)
if [ -f locallm_ollama.pid ]; then
    OLLAMA_PORT_PIDS=$(lsof -ti:11434 2>/dev/null | tr '\n' ' ')
    if [ -n "$OLLAMA_PORT_PIDS" ]; then
        echo "$OLLAMA_PORT_PIDS" | xargs -r kill -9 2>/dev/null
    fi
fi

echo "✅ LocalLLM services stopped!"
echo "Note: Other applications (including port 5000) are preserved"
