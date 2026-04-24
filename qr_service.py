from __future__ import annotations

import io
import re
from typing import Final

import qrcode
from qrcode.constants import ERROR_CORRECT_M


DEFAULT_FILE_STEM: Final[str] = "qr-code"
MAX_FILE_STEM_LENGTH: Final[int] = 80
INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
WHITESPACE = re.compile(r"\s+")
MULTIPLE_DASHES = re.compile(r"-{2,}")


class QRCodeRequestError(ValueError):
    """Raised when a QR code request is invalid."""


def build_download_name(raw_name: str) -> str:
    stem = (raw_name or "").strip()

    if stem.lower().endswith(".png"):
        stem = stem[:-4]

    stem = INVALID_FILE_CHARS.sub("-", stem)
    stem = WHITESPACE.sub("-", stem)
    stem = MULTIPLE_DASHES.sub("-", stem)
    stem = stem.strip(" .-_")

    if not stem:
        stem = DEFAULT_FILE_STEM

    stem = stem[:MAX_FILE_STEM_LENGTH].rstrip(" .-_")

    if not stem:
        stem = DEFAULT_FILE_STEM

    return f"{stem}.png"


def generate_qr_png(text: str) -> bytes:
    value = (text or "").strip()
    if not value:
        raise QRCodeRequestError("Please enter a text or a link before generating a QR code.")

    qr_code = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr_code.add_data(value)
    qr_code.make(fit=True)

    image = qr_code.make_image(fill_color="#102033", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
