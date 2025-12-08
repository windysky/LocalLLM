#!/bin/bash

# Check what's running on different ports to ensure safety

echo "🔍 Port Status Check"
echo "===================="

# Check port 5000 (your other app)
if lsof -i:5000 > /dev/null 2>&1; then
    echo "✅ Port 5000: In use (your application - will NOT be affected)"
else
    echo "ℹ️  Port 5000: Not in use"
fi

# Check port 8000 (LocalLLM API)
if lsof -i:8000 > /dev/null 2>&1; then
    echo "✅ Port 8000: In use (LocalLLM API)"
else
    echo "ℹ️  Port 8000: Available for LocalLLM API"
fi

# Check port 8080 (LocalLLM Web)
if lsof -i:8080 > /dev/null 2>&1; then
    echo "✅ Port 8080: In use (LocalLLM Web Interface)"
else
    echo "ℹ️  Port 8080: Available for LocalLLM Web"
fi

# Check port 11434 (Ollama)
if lsof -i:11434 > /dev/null 2>&1; then
    echo "✅ Port 11434: In use (Ollama)"
else
    echo "ℹ️  Port 11434: Available for Ollama"
fi

echo ""
echo "LocalLLM uses ports: 8000 (API), 8080 (Web), 11434 (Ollama)"
echo "Your application uses port: 5000 (WILL NOT BE AFFECTED)"