#!/bin/bash

# Start both LocalLLM API server and web interface

echo "🚀 Starting LocalLLM Services..."
echo "================================"

# Start API server in background
echo "Starting API server on port 8000..."
python cli/start_server.py > /tmp/locallm_api.log 2>&1 &
API_PID=$!
echo "API server PID: $API_PID"

# Wait a moment for API server to start
sleep 3

# Check if API server started successfully
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server started successfully"
else
    echo "❌ API server failed to start"
    tail -n 20 /tmp/locallm_api.log
    exit 1
fi

# Start web interface
echo "Starting web interface on port 8080..."
python web/app.py --port 8080 > /tmp/locallm_web.log 2>&1 &
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
echo "To stop all services:"
echo "  kill $API_PID $WEB_PID"
echo "  Or run: ./stop_all.sh"
echo ""
echo "To view logs:"
echo "  API:  tail -f /tmp/locallm_api.log"
echo "  Web:  tail -f /tmp/locallm_web.log"