"""FastAPI server for LocalLLM."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .model_manager import ModelManager
from .models import (
    ChatCompletionRequest, ChatCompletionResponse,
    CompletionRequest, CompletionResponse,
    ModelsResponse, ModelInfo,
    LoadModelRequest, UnloadModelRequest,
    DownloadModelRequest, ErrorResponse
)
from .config import Config, config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.logging.file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global model manager
model_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global model_manager
    logger.info("Starting LocalLLM server...")

    # Initialize model manager
    model_manager = ModelManager()

    # Load default model if specified
    if config.models.default_model:
        logger.info(f"Loading default model: {config.models.default_model}")
        if model_manager.download_model(config.models.default_model):
            if model_manager.load_model(config.models.default_model):
                logger.info("Default model loaded successfully")
            else:
                logger.warning("Failed to load default model")
        else:
            logger.warning("Failed to download default model")

    logger.info("LocalLLM server started successfully")
    yield

    logger.info("Shutting down LocalLLM server...")
    # Unload all models
    loaded_models = list(model_manager.loaded_models.keys())
    for model_name in loaded_models:
        model_manager.unload_model(model_name)
    logger.info("LocalLLM server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="LocalLLM API",
    description="OpenAI-compatible API for running local language models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
if config.api.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error={"type": "http_error", "code": exc.status_code},
            message=exc.detail,
            type="http_error"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error={"type": "internal_error", "code": 500},
            message="Internal server error",
            type="internal_error"
        ).dict()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LocalLLM API Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "completions": "/v1/completions",
            "models": "/v1/models",
            "load_model": "/models/load",
            "unload_model": "/models/unload",
            "download_model": "/models/download",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "models_loaded": len(model_manager.loaded_models) if model_manager else 0
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """Create a chat completion."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    # Check if model is loaded
    if request.model not in model_manager.loaded_models:
        # Try to download and load the model
        if config.models.auto_download:
            logger.info(f"Model {request.model} not loaded, attempting to download and load...")
            if not model_manager.download_model(request.model):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model {request.model} not found and could not be downloaded"
                )
            if not model_manager.load_model(request.model):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load model {request.model}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {request.model} not loaded"
            )

    # Convert messages to dict format
    messages = [msg.dict() for msg in request.messages]

    # Generate response
    response = model_manager.chat_completion(
        request.model,
        messages,
        temperature=request.temperature or config.inference.temperature,
        max_tokens=request.max_tokens or config.inference.max_tokens,
        context_size=config.inference.context_size
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )

    return response


@app.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Create a text completion."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    # Check if model is loaded
    if request.model not in model_manager.loaded_models:
        if config.models.auto_download:
            logger.info(f"Model {request.model} not loaded, attempting to download and load...")
            if not model_manager.download_model(request.model):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model {request.model} not found and could not be downloaded"
                )
            if not model_manager.load_model(request.model):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load model {request.model}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {request.model} not loaded"
            )

    # Generate response
    response_text = model_manager.generate(
        request.model,
        request.prompt,
        temperature=request.temperature or config.inference.temperature,
        max_tokens=request.max_tokens or config.inference.max_tokens,
        context_size=config.inference.context_size
    )

    if not response_text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )

    # Create OpenAI-compatible response
    return CompletionResponse(
        id=f"cmpl-{int(time.time())}",
        created=int(time.time()),
        model=request.model,
        choices=[
            {
                "index": 0,
                "text": response_text,
                "finish_reason": "stop"
            }
        ],
        usage={
            "prompt_tokens": len(request.prompt) // 4,  # Rough estimate
            "completion_tokens": len(response_text) // 4,
            "total_tokens": (len(request.prompt) + len(response_text)) // 4
        }
    )


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    models = []
    for model_info in model_manager.list_available_models():
        models.append(
            ModelInfo(
                id=model_info["name"],
                created=int(time.time()),
                owned_by="local"
            )
        )

    return ModelsResponse(data=models)


@app.post("/models/load")
async def load_model(request: LoadModelRequest):
    """Load a model."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    # Check if model is downloaded
    if request.model not in model_manager.downloaded_models:
        if config.models.auto_download:
            logger.info(f"Model {request.model} not downloaded, downloading...")
            if not model_manager.download_model(request.model):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model {request.model} not found and could not be downloaded"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {request.model} not downloaded"
            )

    # Load the model
    if model_manager.load_model(request.model):
        return {"message": f"Model {request.model} loaded successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model {request.model}"
        )


@app.post("/models/unload")
async def unload_model(request: UnloadModelRequest):
    """Unload a model."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    if request.model:
        # Unload specific model
        if request.model in model_manager.loaded_models:
            if model_manager.unload_model(request.model):
                return {"message": f"Model {request.model} unloaded successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to unload model {request.model}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {request.model} not loaded"
            )
    else:
        # Unload all models
        loaded_models = list(model_manager.loaded_models.keys())
        for model_name in loaded_models:
            model_manager.unload_model(model_name)
        return {"message": f"Unloaded {len(loaded_models)} models"}


@app.delete("/models/{model_name}")
async def remove_model(model_name: str):
    """Remove a downloaded model from disk."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    try:
        logger.info(f"Removing model {model_name}...")

        # First unload the model if it's loaded
        if model_name in model_manager.loaded_models:
            logger.info(f"Unloading model {model_name} before removal...")
            model_manager.unload_model(model_name)

        # Remove the model from disk
        success = model_manager.downloader.remove_model(model_name)
        if success:
            logger.info(f"Model {model_name} removed successfully")
            return {"message": f"Model {model_name} removed successfully"}
        else:
            logger.error(f"Failed to remove model {model_name}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove model {model_name}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/models/download/{model_name}/progress")
async def get_download_progress(model_name: str):
    """Get download progress for a model."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    try:
        # Get progress from downloader
        progress = model_manager.downloader.get_download_progress(model_name)
        logger.info(f"Progress endpoint called for {model_name}, returning: {progress}")
        return JSONResponse(content=progress)
    except Exception as e:
        logger.error(f"Error getting progress for {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/models/download")
async def download_model(request: DownloadModelRequest):
    """Download a model."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    # Check if already downloaded
    if request.model in model_manager.downloaded_models:
        return {"message": f"Model {request.model} already downloaded"}

    # Download the model
    if model_manager.download_model(request.model):
        return {"message": f"Model {request.model} downloaded successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download model {request.model}"
        )


@app.get("/models/status")
async def get_models_status():
    """Get status of all models."""
    global model_manager

    if not model_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model manager not initialized"
        )

    return {
        "available": model_manager.list_available_models(),
        "loaded": model_manager.get_loaded_models(),
        "downloaded": model_manager.downloaded_models
    }


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.server:app",
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers,
        log_level=config.logging.level.lower()
    )


if __name__ == "__main__":
    run_server()