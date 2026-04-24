import io

import pytest
from PIL import Image

from qr_service import QRCodeRequestError, build_download_name, generate_qr_png


def build_logo_file() -> io.BytesIO:
    logo_file = io.BytesIO()
    Image.new("RGBA", (80, 80), (15, 118, 110, 255)).save(logo_file, format="PNG")
    logo_file.seek(0)
    return logo_file


def test_build_download_name_adds_extension_when_missing():
    assert build_download_name("my-file") == "my-file.png"


def test_build_download_name_sanitizes_invalid_characters():
    assert build_download_name('bad:/\\name?.png') == "bad-name.png"


def test_build_download_name_uses_default_for_blank_input():
    assert build_download_name("   ") == "qr-code.png"


def test_generate_qr_png_returns_png_signature():
    image_bytes = generate_qr_png("https://example.com")
    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_supports_custom_colors_and_shape():
    image_bytes = generate_qr_png(
        "https://example.com",
        foreground_color="#0f766e",
        background_color="#ffffff",
        module_style="rounded",
    )

    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_supports_embedded_logo():
    image_bytes = generate_qr_png(
        "https://example.com",
        foreground_color="#102033",
        background_color="#ffffff",
        module_style="circle",
        logo_file=build_logo_file(),
    )

    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_rejects_invalid_color():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("https://example.com", foreground_color="teal")


def test_generate_qr_png_rejects_low_contrast_colors():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png(
            "https://example.com",
            foreground_color="#ffffff",
            background_color="#ffffff",
        )


def test_generate_qr_png_rejects_unknown_shape():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("https://example.com", module_style="triangle")


def test_generate_qr_png_rejects_blank_text():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("   ")
