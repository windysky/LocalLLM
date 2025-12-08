# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LocalLLM is a Python-based service for running small to medium-sized language models locally (8B-20B parameter range). The project provides:

- Local LLM inference server with REST API
- Web-based management interface for model management
- Automatic model downloading from Hugging Face
- Support for models like Gemma-2-9B, Qwen2.5-7B, Llama-3.1-8B, and similar sized models
- Easy start/stop controls via CLI or web interface

## Core Architecture

The project is structured around these main components:

### Backend Services (`/src`)
- `server.py` - Main FastAPI application serving REST endpoints
- `model_manager.py` - Handles model loading, unloading, and inference
- `downloader.py` - Manages automatic model downloads from Hugging Face
- `config.py` - Configuration management and settings

### Model Storage (`/models`)
- Downloaded models are stored here by default
- Organized by model name/version

### Web Interface (`/web`)
- Simple HTML/CSS/JS frontend for model management
- No authentication required (as specified)

### CLI Tools (`/cli`)
- `start_server.py` - Start the LLM service
- `stop_server.py` - Stop the running service
- `manage_models.py` - List, download, or remove models

## Key Technologies

- **Ollama integration** - Primary backend for model inference
- **FastAPI** - REST API framework
- **Hugging Face Hub** - Model repository
- **Transformers & Accelerate** - Model loading and inference
- **uvicorn** - ASGI server

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start the LLM service (CLI)
python cli/start_server.py --port 8000

# Stop the service
python cli/stop_server.py

# Download a model manually
python cli/manage_models.py --download gemma-2-9b

# List available models
python cli/manage_models.py --list

# Run with specific model
python cli/start_server.py --model llama-3.1-8b

# Start web interface only
python web/app.py --port 8080
```

## API Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `POST /v1/completions` - Text completions
- `GET /v1/models` - List loaded models
- `POST /models/load` - Load a specific model
- `POST /models/unload` - Unload a model
- `GET /health` - Health check

## Configuration

Configuration is managed through:
1. Command-line arguments
2. Environment variables
3. `.env` file in project root
4. `config.yaml` for persistent settings

Key settings:
- `MODEL_DIR` - Directory to store downloaded models (default: ./models)
- `DEFAULT_HOST` - Server host (default: 0.0.0.0)
- `DEFAULT_PORT` - Server port (default: 8000)
- `MAX_MEMORY` - Maximum memory allocation for models
- `DEVICE` - Inference device (cpu/cuda/mps)

## Model Compatibility

The system supports models in these formats:
- GGUF (recommended for CPU inference)
- Safetensors
- PyTorch bin files

Popular tested models:
- `gemma-2-9b-it`
- `qwen2.5-7b-instruct`
- `llama-3.1-8b-instruct`
- `mistral-7b-instruct-v0.3`

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=src tests/

# Test API endpoints manually
python tests/test_api_endpoints.py
```

## Important Implementation Notes

1. **Model Downloading**: Models are auto-downloaded on first request if not present
2. **Memory Management**: Only one model loaded at a time by default (configurable)
3. **Web Interface**: Simple static HTML/JS, no build process required
4. **No Authentication**: As specified, the system runs without auth
5. **Process Management**: Uses PID files for service start/stop operations

## Development Setup

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests to verify setup: `pytest`
6. Start development server: `python cli/start_server.py --dev`