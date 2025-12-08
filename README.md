# LocalLLM

A Python-based service for running small to medium-sized language models locally with a simple web interface and REST API.

## Features

- 🚀 Easy model management via web UI or CLI
- 📦 Automatic model downloading from Hugging Face
- 🔌 OpenAI-compatible API endpoints
- 🌐 Simple web-based management interface
- ⚡ Optimized for 8B-20B parameter models
- 🔄 Start/stop service control
- 📱 No authentication required

## Supported Models

- Gemma-2-9B
- Qwen2.5-7B
- Llama-3.1-8B
- Mistral-7B
- And other models in the 8B-20B parameter range

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Start the service
python cli/start_server.py

# Open web interface
http://localhost:8080
```

## API Usage

```bash
# Chat completion (OpenAI-compatible)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-2-9b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Project Structure

```
LocalLLM/
├── src/           # Core application code
├── cli/           # Command-line tools
├── web/           # Web interface
├── models/        # Downloaded models
├── tests/         # Test suite
└── config.yaml    # Configuration file
```

## Requirements

- Python 3.8+
- 8GB+ RAM (for 8B models)
- 16GB+ recommended (for 20B models)
- Optional: CUDA-compatible GPU