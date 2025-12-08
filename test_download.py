#!/usr/bin/env python3
"""Test which models can actually be downloaded"""

import requests
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

# Models to test
test_models = {
    "phi-3-mini": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
    "qwen2.5-7b": "Qwen/Qwen2.5-7B-Instruct"
}

print("Testing model downloads (checking first file only)...")
print("=" * 60)

success_models = []
failed_models = []

for model_name, repo_id in test_models.items():
    try:
        # Try to download just the config file to test access
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename="config.json",
            local_dir="/tmp/test_download",
            local_dir_use_symlinks=False
        )
        print(f"✅ {model_name} - Can download")
        success_models.append(model_name)
    except HfHubHTTPError as e:
        print(f"❌ {model_name} - Failed: {e}")
        failed_models.append(model_name)
    except Exception as e:
        print(f"⚠️ {model_name} - Error: {e}")
        failed_models.append(model_name)

print("\n" + "=" * 60)
print("\n✅ Models you can download NOW:")
for model in success_models:
    print(f"  - {model}")

print("\n❌ Models that require authentication:")
for model in failed_models:
    print(f"  - {model}")

# Clean up
import shutil
shutil.rmtree("/tmp/test_download", ignore_errors=True)