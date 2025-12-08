#!/usr/bin/env python3
"""Hugging Face model search API endpoint"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import requests
import os

router = APIRouter()

# Hugging Face API
HF_API_URL = "https://huggingface.co/api/models"

@router.get("/api/search/huggingface")
async def search_huggingface(
    query: str,
    limit: int = 10,
    filter: Optional[str] = None
):
    """Search for models on Hugging Face"""

    try:
        # Build search parameters
        params = {
            "search": query,
            "limit": limit,
            "sort": "downloads",
            "direction": "-1"
        }

        # Add filters if specified
        if filter:
            if filter == "text-generation":
                params["library"] = "transformers"
                params["tags"] = "text-generation"
            elif filter == "gguf":
                params["tags"] = "gguf"

        # Make request to Hugging Face API
        response = requests.get(HF_API_URL, params=params, timeout=10)
        response.raise_for_status()

        models = response.json()

        # Format results
        formatted_models = []
        for model in models[:limit]:
            # Only include models with proper model cards
            if model.get("modelId") and model.get("downloads", 0) > 0:
                formatted_models.append({
                    "id": model["modelId"],
                    "author": model.get("author", ""),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "lastModified": model.get("lastModified", ""),
                    "tags": model.get("tags", []),
                    "pipeline_tag": model.get("pipeline_tag", ""),
                    "library_name": model.get("library_name", ""),
                    "description": (model.get("cardData", {}).get("text", "") or "")[:200] + "..." if model.get("cardData", {}).get("text") else "No description available"
                })

        return {
            "success": True,
            "models": formatted_models,
            "total": len(formatted_models)
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search Hugging Face: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )