"""
CLI entry point for opencode-configer.

Starts the FastAPI server on a free port and opens the browser automatically.
"""
import socket
import time
import webbrowser
from contextlib import suppress
from threading import Thread

import httpx
import typer
import uvicorn

app = typer.Typer(help="Web UI for managing opencode configuration pairs.")

_POLL_INTERVAL = 0.25
_POLL_TIMEOUT = 30.0


def _find_free_port(start: int = 7420) -> int:
    """
    Find the first available TCP port starting from `start`.

    :param start: Port number to start scanning from.
    :type start: int
    :return: An available port number.
    :rtype: int
    """
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


def _open_when_ready(url: str, health_url: str) -> None:
    """
    Poll the health endpoint and open the browser once the server is ready.

    :param url: Base URL to open in the browser.
    :type url: str
    :param health_url: URL of the health-check endpoint to poll.
    :type health_url: str
    """
    deadline = time.monotonic() + _POLL_TIMEOUT
    while time.monotonic() < deadline:
        with suppress(httpx.RequestError):
            resp = httpx.get(health_url, timeout=1.0)
            if resp.status_code == 200:
                webbrowser.open(url)
                return
        time.sleep(_POLL_INTERVAL)


@app.command()
def main(
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to."),
    port: int = typer.Option(0, help="Port to listen on (0 = auto-select)."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not open the browser automatically."),
) -> None:
    """Start the opencode-configer web UI."""
    resolved_port = port or _find_free_port()
    url = f"http://{host}:{resolved_port}"
    health_url = f"{url}/api/health"

    typer.echo(f"Starting opencode-configer at {url}")

    if not no_browser:
        Thread(target=_open_when_ready, args=(url, health_url), daemon=True).start()

    uvicorn.run(
        "opencode_configer.server:app",
        host=host,
        port=resolved_port,
        log_level="warning",
    )


if __name__ == "__main__":
    app()
