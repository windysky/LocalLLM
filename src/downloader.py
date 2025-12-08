"""Model downloader from Hugging Face."""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Any
import requests
from tqdm import tqdm
from huggingface_hub import hf_hub_download, snapshot_download, model_info, HfFolder
from huggingface_hub.utils import HfHubHTTPError
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Get project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        # Set token for HfFolder if available
        hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        if hf_token:
            HfFolder.save_token(hf_token)
            logger.info("Hugging Face token loaded from environment")
except ImportError:
    pass
except Exception as e:
    logger.warning(f"Failed to load Hugging Face token from .env: {e}")


class ModelDownloader:
    """Handles downloading models from Hugging Face."""

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.download_progress = {}  # Track download progress

    # Popular model configurations
    MODEL_REGISTRY = {
        "gemma-2-9b": {
            "repo_id": "google/gemma-2-9b-it",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Google Gemma 2 - 9B parameters",
            "ollama_base": "gemma2:9b"
        },
        "gemma-2-9b-it": {
            "repo_id": "google/gemma-2-9b-it",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Google Gemma 2 Instruct - 9B parameters",
            "ollama_base": "gemma2:9b"
        },
        "qwen2.5-7b": {
            "repo_id": "Qwen/Qwen2.5-7B-Instruct",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Alibaba Qwen 2.5 - 7B parameters",
            "ollama_base": "qwen2.5:7b"
        },
        "qwen2.5-7b-instruct": {
            "repo_id": "Qwen/Qwen2.5-7B-Instruct",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Alibaba Qwen 2.5 Instruct - 7B parameters",
            "ollama_base": "qwen2.5:7b-instruct"
        },
        "llama-3.1-8b": {
            "repo_id": "meta-llama/Llama-3.1-8B",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Meta Llama 3.1 - 8B parameters (requires HF access)",
            "ollama_base": "llama3.1:8b"
        },
        "llama-3.1-8b-instruct": {
            "repo_id": "meta-llama/Llama-3.1-8B-Instruct",
            "files": [
                "model-00001-of-00004.safetensors",
                "model-00002-of-00004.safetensors",
                "model-00003-of-00004.safetensors",
                "model-00004-of-00004.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Meta Llama 3.1 Instruct - 8B parameters (requires HF access)",
            "ollama_base": "llama3.1:8b-instruct"
        },
        "mistral-7b": {
            "repo_id": "mistralai/Mistral-7B-Instruct-v0.3",
            "files": [
                "model-00001-of-00003.safetensors",
                "model-00002-of-00003.safetensors",
                "model-00003-of-00003.safetensors",
                "model.safetensors.index.json",
                "config.json",
                "tokenizer.json"
            ],
            "type": "safetensors",
            "description": "Mistral 7B Instruct - 7B parameters",
            "ollama_base": "mistral:7b-instruct"
        },
        "phi-3-mini": {
            "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
            "files": ["phi-3-mini-4k-instruct.q4.gguf"],
            "type": "gguf",
            "description": "Microsoft Phi-3 Mini - 3.8B parameters (GGUF format)",
            "ollama_base": "phi3:mini"
        },
    }


    def list_available_models(self) -> List[str]:
        """List all available models in the registry."""
        return list(self.MODEL_REGISTRY.keys())

    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        model_dir = self.storage_dir / model_name
        if not model_dir.exists():
            return False

        # Check for key files
        if model_name in self.MODEL_REGISTRY:
            config = self.MODEL_REGISTRY[model_name]
            for file in config["files"]:
                if not (model_dir / file).exists():
                    return False
        return True

    def get_download_progress(self, model_name: str) -> dict:
        """Get the current download progress for a model."""
        return self.download_progress.get(model_name, {"status": "not_started", "progress": 0})

    def set_download_progress(self, model_name: str, status: str, progress: int = 0, message: str = ""):
        """Set the download progress for a model."""
        self.download_progress[model_name] = {
            "status": status,
            "progress": progress,
            "message": message
        }
        logger.info(f"Progress set for {model_name}: status={status}, progress={progress}%, message={message}")

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get the local path to a downloaded model."""
        # First try the base model name
        if self.is_model_downloaded(model_name):
            return self.storage_dir / model_name

        # If not found, look for format-suffixed versions
        for suffix in ["-gguf", "-safetensors", "-pytorch"]:
            format_dir = self.storage_dir / f"{model_name}{suffix}"
            if format_dir.exists() and any(format_dir.rglob("*")):
                return format_dir

        # If still not found, try to find any directory that looks like this model
        for model_dir in self.storage_dir.iterdir():
            if not model_dir.is_dir():
                continue

            dir_name = model_dir.name
            # Check if this is a format-suffixed version of the model
            for suffix in ["-gguf", "-safetensors", "-pytorch"]:
                if dir_name.endswith(suffix):
                    base_name = dir_name[:-len(suffix)]
                    if base_name == model_name and any(model_dir.rglob("*")):
                        return model_dir

        return None

    def download_model(self, model_name: str, format_type="safetensors", progress_callback=None) -> bool:
        """Download a model from Hugging Face."""
        if model_name not in self.MODEL_REGISTRY:
            logger.error(f"Model {model_name} not found in registry")
            return False

        # Check if model with this format is already downloaded
        format_suffix = f"-{format_type}" if format_type != self.MODEL_REGISTRY[model_name].get("type", "safetensors") else ""
        model_key = f"{model_name}{format_suffix}"

        if self.is_model_downloaded(model_key):
            logger.info(f"Model {model_name} ({format_type}) already downloaded")
            return True

        model_config = self.MODEL_REGISTRY[model_name]
        model_dir = self.storage_dir / model_key
        model_dir.mkdir(exist_ok=True)

        # For GGUF format, use different repository and files
        if format_type == "gguf":
            # Define GGUF repositories for models that have them
            gguf_repos = {
                "gemma-2-9b": "bartowski/gemma-2-9b-it-GGUF",
                "gemma-2-9b-it": "bartowski/gemma-2-9b-it-GGUF",
                "llama-3.1-8b": "bartowski/Llama-3.1-8B-Instruct-GGUF",
                "llama-3.1-8b-instruct": "bartowski/Llama-3.1-8B-Instruct-GGUF",
                "qwen2.5-7b": "bartowski/Qwen2.5-7B-Instruct-GGUF",
                "qwen2.5-7b-instruct": "bartowski/Qwen2.5-7B-Instruct-GGUF",
                "mistral-7b": "TheBloke/Mistral-7B-Instruct-v0.3-GGUF"
            }

            if model_name in gguf_repos:
                # Download GGUF version
                logger.info(f"Downloading GGUF model {model_name} from {gguf_repos[model_name]}")

                # Get file list from the GGUF repository
                try:
                    from huggingface_hub import list_repo_files
                    gguf_files = list_repo_files(gguf_repos[model_name])
                    gguf_files = [f for f in gguf_files if f.endswith('.gguf')]

                    if not gguf_files:
                        logger.error(f"No GGUF files found in {gguf_repos[model_name]}")
                        return False

                    # Pick the most appropriate GGUF file (prioritize Q4_K_M for balance)
                    preferred_file = None
                    for suffix in ['.Q4_K_M.gguf', '.Q5_K_M.gguf', '.Q4_0.gguf', '.Q5_0.gguf']:
                        for f in gguf_files:
                            if suffix in f:
                                preferred_file = f
                                break
                        if preferred_file:
                            break

                    if not preferred_file:
                        preferred_file = gguf_files[0]  # Use first available if no preferred match

                    # Initialize progress tracking
                    self.set_download_progress(model_key, "downloading", 0, f"Starting download...")

                    # Download the GGUF file
                    logger.info(f"Downloading GGUF file: {preferred_file}")
                    hf_hub_download(
                        repo_id=gguf_repos[model_name],
                        filename=preferred_file,
                        local_dir=model_dir,
                        local_dir_use_symlinks=False
                    )

                    self.set_download_progress(model_key, "completed", 100, "Download completed successfully")
                    logger.info(f"Successfully downloaded GGUF model {model_name}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to download GGUF model: {e}")
                    return False
            else:
                logger.error(f"No GGUF version available for model {model_name}")
                return False

        logger.info(f"Downloading model {model_name} from {model_config['repo_id']}")

        # Initialize progress tracking
        logger.info(f"Initializing download progress for {model_name}")
        self.set_download_progress(model_name, "downloading", 0, f"Starting download...")

        try:
            # Special handling for Llama models (requires authentication)
            if "llama" in model_name.lower():
                logger.warning("Llama models require authentication. Please ensure you have access.")
                logger.warning("Visit https://huggingface.co/meta-llama to request access.")

            # Download files
            total_files = len(model_config["files"])
            logger.info(f"Total files to download for {model_name}: {total_files}")
            for i, file_name in enumerate(model_config["files"]):
                file_path = model_dir / file_name
                if file_path.exists():
                    logger.info(f"File {file_name} already exists, skipping...")
                    # Update progress for skipped file
                    progress = int(((i + 1) / total_files) * 100)
                    self.set_download_progress(model_name, "downloading", progress, f"Skipping {file_name} (already exists)")
                    continue

                # Update progress before download
                progress = int((i / total_files) * 100)
                self.set_download_progress(model_name, "downloading", progress, f"Downloading {file_name}...")
                logger.info(f"Progress before downloading {file_name}: {progress}%")

                logger.info(f"Downloading {file_name}...")
                downloaded_path = hf_hub_download(
                    repo_id=model_config["repo_id"],
                    filename=file_name,
                    local_dir=model_dir,
                    local_dir_use_symlinks=False
                )

                # Update progress after download
                progress = int(((i + 1) / total_files) * 100)
                self.set_download_progress(model_name, "downloading", progress, f"Completed {file_name}")
                logger.info(f"Progress after downloading {file_name}: {progress}%")

                if progress_callback:
                    progress_callback(file_name)

            # Mark as complete
            self.set_download_progress(model_name, "completed", 100, f"Download completed successfully")
            logger.info(f"Successfully downloaded model {model_name}")
            return True

        except HfHubHTTPError as e:
            logger.error(f"Failed to download {model_name}: {e}")
            self.set_download_progress(model_name, "failed", 0, f"Download failed: {str(e)}")
            # Clean up partial download
            if model_dir.exists():
                shutil.rmtree(model_dir)
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {model_name}: {e}")
            self.set_download_progress(model_name, "failed", 0, f"Download failed: {str(e)}")
            # Clean up partial download
            if model_dir.exists():
                shutil.rmtree(model_dir)
            return False

    def remove_model(self, model_name: str) -> bool:
        """Remove a downloaded model."""
        # First try the base model name
        model_dir = self.storage_dir / model_name

        # If not found, look for format-suffixed versions
        if not model_dir.exists():
            for suffix in ["-gguf", "-safetensors", "-pytorch"]:
                format_dir = self.storage_dir / f"{model_name}{suffix}"
                if format_dir.exists():
                    model_dir = format_dir
                    break

        if not model_dir.exists():
            logger.warning(f"Model {model_name} not found locally")
            return False

        try:
            shutil.rmtree(model_dir)
            logger.info(f"Successfully removed model {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove model {model_name}: {e}")
            return False

    def list_downloaded_models(self) -> List[Dict[str, Any]]:
        """List models present on disk (complete or partial) with their info."""
        models: List[Dict[str, Any]] = []
        checked_names = set()

        # First check base model names from registry
        for model_name in self.MODEL_REGISTRY:
            checked_names.add(model_name)
            model_path = self.storage_dir / model_name
            if model_path.exists():
                # Skip empty directories
                if any(model_path.rglob("*")):
                    complete = self.is_model_downloaded(model_name)
                    total_size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())

                    models.append({
                        "name": model_name,
                        "path": str(model_path),
                        "size_bytes": total_size,
                        "size_gb": round(total_size / (1024**3), 2),
                        "type": self.MODEL_REGISTRY[model_name]["type"],
                        "status": "downloaded" if complete else "incomplete"
                    })

        # Then check for format-suffixed directories
        for model_dir in self.storage_dir.iterdir():
            if not model_dir.is_dir():
                continue

            dir_name = model_dir.name

            # Check if it's a format-suffixed version
            is_format_suffixed = False
            for suffix in ["-gguf", "-safetensors", "-pytorch"]:
                if dir_name.endswith(suffix):
                    base_name = dir_name[:-len(suffix)]
                    if base_name in self.MODEL_REGISTRY:
                        # Check if base directory doesn't exist (only format-suffixed version exists)
                        base_dir = self.storage_dir / base_name
                        if not base_dir.exists() or base_name not in checked_names:
                            checked_names.add(base_name)
                            is_format_suffixed = True

                            # Skip empty directories
                            if any(model_dir.rglob("*")):
                                complete = True  # GGUF models are single files, so they're complete
                                total_size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())

                                # Determine the type from the suffix
                                format_type = suffix[1:]  # Remove the dash

                                models.append({
                                    "name": base_name,
                                    "path": str(model_dir),
                                    "size_bytes": total_size,
                                    "size_gb": round(total_size / (1024**3), 2),
                                    "type": format_type,
                                    "status": "downloaded"
                                })
                    break

            # If no suffix matched, this might be a model not in registry
            if not is_format_suffixed:
                # Check if it looks like a model directory (has model files)
                if any(model_dir.rglob("*")) and dir_name not in checked_names:
                    # Try to detect if this is a model by looking for common model files
                    has_model_files = (
                        any(model_dir.glob("*.gguf")) or
                        any(model_dir.glob("*.safetensors")) or
                        any(model_dir.glob("*.bin")) or
                        any(model_dir.glob("config.json"))
                    )

                    if has_model_files:
                        total_size = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())

                        # Detect type based on files present
                        if any(model_dir.glob("*.gguf")):
                            model_type = "gguf"
                        elif any(model_dir.glob("*.safetensors")):
                            model_type = "safetensors"
                        elif any(model_dir.glob("*.bin")):
                            model_type = "pytorch"
                        else:
                            model_type = "unknown"

                        models.append({
                            "name": dir_name,
                            "path": str(model_dir),
                            "size_bytes": total_size,
                            "size_gb": round(total_size / (1024**3), 2),
                            "type": model_type,
                            "status": "downloaded"
                        })

        return models
