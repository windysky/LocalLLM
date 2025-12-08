"""Simple Python client for LocalLLM service"""

import requests
from typing import List, Dict, Optional

class LocalLLMClient:
    """Client for interacting with LocalLLM service"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/v1"

    def get_available_models(self) -> List[Dict]:
        """Get all models available in the registry"""
        response = requests.get(f"{self.api_base}/models")
        response.raise_for_status()
        return response.json()["data"]

    def get_model_status(self) -> Dict:
        """Get detailed status of all models"""
        response = requests.get(f"{self.base_url}/models/status")
        response.raise_for_status()
        return response.json()

    def get_downloaded_models(self) -> List[str]:
        """Get list of downloaded models"""
        status = self.get_model_status()
        return list(status["downloaded"].keys())

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        status = self.get_model_status()
        return [model["name"] for model in status["loaded"]]

    def is_model_available(self, model_name: str) -> bool:
        """Check if model exists in registry"""
        available = self.get_available_models()
        return any(model["id"] == model_name for model in available)

    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if model is downloaded"""
        return model_name in self.get_downloaded_models()

    def is_model_loaded(self, model_name: str) -> bool:
        """Check if model is loaded in memory"""
        return model_name in self.get_loaded_models()

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get detailed info about a specific model"""
        status = self.get_model_status()

        # Check in available models
        for model in status["available"]:
            if model["name"] == model_name:
                return model

        return None

    def download_model(self, model_name: str) -> bool:
        """Download a model"""
        response = requests.post(
            f"{self.base_url}/models/download",
            json={"model": model_name}
        )
        return response.json().get("success", False)

    def load_model(self, model_name: str) -> bool:
        """Load a model into memory"""
        response = requests.post(
            f"{self.base_url}/models/load",
            json={"model": model_name}
        )
        return response.json().get("success", False)

    def unload_model(self, model_name: str) -> bool:
        """Unload a model from memory"""
        response = requests.post(
            f"{self.base_url}/models/unload",
            json={"model": model_name}
        )
        return response.json().get("success", False)

# Example usage
if __name__ == "__main__":
    client = LocalLLMClient()

    print("Available models:")
    for model in client.get_available_models():
        print(f"  - {model['id']}")

    print("\nModel Status:")
    status = client.get_model_status()
    print(f"  Available: {len(status['available'])}")
    print(f"  Downloaded: {len(status['downloaded'])}")
    print(f"  Loaded: {len(status['loaded'])}")