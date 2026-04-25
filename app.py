from __future__ import annotations

import io
import os
import sys
from http import HTTPStatus
from pathlib import Path

from bootstrap import ensure_project_interpreter

ensure_project_interpreter()

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

from qr_payload import build_qr_payload
from qr_service import QRCodeRequestError, build_download_name, generate_qr_file

MAX_REQUEST_BYTES = 3 * 1024 * 1024


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
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), HTTPStatus.OK

    @app.errorhandler(RequestEntityTooLarge)
    def request_entity_too_large(_error):
        return (
            jsonify({"error": "Logo image must be 2 MB or smaller."}),
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )

    @app.post("/api/qr-code")
    def create_qr_code():
        payload = request.get_json(silent=True) if request.is_json else None
        if payload is None:
            payload = request.form or {}

        filename = payload.get("filename", "")
        logo_upload = request.files.get("logo")
        logo_file = logo_upload.stream if logo_upload and logo_upload.filename else None

        try:
            qr_payload = build_qr_payload(payload)
            image_bytes, mimetype, extension = generate_qr_file(
                qr_payload,
                output_format=payload.get("output_format", ""),
                foreground_color=payload.get("foreground_color", ""),
                foreground_color_2=payload.get("foreground_color_2", ""),
                background_color=payload.get("background_color", ""),
                module_style=payload.get("module_style", ""),
                eye_style=payload.get("eye_style", ""),
                quality=payload.get("quality", ""),
                error_correction=payload.get("error_correction", ""),
                border_size=payload.get("border_size", ""),
                color_mode=payload.get("color_mode", ""),
                transparent_background=payload.get("transparent_background", ""),
                logo_size=payload.get("logo_size", ""),
                logo_file=logo_file,
            )
            download_name = build_download_name(filename, extension)
        except QRCodeRequestError as error:
            return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST

        return send_file(
            io.BytesIO(image_bytes),
            mimetype=mimetype,
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
