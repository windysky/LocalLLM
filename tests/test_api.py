"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json

from src.server import app
from src.models import ChatCompletionRequest, CompletionRequest


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_model_manager():
    """Mock model manager."""
    mock = Mock()
    mock.list_available_models.return_value = [
        {
            "name": "gemma-2-9b",
            "status": "downloaded",
            "type": "safetensors",
            "size_gb": 5.2
        }
    ]
    mock.get_loaded_models.return_value = []
    mock.downloaded_models = {}
    mock.loaded_models = {}
    return mock


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns correct status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "models_loaded" in data


class TestModelsEndpoint:
    """Test models endpoints."""

    @patch('src.server.model_manager')
    def test_list_models(self, mock_manager, client):
        """Test listing models."""
        mock_manager.list_available_models.return_value = [
            {
                "name": "gemma-2-9b",
                "status": "downloaded",
                "type": "safetensors"
            },
            {
                "name": "qwen2.5-7b",
                "status": "not_downloaded",
                "type": "safetensors"
            }
        ]

        response = client.get("/v1/models")
        assert response.status_code == 200

        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "gemma-2-9b"
        assert data["data"][0]["object"] == "model"
        assert data["data"][0]["owned_by"] == "local"


class TestChatCompletion:
    """Test chat completion endpoint."""

    @patch('src.server.model_manager')
    def test_chat_completion_success(self, mock_manager, client):
        """Test successful chat completion."""
        mock_manager.loaded_models = {"gemma-2-9b": {}}
        mock_manager.chat_completion.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gemma-2-9b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20
            }
        }

        request_data = {
            "model": "gemma-2-9b",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "gemma-2-9b"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["content"] == "Hello! How can I help you?"

    @patch('src.server.model_manager')
    def test_chat_completion_model_not_loaded(self, mock_manager, client):
        """Test chat completion with model not loaded."""
        mock_manager.loaded_models = {}
        mock_manager.download_model.return_value = False

        request_data = {
            "model": "gemma-2-9b",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 404

    @patch('src.server.model_manager')
    def test_chat_completion_generation_failure(self, mock_manager, client):
        """Test chat completion with generation failure."""
        mock_manager.loaded_models = {"gemma-2-9b": {}}
        mock_manager.chat_completion.return_value = None

        request_data = {
            "model": "gemma-2-9b",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 500


class TestCompletion:
    """Test text completion endpoint."""

    @patch('src.server.model_manager')
    def test_completion_success(self, mock_manager, client):
        """Test successful text completion."""
        mock_manager.loaded_models = {"gemma-2-9b": {}}
        mock_manager.generate.return_value = "This is a completion."

        request_data = {
            "model": "gemma-2-9b",
            "prompt": "Once upon a time"
        }

        response = client.post("/v1/completions", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "gemma-2-9b"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["text"] == "This is a completion."
        assert data["choices"][0]["finish_reason"] == "stop"

    @patch('src.server.model_manager')
    def test_completion_model_not_loaded(self, mock_manager, client):
        """Test completion with model not loaded."""
        mock_manager.loaded_models = {}
        mock_manager.download_model.return_value = False

        request_data = {
            "model": "gemma-2-9b",
            "prompt": "Once upon a time"
        }

        response = client.post("/v1/completions", json=request_data)
        assert response.status_code == 404


class TestModelManagement:
    """Test model management endpoints."""

    @patch('src.server.model_manager')
    def test_load_model(self, mock_manager, client):
        """Test loading a model."""
        mock_manager.downloaded_models = {"gemma-2-9b": {}}
        mock_manager.load_model.return_value = True

        response = client.post("/models/load", json={"model": "gemma-2-9b"})
        assert response.status_code == 200

        data = response.json()
        assert "loaded successfully" in data["message"]

    @patch('src.server.model_manager')
    def test_unload_model(self, mock_manager, client):
        """Test unloading a model."""
        mock_manager.loaded_models = {"gemma-2-9b": {}}
        mock_manager.unload_model.return_value = True

        response = client.post("/models/unload", json={"model": "gemma-2-9b"})
        assert response.status_code == 200

        data = response.json()
        assert "unloaded successfully" in data["message"]

    @patch('src.server.model_manager')
    def test_download_model(self, mock_manager, client):
        """Test downloading a model."""
        mock_manager.downloaded_models = {}
        mock_manager.download_model.return_value = True

        response = client.post("/models/download", json={"model": "gemma-2-9b"})
        assert response.status_code == 200

        data = response.json()
        assert "downloaded successfully" in data["message"]

    @patch('src.server.model_manager')
    def test_get_models_status(self, mock_manager, client):
        """Test getting models status."""
        mock_manager.list_available_models.return_value = []
        mock_manager.get_loaded_models.return_value = []
        mock_manager.downloaded_models = {}

        response = client.get("/models/status")
        assert response.status_code == 200

        data = response.json()
        assert "available" in data
        assert "loaded" in data
        assert "downloaded" in data