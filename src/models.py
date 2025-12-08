"""Pydantic models for API requests and responses."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(..., description="Model name")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice model."""
    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Chat completion response model."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo


class CompletionRequest(BaseModel):
    """Text completion request model."""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Text prompt")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class CompletionChoice(BaseModel):
    """Completion choice model."""
    index: int
    text: str
    finish_reason: str


class CompletionResponse(BaseModel):
    """Completion response model."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: UsageInfo


class ModelInfo(BaseModel):
    """Model information model."""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    """Models list response model."""
    object: str = "list"
    data: List[ModelInfo]


class LoadModelRequest(BaseModel):
    """Load model request model."""
    model: str = Field(..., description="Model name to load")


class UnloadModelRequest(BaseModel):
    """Unload model request model."""
    model: Optional[str] = Field(None, description="Model name to unload (if None, unload all)")


class DownloadModelRequest(BaseModel):
    """Download model request model."""
    model: str = Field(..., description="Model name to download")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Any] = Field(..., description="Error details")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")