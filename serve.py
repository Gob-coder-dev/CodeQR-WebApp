from __future__ import annotations

import os

from bootstrap import ensure_project_interpreter

ensure_project_interpreter()

from waitress import serve

from app import create_app


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "10000"))
    threads = int(os.environ.get("WAITRESS_THREADS", "4"))

    serve(create_app(), host=host, port=port, threads=threads)


if __name__ == "__main__":
    main()
