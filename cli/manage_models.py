#!/usr/bin/env python3
"""Manage LocalLLM models."""

import sys
import os
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.model_manager import ModelManager

console = Console()


def list_models(manager: ModelManager):
    """List all available models."""
    models = manager.list_available_models()

    if not models:
        rprint("[yellow]No models found[/yellow]")
        return

    table = Table(title="Available Models")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Size (GB)", justify="right")

    for model in models:
        status = model["status"]
        if status == "downloaded":
            status_str = "[green]Downloaded[/green]"
            size = f"{model.get('size_gb', 'N/A')}"
        elif status == "loaded":
            status_str = "[blue]Loaded[/blue]"
            size = f"{model.get('size_gb', 'N/A')}"
        else:
            status_str = "[red]Not Downloaded[/red]"
            size = "N/A"

        table.add_row(
            model["name"],
            status_str,
            model.get("type", "unknown"),
            size
        )

    console.print(table)


def download_model(manager: ModelManager, model_name: str):
    """Download a model."""
    rprint(f"[cyan]Downloading model: {model_name}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading...", total=None)

        def progress_callback(filename):
            progress.update(task, description=f"Downloading {filename}...")

        if manager.download_model(model_name):
            progress.update(task, description="[green]Download complete![/green]")
            rprint(f"[green]Successfully downloaded {model_name}[/green]")
        else:
            progress.update(task, description="[red]Download failed![/red]")
            rprint(f"[red]Failed to download {model_name}[/red]")


def remove_model(manager: ModelManager, model_name: str):
    """Remove a downloaded model."""
    rprint(f"[yellow]Removing model: {model_name}[/yellow]")

    if manager.downloader.remove_model(model_name):
        rprint(f"[green]Successfully removed {model_name}[/green]")
    else:
        rprint(f"[red]Failed to remove {model_name}[/red]")


def load_model(manager: ModelManager, model_name: str):
    """Load a model into memory."""
    rprint(f"[cyan]Loading model: {model_name}[/cyan]")

    if model_name in manager.loaded_models:
        rprint(f"[yellow]Model {model_name} is already loaded[/yellow]")
        return

    if manager.load_model(model_name):
        rprint(f"[green]Successfully loaded {model_name}[/green]")
    else:
        rprint(f"[red]Failed to load {model_name}[/red]")


def unload_model(manager: ModelManager, model_name: str):
    """Unload a model from memory."""
    rprint(f"[yellow]Unloading model: {model_name}[/yellow]")

    if model_name not in manager.loaded_models:
        rprint(f"[yellow]Model {model_name} is not loaded[/yellow]")
        return

    if manager.unload_model(model_name):
        rprint(f"[green]Successfully unloaded {model_name}[/green]")
    else:
        rprint(f"[red]Failed to unload {model_name}[/red]")


def show_loaded_models(manager: ModelManager):
    """Show currently loaded models."""
    loaded = manager.get_loaded_models()

    if not loaded:
        rprint("[yellow]No models are currently loaded[/yellow]")
        return

    table = Table(title="Loaded Models")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Ollama Name", style="magenta")
    table.add_column("Path", style="green")

    for model in loaded:
        table.add_row(
            model["name"],
            model["ollama_name"],
            model["path"]
        )

    console.print(table)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage LocalLLM models")
    parser.add_argument("--list", "-l", action="store_true", help="List all available models")
    parser.add_argument("--download", "-d", help="Download a model")
    parser.add_argument("--remove", "-r", help="Remove a downloaded model")
    parser.add_argument("--load", help="Load a model")
    parser.add_argument("--unload", "-u", help="Unload a model")
    parser.add_argument("--loaded", action="store_true", help="Show loaded models")

    args = parser.parse_args()

    # Initialize model manager
    manager = ModelManager()

    if args.list:
        list_models(manager)
    elif args.download:
        download_model(manager, args.download)
    elif args.remove:
        remove_model(manager, args.remove)
    elif args.load:
        load_model(manager, args.load)
    elif args.unload:
        unload_model(manager, args.unload)
    elif args.loaded:
        show_loaded_models(manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()