"""Configuration management for LocalLLM."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration settings."""
    model_config = SettingsConfigDict(env_prefix="server_")

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1


class ModelsConfig(BaseSettings):
    """Model-related configuration."""
    model_config = SettingsConfigDict(env_prefix="models_")

    storage_dir: str = "./models"
    default_model: str = ""
    max_loaded_models: int = 1
    auto_download: bool = True
    supported_formats: list = ["gguf", "safetensors", "pytorch"]


class InferenceConfig(BaseSettings):
    """Inference configuration."""
    model_config = SettingsConfigDict(env_prefix="inference_")

    device: str = "auto"
    max_memory: int = 8
    context_size: int = 2048
    temperature: float = 0.7
    max_tokens: int = 1024


class WebConfig(BaseSettings):
    """Web interface configuration."""
    model_config = SettingsConfigDict(env_prefix="web_")

    enabled: bool = True
    port: int = 8080
    host: str = "0.0.0.0"


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    model_config = SettingsConfigDict(env_prefix="logging_")

    level: str = "INFO"
    file: str = "logs/locallm.log"
    max_size: str = "10MB"
    backup_count: int = 5


class APIConfig(BaseSettings):
    """API configuration."""
    model_config = SettingsConfigDict(env_prefix="api_")

    openai_compatible: bool = True
    rate_limit: int = 60
    cors_enabled: bool = True
    cors_origins: list = ["*"]


class Config(BaseSettings):
    """Main configuration class."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow"
    )

    server: ServerConfig = ServerConfig()
    models: ModelsConfig = ModelsConfig()
    inference: InferenceConfig = InferenceConfig()
    web: WebConfig = WebConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = "config.yaml"

        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f) or {}
            return cls(**config_data)
        return cls()

    def ensure_directories(self):
        """Ensure necessary directories exist."""
        # Create model storage directory
        model_dir = Path(self.models.storage_dir)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Create logs directory
        log_file = Path(self.logging.file)
        log_file.parent.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config.load_from_file()
config.ensure_directories()