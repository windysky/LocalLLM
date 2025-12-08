#!/usr/bin/env python3
"""Quick system test to verify everything works."""

import sys
import os
import time
import subprocess
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.model_manager import ModelManager


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.config import Config
        from src.downloader import ModelDownloader
        from src.model_manager import ModelManager
        from src.server import app
        from src.models import ChatCompletionRequest
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
        assert config.models.storage_dir == "./models"
        assert Path(config.models.storage_dir).exists()
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_model_manager():
    """Test model manager initialization."""
    print("\nTesting model manager...")

    try:
        manager = ModelManager()

        # Test listing models
        models = manager.list_available_models()
        assert len(models) > 0
        assert "gemma-2-9b" in [m["name"] for m in models]

        print(f"✓ Found {len(models)} models in registry")
        return True
    except Exception as e:
        print(f"✗ Model manager error: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints by starting the server briefly."""
    print("\nTesting API endpoints...")

    # Start server in background
    env = os.environ.copy()
    env["DEFAULT_PORT"] = "8998"  # Use different port

    server_proc = subprocess.Popen(
        [sys.executable, "cli/start_server.py", "--port", "8998", "--no-auto-download"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )

    # Wait for server to start
    time.sleep(3)

    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8998/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server health check passed")
        else:
            raise Exception(f"Health check failed: {response.status_code}")

        # Test models endpoint
        response = requests.get("http://127.0.0.1:8998/v1/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert len(data["data"]) > 0
            print(f"✓ Models endpoint returned {len(data['data'])} models")
        else:
            raise Exception(f"Models endpoint failed: {response.status_code}")

        # Test root endpoint
        response = requests.get("http://127.0.0.1:8998/", timeout=5)
        if response.status_code == 200:
            print("✓ Root endpoint accessible")
        else:
            raise Exception(f"Root endpoint failed: {response.status_code}")

        return True
    except Exception as e:
        print(f"✗ API test error: {e}")
        return False
    finally:
        # Clean up server
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()


def main():
    """Run all tests."""
    print("Running LocalLLM System Tests\n")
    print("=" * 50)

    results = []

    # Run tests
    results.append(test_imports())
    results.append(test_config())
    results.append(test_model_manager())
    results.append(test_api_endpoints())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Start the server: python cli/start_server.py")
        print("3. Open the web interface: http://localhost:8080")
        print("4. Or use the API: http://localhost:8000/v1/chat/completions")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())