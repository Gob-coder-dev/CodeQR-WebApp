from __future__ import annotations

import io
import os
import sys
from http import HTTPStatus
from pathlib import Path

from bootstrap import ensure_project_interpreter

ensure_project_interpreter()

from flask import Flask, jsonify, render_template, request, send_file

from qr_service import QRCodeRequestError, build_download_name, generate_qr_png


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))

    return Path(__file__).resolve().parent


def create_app() -> Flask:
    runtime_root = get_runtime_root()
    app = Flask(
        __name__,
        template_folder=str(runtime_root / "templates"),
        static_folder=str(runtime_root / "static"),
    )

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), HTTPStatus.OK

    @app.post("/api/qr-code")
    def create_qr_code():
        payload = request.get_json(silent=True) or request.form or {}
        text = payload.get("text", "")
        filename = payload.get("filename", "")

        try:
            download_name = build_download_name(filename)
            image_bytes = generate_qr_png(text)
        except QRCodeRequestError as error:
            return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST

        return send_file(
            io.BytesIO(image_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=download_name,
            max_age=0,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
    )
