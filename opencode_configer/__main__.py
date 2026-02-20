"""
CLI entry point for opencode-configer.

Starts the FastAPI server on a free port and opens the browser automatically.
"""
import socket
import webbrowser
from threading import Timer

import typer
import uvicorn

app = typer.Typer(help="Web UI for managing opencode configuration pairs.")


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


@app.command()
def main(
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to."),
    port: int = typer.Option(0, help="Port to listen on (0 = auto-select)."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not open the browser automatically."),
) -> None:
    """Start the opencode-configer web UI."""
    resolved_port = port or _find_free_port()
    url = f"http://{host}:{resolved_port}"

    typer.echo(f"Starting opencode-configer at {url}")

    if not no_browser:
        # Open browser shortly after server starts
        Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(
        "opencode_configer.server:app",
        host=host,
        port=resolved_port,
        log_level="warning",
    )


if __name__ == "__main__":
    app()
