#!/bin/bash
# Master launcher for LocalLLM (Ollama daemon, API server, Web UI)

set -e

echo "🚀 Starting LocalLLM Services..."
echo "================================"

# Load .env if present
if [ -f .env ]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

# Start Ollama daemon if not reachable
echo "Checking Ollama daemon..."
if ! command -v ollama >/dev/null 2>&1; then
  echo "❌ Ollama CLI not found. Install from https://ollama.ai and retry."
  exit 1
fi
if ! ollama list >/dev/null 2>&1; then
  echo "Starting Ollama daemon..."
  ollama serve > /tmp/ollama.log 2>&1 &
  OLLAMA_PID=$!
  echo "Ollama PID: $OLLAMA_PID"
  # Give it a moment to boot
  sleep 3
  if ! ollama list >/dev/null 2>&1; then
    echo "❌ Ollama daemon failed to start (see /tmp/ollama.log)"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
  fi
  echo "$OLLAMA_PID" > locallm_ollama.pid
else
  echo "✅ Ollama daemon reachable"
fi

# Start API server in background
echo "Starting API server on port 8000..."
/home/juhur/miniconda3/envs/locallm/bin/python cli/start_server.py > /tmp/locallm_api.log 2>&1 &
API_PID=$!
echo "API server PID: $API_PID"
# Wait for API server to start (up to 30s)
echo "Waiting for API server health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API server started successfully"
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ API server failed to start after waiting"
    tail -n 40 /tmp/locallm_api.log
    [ -n "$OLLAMA_PID" ] && kill "$OLLAMA_PID" 2>/dev/null
    exit 1
fi
# Start web interface
echo "Starting web interface on port 8080..."
/home/juhur/miniconda3/envs/locallm/bin/python web/app.py --port 8080 > /tmp/locallm_web.log 2>&1 &
WEB_PID=$!
echo "Web interface PID: $WEB_PID"

# Create PID file for easy cleanup
echo "$API_PID" > locallm_api.pid
echo "$WEB_PID" > locallm_web.pid

echo ""
echo "✅ All services started!"
echo "========================"
echo "📊 Admin Dashboard: http://localhost:8080"
echo "🔌 API Endpoints:   http://localhost:8000"
echo ""
echo "To stop all services: ./stop_all.sh"
echo ""
echo "To view logs:"
echo "  Ollama: tail -f /tmp/ollama.log"
echo "  API:    tail -f /tmp/locallm_api.log"
echo "  Web:    tail -f /tmp/locallm_web.log"
