#!/usr/bin/env python3
"""Utility to update the model registry from models.yaml"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def update_registry():
    """Update MODEL_REGISTRY in downloader.py from models.yaml"""

    # Read models.yaml
    models_file = Path(__file__).parent / "models.yaml"
    if not models_file.exists():
        print(f"Error: {models_file} not found!")
        return 1

    with open(models_file, 'r') as f:
        models_config = yaml.safe_load(f)

    # Generate Python code for MODEL_REGISTRY
    registry_code = "    MODEL_REGISTRY = {\n"

    for model_name, model_info in models_config['models'].items():
        registry_code += f'        "{model_name}": {{\n'
        registry_code += f'            "repo_id": "{model_info["repo_id"]}",\n'
        registry_code += '            "files": ['
        registry_code += ', '.join(f'"{file}"' for file in model_info["files"])
        registry_code += '],\n'
        registry_code += f'            "type": "{model_info["type"]}"\n'
        if "description" in model_info:
            registry_code += f',            "description": "{model_info["description"]}"\n'
        registry_code += '        },\n'

    registry_code += "    }\n"

    # Read downloader.py
    downloader_file = Path(__file__).parent / "src" / "downloader.py"
    with open(downloader_file, 'r') as f:
        content = f.read()

    # Find and replace MODEL_REGISTRY
    import re
    pattern = r'    # Popular model configurations\n    MODEL_REGISTRY = \{.*?\n    \}'
    new_content = re.sub(
        pattern,
        f'    # Popular model configurations\n{registry_code}',
        content,
        flags=re.DOTALL
    )

    # Write back to downloader.py
    with open(downloader_file, 'w') as f:
        f.write(new_content)

    print(f"✅ Updated {len(models_config['models'])} models in MODEL_REGISTRY")
    print("⚠️  Please restart the LocalLLM server to apply changes")
    return 0

if __name__ == "__main__":
    sys.exit(update_registry())