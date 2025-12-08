# LocalLLM Usage Guide

## Prerequisites

1. **Install Ollama** (required for model inference):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### 1. Start the API Server

```bash
# Start the server with default settings
python cli/start_server.py

# Or specify custom port
python cli/start_server.py --port 8080

# Run in development mode
python cli/start_server.py --dev
```

The API server will be available at `http://localhost:8000`

### 2. Start the Web Interface

In another terminal:

```bash
python web/app.py
```

The web interface will be available at `http://localhost:8080`

## CLI Commands

### Manage Models

```bash
# List all available models
python cli/manage_models.py --list

# Download a model
python cli/manage_models.py --download gemma-2-9b

# Load a model
python cli/manage_models.py --load gemma-2-9b

# Show loaded models
python cli/manage_models.py --loaded

# Unload a model
python cli/manage_models.py --unload gemma-2-9b
```

### Server Control

```bash
# Start server
python cli/start_server.py --port 8000

# Stop server
python cli/stop_server.py

# Force stop (if stuck)
python cli/stop_server.py --force
```

## API Usage

### Chat Completions (OpenAI-Compatible)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-2-9b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### List Models

```bash
curl http://localhost:8000/v1/models
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Model Management via API

### Download a Model

```bash
curl -X POST http://localhost:8000/models/download \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma-2-9b"}'
```

### Load a Model

```bash
curl -X POST http://localhost:8000/models/load \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma-2-9b"}'
```

### Unload a Model

```bash
curl -X POST http://localhost:8000/models/unload \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma-2-9b"}'
```

## Supported Models

The system supports the following models:

| Model | Size | Type | Notes |
|-------|------|------|-------|
| gemma-2-9b | ~9B | Instruction | Google Gemma 2 |
| qwen2.5-7b | ~7B | Instruction | Alibaba Qwen |
| llama-3.1-8b | ~8B | Instruction | Meta Llama 3.1 |
| mistral-7b | ~7B | Instruction | Mistral AI |

## Configuration

### Using config.yaml

Edit `config.yaml` to customize settings:

```yaml
server:
  host: "0.0.0.0"
  port: 8000

models:
  storage_dir: "./models"
  auto_download: true
  max_loaded_models: 1

inference:
  device: "auto"  # auto, cpu, cuda, mps
  temperature: 0.7
  max_tokens: 1024
```

### Using Environment Variables

```bash
# Server settings
export DEFAULT_HOST=127.0.0.1
export DEFAULT_PORT=9000

# Model settings
export MODEL_DIR=/path/to/models
export DEVICE=cpu

# Logging
export LOG_LEVEL=DEBUG
```

## Web Interface Features

The web interface at `http://localhost:8080` provides:

- **Model Management**: View, download, load, and unload models
- **Chat Interface**: Test models through an OpenAI-compatible API
- **Real-time Status**: See which models are currently loaded
- **API Information**: View API endpoints and examples

## Troubleshooting

### Ollama Not Found

If you get an error about Ollama not being found:

1. Install Ollama: https://ollama.ai
2. Make sure the Ollama service is running: `ollama serve`

### Model Download Fails

For some models (like Llama), you need to:

1. Visit the model page on Hugging Face
2. Request access (may require approval)
3. Set up your Hugging Face token:

```bash
export HUGGINGFACE_TOKEN=your_token_here
```

### Memory Issues

If you're running out of memory:

1. Reduce `max_memory` in config.yaml
2. Unload models when not in use
3. Use smaller models (7B instead of 9B)

### Server Won't Start

Check the logs for errors:

```bash
# Check if server is already running
python cli/stop_server.py

# Start with debug logging
export LOG_LEVEL=DEBUG
python cli/start_server.py
```

## Examples

### Python Client

```python
import requests

# Chat completion
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "gemma-2-9b",
        "messages": [
            {"role": "user", "content": "Explain quantum computing"}
        ]
    }
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

### OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-required"  # No auth needed
)

response = client.chat.completions.create(
    model="gemma-2-9b",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_config.py
```

### Code Structure

```
LocalLLM/
├── src/           # Core application code
│   ├── config.py  # Configuration management
│   ├── server.py  # FastAPI server
│   ├── model_manager.py  # Model loading/inference
│   ├── downloader.py     # Model downloading
│   └── models.py    # Pydantic models
├── cli/           # Command-line tools
├── web/           # Web interface
├── tests/         # Test suite
└── config.yaml    # Configuration file
```