from __future__ import annotations

import contextlib
import socket
import threading
import time
import webbrowser

from bootstrap import ensure_project_interpreter

ensure_project_interpreter()

from waitress import serve

from app import create_app


HOST = "127.0.0.1"
DEFAULT_PORT = 5000


def choose_port(preferred_port: int = DEFAULT_PORT) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((HOST, preferred_port))
        return preferred_port


def resolve_port() -> int:
    try:
        return choose_port(DEFAULT_PORT)
    except OSError:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind((HOST, 0))
            return sock.getsockname()[1]


def open_browser_when_ready(url: str) -> None:
    time.sleep(1)
    webbrowser.open(url)


def main() -> None:
    port = resolve_port()
    url = f"http://{HOST}:{port}"

    print("QR Code Converter is starting...")
    print(f"Open in your browser: {url}")
    print("Close this window to stop the app.")

    threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    serve(create_app(), host=HOST, port=port, threads=4)


if __name__ == "__main__":
    main()
