#!/usr/bin/env python3
"""Check which models are actually downloadable without authentication"""

import requests
from huggingface_hub import HfApi
import yaml

# Load model registry
with open('models.yaml', 'r') as f:
    registry = yaml.safe_load(f)

api = HfApi()

print("Checking model availability on Hugging Face...")
print("=" * 60)

available_models = []
restricted_models = []

for model_name, model_info in registry['models'].items():
    repo_id = model_info['repo_id']

    try:
        # Check if repo exists and is accessible
        repo_info = api.repo_info(repo_id=repo_id, files_metadata=False)

        # Try to get file info
        files = api.list_repo_files(repo_id=repo_id)

        # Check if required files exist
        missing_files = []
        for required_file in model_info['files']:
            if required_file not in files:
                missing_files.append(required_file)

        if missing_files:
            print(f"❌ {model_name}")
            print(f"   Repo: {repo_id}")
            print(f"   Missing files: {missing_files}")
            restricted_models.append(model_name)
        else:
            print(f"✅ {model_name}")
            print(f"   Repo: {repo_id}")
            available_models.append(model_name)

    except Exception as e:
        print(f"❌ {model_name}")
        print(f"   Repo: {repo_id}")
        print(f"   Error: {str(e)}")
        restricted_models.append(model_name)

    print()

print("=" * 60)
print(f"Available models (no auth needed): {len(available_models)}")
for model in available_models:
    print(f"  - {model}")

print(f"\nRestricted models (need HF token): {len(restricted_models)}")
for model in restricted_models:
    print(f"  - {model}")

print("\n" + "=" * 60)
print("\nRecommendations:")
print("1. For quick testing without HF token:")
for model in available_models:
    print(f"   - {model}")

print("\n2. To access restricted models:")
print("   - Request access on Hugging Face website")
print("   - Set HUGGINGFACE_TOKEN environment variable")
print("   - Or use alternative models that don't require access")