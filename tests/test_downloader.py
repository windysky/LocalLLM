"""Test model downloader."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.downloader import ModelDownloader


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def downloader(temp_storage):
    """Create a ModelDownloader instance with temporary storage."""
    return ModelDownloader(temp_storage)


def test_list_available_models(downloader):
    """Test listing available models in registry."""
    models = downloader.list_available_models()

    assert isinstance(models, list)
    assert "gemma-2-9b" in models
    assert "qwen2.5-7b" in models
    assert "llama-3.1-8b" in models


def test_is_model_downloaded(downloader, temp_storage):
    """Test checking if model is downloaded."""
    # Model not downloaded initially
    assert not downloader.is_model_downloaded("gemma-2-9b")

    # Create fake model files
    model_dir = Path(temp_storage) / "gemma-2-9b"
    model_dir.mkdir()
    (model_dir / "config.json").touch()
    (model_dir / "tokenizer.json").touch()

    # Still not fully downloaded (missing safetensors)
    assert not downloader.is_model_downloaded("gemma-2-9b")

    # Add required files
    (model_dir / "model-00001-of-00004.safetensors").touch()
    (model_dir / "model-00002-of-00004.safetensors").touch()
    (model_dir / "model-00003-of-00004.safetensors").touch()
    (model_dir / "model-00004-of-00004.safetensors").touch()
    (model_dir / "model.safetensors.index.json").touch()

    # Now it should be considered downloaded
    assert downloader.is_model_downloaded("gemma-2-9b")


def test_get_model_path(downloader, temp_storage):
    """Test getting model path."""
    # Non-existent model returns None
    assert downloader.get_model_path("gemma-2-9b") is None

    # Create model directory
    model_dir = Path(temp_storage) / "gemma-2-9b"
    model_dir.mkdir()
    (model_dir / "config.json").touch()

    # Still returns None because not fully downloaded
    assert downloader.get_model_path("gemma-2-9b") is None

    # Add all required files
    for file in downloader.MODEL_REGISTRY["gemma-2-9b"]["files"]:
        (model_dir / file).touch()

    # Now returns the path
    path = downloader.get_model_path("gemma-2-9b")
    assert path is not None
    assert path == model_dir


def test_list_downloaded_models(downloader, temp_storage):
    """Test listing downloaded models."""
    # Initially empty
    models = downloader.list_downloaded_models()
    assert len(models) == 0

    # Create a fake downloaded model
    model_dir = Path(temp_storage) / "gemma-2-9b"
    model_dir.mkdir()
    total_size = 0
    for file in downloader.MODEL_REGISTRY["gemma-2-9b"]["files"]:
        file_path = model_dir / file
        file_path.write_text("test content")
        total_size += file_path.stat().st_size

    models = downloader.list_downloaded_models()
    assert len(models) == 1
    assert models[0]["name"] == "gemma-2-9b"
    assert models[0]["path"] == str(model_dir)
    assert models[0]["size_bytes"] == total_size
    assert models[0]["type"] == "safetensors"


@patch('src.downloader.hf_hub_download')
def test_download_model_success(mock_download, downloader, temp_storage):
    """Test successful model download."""
    mock_download.return_value = "downloaded_file_path"

    # Download a model
    success = downloader.download_model("gemma-2-9b")

    assert success
    assert mock_download.call_count == len(downloader.MODEL_REGISTRY["gemma-2-9b"]["files"])


def test_remove_model(downloader, temp_storage):
    """Test removing a downloaded model."""
    # Create a fake model
    model_dir = Path(temp_storage) / "gemma-2-9b"
    model_dir.mkdir()
    (model_dir / "test_file").touch()

    # Remove it
    success = downloader.remove_model("gemma-2-9b")

    assert success
    assert not model_dir.exists()


def test_remove_nonexistent_model(downloader):
    """Test removing a non-existent model."""
    success = downloader.remove_model("nonexistent-model")
    assert not success