#!/usr/bin/env python3
"""Start the LocalLLM server."""

import sys
import os
import argparse
import signal
import time
from pathlib import Path
from rich.console import Console
from rich import print as rprint

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Get project root (parent of cli directory)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
except ImportError:
    print("Warning: python-dotenv not installed, .env file will not be loaded automatically")
except Exception as e:
    print(f"Warning: Failed to load .env file: {e}")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.server import run_server

console = Console()
PID_FILE = "locallm_server.pid"


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    rprint("\n[yellow]Shutting down server...[/yellow]")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


def check_server_running():
    """Check if server is already running."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is running
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # PID file exists but process is not running
            os.remove(PID_FILE)
    return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Start LocalLLM server")
    parser.add_argument("--host", default=config.server.host, help="Server host")
    parser.add_argument("--port", type=int, default=config.server.port, help="Server port")
    parser.add_argument("--workers", type=int, default=config.server.workers, help="Number of workers")
    parser.add_argument("--model", default=config.models.default_model, help="Default model to load")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--no-auto-download", action="store_true", help="Disable automatic model downloading")

    args = parser.parse_args()

    # Check if server is already running
    if check_server_running():
        rprint("[red]Server is already running![/red]")
        rprint(f"Check {PID_FILE} for the PID")
        sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Write PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # Update config
    config.server.host = args.host
    config.server.port = args.port
    config.server.workers = 1 if args.dev else args.workers
    config.models.default_model = args.model or ""
    config.models.auto_download = not args.no_auto_download

    # Print startup message
    rprint("[green]Starting LocalLLM server...[/green]")
    rprint(f"Host: {config.server.host}")
    rprint(f"Port: {config.server.port}")
    rprint(f"Workers: {config.server.workers}")
    if config.models.default_model:
        rprint(f"Default model: {config.models.default_model}")
    rprint(f"Auto-download: {'enabled' if config.models.auto_download else 'disabled'}")

    # Start server
    try:
        run_server()
    except KeyboardInterrupt:
        handle_shutdown(None, None)
    except Exception as e:
        rprint(f"[red]Error starting server: {e}[/red]")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        sys.exit(1)


if __name__ == "__main__":
    main()