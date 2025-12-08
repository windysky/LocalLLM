"""Model manager for loading and running LLM models."""

import logging
import subprocess
import json
import time
from typing import Dict, Optional, List, Any
from pathlib import Path
from .downloader import ModelDownloader
from .config import config

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model loading, unloading, and inference."""

    def __init__(self):
        self.downloader = ModelDownloader(config.models.storage_dir)
        self.loaded_models: Dict[str, Any] = {}
        self.ollama_models: Dict[str, str] = {}  # Map model name to Ollama model ID
        self.max_models = config.models.max_loaded_models

    def _ensure_ollama(self):
        """Ensure Ollama is installed and running."""
        try:
            # Check if Ollama is installed
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.error("Ollama not found. Please install Ollama first: https://ollama.ai")
                return False

            # Check if Ollama server is running
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Ollama command timed out")
            return False
        except FileNotFoundError:
            logger.error("Ollama not found. Please install Ollama first: https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama: {e}")
            return False

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models (downloaded + in registry)."""
        models = []

        # List downloaded models
        for model_info in self.downloader.list_downloaded_models():
            model_info["status"] = "downloaded"
            models.append(model_info)

        # List models in registry but not downloaded
        for model_name in self.downloader.list_available_models():
            if not any(m["name"] == model_name for m in models):
                models.append({
                    "name": model_name,
                    "status": "not_downloaded",
                    "type": self.downloader.MODEL_REGISTRY[model_name]["type"]
                })

        return models

    def download_model(self, model_name: str) -> bool:
        """Download a model if not already present."""
        if model_name not in self.downloader.MODEL_REGISTRY:
            logger.error(f"Unknown model: {model_name}")
            return False

        return self.downloader.download_model(model_name)

    def load_model(self, model_name: str) -> bool:
        """Load a model for inference using Ollama."""
        if model_name not in self.downloaded_models:
            logger.error(f"Model {model_name} not downloaded")
            return False

        if model_name in self.loaded_models:
            logger.info(f"Model {model_name} already loaded")
            return True

        if len(self.loaded_models) >= self.max_models:
            # Unload the oldest model
            oldest_model = next(iter(self.loaded_models))
            self.unload_model(oldest_model)

        # Ensure Ollama is available
        if not self._ensure_ollama():
            return False

        try:
            model_path = self.downloader.get_model_path(model_name)
            ollama_model_name = f"locallm-{model_name}"

            # Check if model already exists in Ollama
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )

            model_exists = False
            if result.returncode == 0:
                # Parse the output to check if model exists
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and ollama_model_name in line:
                        model_exists = True
                        break

            # Create or pull the model in Ollama
            if not model_exists:
                logger.info(f"Creating Ollama model {ollama_model_name} from {model_path}")

                # Create Modelfile
                modelfile_path = model_path / "Modelfile"
                with open(modelfile_path, "w") as f:
                    # Determine the base model for Ollama
                    if "gemma" in model_name.lower():
                        base_model = "gemma2"
                    elif "qwen" in model_name.lower():
                        base_model = "qwen2.5"
                    elif "llama" in model_name.lower():
                        base_model = "llama3.1"
                    elif "mistral" in model_name.lower():
                        base_model = "mistral"
                    else:
                        base_model = "llama3.1"  # Default fallback

                    f.write(f"FROM {base_model}\n")
                    # Add model-specific parameters
                    f.write(f"PARAMETER temperature {config.inference.temperature}\n")
                    f.write(f"PARAMETER num_ctx {config.inference.context_size}\n")
                    f.write(f"PARAMETER num_predict {config.inference.max_tokens}\n")

                # Create model using Modelfile
                result = subprocess.run(
                    ["ollama", "create", ollama_model_name, "-f", str(modelfile_path)],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if result.returncode != 0:
                    logger.error(f"Failed to create Ollama model: {result.stderr}")
                    return False

            # Test the model
            test_result = subprocess.run(
                ["ollama", "run", ollama_model_name, "test"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if test_result.returncode == 0:
                self.loaded_models[model_name] = {
                    "ollama_name": ollama_model_name,
                    "path": str(model_path),
                    "load_time": time.time()
                }
                self.ollama_models[model_name] = ollama_model_name
                logger.info(f"Successfully loaded model {model_name}")
                return True
            else:
                logger.error(f"Model test failed: {test_result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Loading model timed out")
            return False
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False

    def unload_model(self, model_name: str) -> bool:
        """Unload a model from memory."""
        if model_name not in self.loaded_models:
            logger.warning(f"Model {model_name} not loaded")
            return False

        try:
            # Remove from Ollama
            if model_name in self.ollama_models:
                ollama_model_name = self.ollama_models[model_name]
                subprocess.run(
                    ["ollama", "rm", ollama_model_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                del self.ollama_models[model_name]

            del self.loaded_models[model_name]
            logger.info(f"Successfully unloaded model {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
            return False

    def generate(self, model_name: str, prompt: str, **kwargs) -> Optional[str]:
        """Generate text using a loaded model."""
        if model_name not in self.loaded_models:
            logger.error(f"Model {model_name} not loaded")
            return None

        try:
            ollama_model_name = self.loaded_models[model_name]["ollama_name"]

            # Build command
            cmd = ["ollama", "run", ollama_model_name, prompt]

            # Add parameters if provided
            params = []
            if "temperature" in kwargs:
                params.extend(["--temperature", str(kwargs["temperature"])])
            if "max_tokens" in kwargs:
                params.extend(["--num-predict", str(kwargs["max_tokens"])])
            if "context_size" in kwargs:
                params.extend(["--num-ctx", str(kwargs["context_size"])])

            if params:
                cmd = ["ollama", "run"] + params + [ollama_model_name, prompt]

            # Run inference
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Generation failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Generation timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None

    def chat_completion(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> Optional[Dict[str, Any]]:
        """Generate a chat completion using the model."""
        if model_name not in self.loaded_models:
            logger.error(f"Model {model_name} not loaded")
            return None

        try:
            ollama_model_name = self.loaded_models[model_name]["ollama_name"]

            # Format messages into a single prompt
            formatted_prompt = self._format_messages(messages)

            # Generate response
            response_text = self.generate(model_name, formatted_prompt, **kwargs)

            if response_text:
                # Return OpenAI-compatible response
                return {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": self._estimate_tokens(formatted_prompt),
                        "completion_tokens": self._estimate_tokens(response_text),
                        "total_tokens": self._estimate_tokens(formatted_prompt) + self._estimate_tokens(response_text)
                    }
                }
            return None

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return None

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a single prompt."""
        formatted = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"Human: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")

        formatted.append("Assistant: ")
        return "\n".join(formatted)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (approximately 4 characters per token)."""
        return max(1, len(text) // 4)

    def get_loaded_models(self) -> List[Dict[str, Any]]:
        """Get information about currently loaded models."""
        models = []
        for model_name, info in self.loaded_models.items():
            models.append({
                "name": model_name,
                "ollama_name": info["ollama_name"],
                "path": info["path"],
                "load_time": info["load_time"]
            })
        return models

    @property
    def downloaded_models(self) -> Dict[str, Any]:
        """Get dictionary of downloaded models."""
        return {m["name"]: m for m in self.downloader.list_downloaded_models()}