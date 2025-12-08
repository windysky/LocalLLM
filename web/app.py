#!/usr/bin/env python3
"""Simple web interface for LocalLLM."""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional
import aiofiles
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import uvicorn

# Hugging Face search functionality
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.model_manager import ModelManager

# Initialize FastAPI app
app = FastAPI(title="LocalLLM Web Interface")

# Initialize model manager
model_manager = ModelManager()

# Setup templates
templates_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files (if any)
static_dir = templates_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Hugging Face search endpoint
@app.get("/api/search/huggingface")
async def search_huggingface(
    query: str,
    limit: int = 10,
    filter: Optional[str] = None
):
    """Search for models on Hugging Face"""

    try:
        # Hugging Face API URL
        HF_API_URL = "https://huggingface.co/api/models"

        # Build search parameters
        params = {
            "search": query,
            "limit": limit,
            "sort": "downloads",
            "direction": "-1"
        }

        # Add filters if specified
        if filter:
            if filter == "text-generation":
                params["library"] = "transformers"
                params["tags"] = "text-generation"
            elif filter == "gguf":
                params["tags"] = "gguf"

        # Make request to Hugging Face API
        response = requests.get(HF_API_URL, params=params, timeout=10)
        response.raise_for_status()

        models = response.json()

        # Format results
        formatted_models = []
        for model in models[:limit]:
            # Only include models with proper model cards
            if model.get("modelId") and model.get("downloads", 0) > 0:
                formatted_models.append({
                    "id": model["modelId"],
                    "author": model.get("author", ""),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "lastModified": model.get("lastModified", ""),
                    "tags": model.get("tags", []),
                    "pipeline_tag": model.get("pipeline_tag", ""),
                    "library_name": model.get("library_name", ""),
                    "description": (model.get("cardData", {}).get("text", "") or "")[:200] + "..." if model.get("cardData", {}).get("text") else "No description available"
                })

        return {
            "success": True,
            "models": formatted_models,
            "total": len(formatted_models)
        }

    except requests.RequestException as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to search Hugging Face: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Unexpected error: {str(e)}"}
        )


@app.get("/")
async def home(request: Request):
    """Home page - admin dashboard."""
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

@app.get("/simple")
async def simple_interface(request: Request):
    """Simple interface page."""
    # Get model status
    available_models = model_manager.list_available_models()
    loaded_models = model_manager.get_loaded_models()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "available_models": available_models,
            "loaded_models": loaded_models,
            "api_base": f"http://{config.server.host}:{config.server.port}"
        }
    )


@app.get("/api/models")
async def api_models():
    """API endpoint for models."""
    return {
        "available": model_manager.list_available_models(),
        "loaded": model_manager.get_loaded_models()
    }


@app.post("/api/models/{model_name}/download")
async def api_download_model(model_name: str):
    """API endpoint to download a model."""
    success = model_manager.download_model(model_name)
    if success:
        return {"success": True, "message": f"Model {model_name} download started"}
    else:
        return {"success": False, "message": f"Failed to download model {model_name}"}


@app.post("/api/models/{model_name}/load")
async def api_load_model(model_name: str):
    """API endpoint to load a model."""
    success = model_manager.load_model(model_name)
    if success:
        return {"success": True, "message": f"Model {model_name} loaded successfully"}
    else:
        return {"success": False, "message": f"Failed to load model {model_name}"}


@app.post("/api/models/{model_name}/unload")
async def api_unload_model(model_name: str):
    """API endpoint to unload a model."""
    success = model_manager.unload_model(model_name)
    if success:
        return {"success": True, "message": f"Model {model_name} unloaded successfully"}
    else:
        return {"success": False, "message": f"Failed to unload model {model_name}"}


@app.post("/api/settings/hf_token")
async def api_save_hf_token(request: Request):
    """API endpoint to save Hugging Face token to .env file."""
    try:
        data = await request.json()
        token = data.get("token")
        if not token:
            return {"success": False, "message": "No token provided"}

        # Get the project root (parent of web directory)
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"

        # Read existing .env file
        env_lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_lines = f.readlines()

        # Remove existing HUGGINGFACE_TOKEN line if present
        env_lines = [line for line in env_lines if not line.startswith("HUGGINGFACE_TOKEN=")]

        # Add the new token
        env_lines.append(f"HUGGINGFACE_TOKEN={token}\n")

        # Write back to .env file
        with open(env_file, 'w') as f:
            f.writelines(env_lines)

        # Set the environment variable for current process
        os.environ["HUGGINGFACE_TOKEN"] = token

        return {
            "success": True,
            "message": "Token saved successfully! Restart the server to apply changes."
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/settings/hf_token")
async def api_get_hf_token():
    """API endpoint to get current Hugging Face token (masked)."""
    try:
        # Get token from environment first
        token = os.environ.get("HUGGINGFACE_TOKEN")

        # If not in environment, check .env file
        if not token:
            project_root = Path(__file__).parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("HUGGINGFACE_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            break

        if token:
            # Mask the token for security
            masked = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
            return {"success": True, "token": masked, "has_token": True}
        else:
            return {"success": True, "has_token": False}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_web_server(host: str = None, port: int = None):
    """Run the web server."""
    host = host or config.web.host
    port = port or config.web.port

    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start LocalLLM web interface")
    parser.add_argument("--host", default=config.web.host, help="Web server host")
    parser.add_argument("--port", type=int, default=config.web.port, help="Web server port")

    args = parser.parse_args()

    run_web_server(args.host, args.port)