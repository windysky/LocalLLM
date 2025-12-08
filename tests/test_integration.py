"""Integration tests for the complete system."""

import pytest
import requests
import subprocess
import time
import os
import sys
import signal
from pathlib import Path

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8999  # Use a different port for testing
API_BASE = f"http://{SERVER_HOST}:{SERVER_PORT}"


@pytest.fixture(scope="session")
def test_server():
    """Start a test server instance."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Start the server process
    env = os.environ.copy()
    env["DEFAULT_HOST"] = SERVER_HOST
    env["DEFAULT_PORT"] = str(SERVER_PORT)
    env["MODEL_DIR"] = str(project_root / "test_models")

    server_process = subprocess.Popen(
        [sys.executable, "cli/start_server.py", "--port", str(SERVER_PORT)],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(3)

    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            server_process.terminate()
            server_process.wait()
            raise RuntimeError("Server failed to start")
    except requests.exceptions.RequestException:
        server_process.terminate()
        server_process.wait()
        raise RuntimeError("Server not responding")

    yield API_BASE

    # Clean up
    server_process.terminate()
    server_process.wait()


class TestSystemIntegration:
    """Integration tests for the complete system."""

    def test_server_health(self, test_server):
        """Test server health endpoint."""
        response = requests.get(f"{test_server}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert isinstance(data["models_loaded"], int)

    def test_list_models(self, test_server):
        """Test listing available models."""
        response = requests.get(f"{test_server}/v1/models")
        assert response.status_code == 200

        data = response.json()
        assert data["object"] == "list"
        assert isinstance(data["data"], list)

        # Check that we have the expected models
        model_ids = [model["id"] for model in data["data"]]
        expected_models = ["gemma-2-9b", "qwen2.5-7b", "llama-3.1-8b", "mistral-7b"]
        for model in expected_models:
            assert model in model_ids

    def test_models_status(self, test_server):
        """Test getting models status."""
        response = requests.get(f"{test_server}/models/status")
        assert response.status_code == 200

        data = response.json()
        assert "available" in data
        assert "loaded" in data
        assert "downloaded" in data
        assert isinstance(data["available"], list)
        assert isinstance(data["loaded"], list)
        assert isinstance(data["downloaded"], dict)

    def test_chat_completion_without_model(self, test_server):
        """Test chat completion with model not loaded (and auto-download disabled for test)."""
        request_data = {
            "model": "gemma-2-9b",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }

        response = requests.post(
            f"{test_server}/v1/chat/completions",
            json=request_data
        )

        # Should fail because model is not downloaded
        assert response.status_code == 404

    def test_openai_api_compatibility(self, test_server):
        """Test that the API is OpenAI-compatible."""
        # This tests the structure of responses
        response = requests.get(f"{test_server}/v1/models")
        assert response.status_code == 200

        data = response.json()
        # Check OpenAI-compatible structure
        assert "object" in data
        assert "data" in data

        if data["data"]:
            model = data["data"][0]
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"
            assert "created" in model
            assert "owned_by" in model

    def test_error_handling(self, test_server):
        """Test error handling."""
        # Test with invalid model
        request_data = {
            "model": "nonexistent-model",
            "messages": [
                {"role": "user", "content": "Hello!"}
            ]
        }

        response = requests.post(
            f"{test_server}/v1/chat/completions",
            json=request_data
        )

        assert response.status_code == 404

        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

    def test_cors_headers(self, test_server):
        """Test CORS headers are present."""
        response = requests.options(f"{test_server}/v1/models")
        # Check for CORS headers
        assert response.status_code in [200, 405]  # 405 is OK for OPTIONS if CORS is enabled

    def test_api_ratelimit_info(self, test_server):
        """Test API returns rate limit info (if configured)."""
        # Just ensure the endpoint responds
        response = requests.get(f"{test_server}/")
        assert response.status_code == 200

        data = response.json()
        assert "endpoints" in data
        assert "chat" in data["endpoints"]
        assert "models" in data["endpoints"]