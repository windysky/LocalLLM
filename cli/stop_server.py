#!/usr/bin/env python3
"""Stop the LocalLLM server."""

import sys
import os
import argparse
import signal
from pathlib import Path
from rich.console import Console
from rich import print as rprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

PID_FILE = "locallm_server.pid"
console = Console()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Stop LocalLLM server")
    parser.add_argument("--force", "-f", action="store_true", help="Force stop")
    args = parser.parse_args()

    if not os.path.exists(PID_FILE):
        rprint("[yellow]Server is not running (no PID file found)[/yellow]")
        sys.exit(0)

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process is running
        try:
            os.kill(pid, 0)
        except OSError:
            rprint("[yellow]Server process not found (stale PID file)[/yellow]")
            os.remove(PID_FILE)
            sys.exit(0)

        # Stop the server
        rprint(f"[yellow]Stopping server (PID: {pid})...[/yellow]")

        if args.force:
            os.kill(pid, signal.SIGKILL)
            rprint("[red]Force killed server[/red]")
        else:
            os.kill(pid, signal.SIGTERM)
            rprint("[green]Server stopped successfully[/green]")

        # Remove PID file
        os.remove(PID_FILE)

    except ValueError:
        rprint("[red]Invalid PID file[/red]")
        os.remove(PID_FILE)
    except PermissionError:
        rprint("[red]Permission denied when trying to stop server[/red]")
        rprint("[yellow]Try running with sudo or check if you own the process[/yellow]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error stopping server: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()