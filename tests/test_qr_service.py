import io

import pytest
from PIL import Image, ImageDraw

from qr_service import (
    QRCodeRequestError,
    build_download_name,
    clear_intersecting_modules,
    generate_qr_png,
)


class FakeQRCode:
    box_size = 10
    border = 0
    modules = [
        [True, True],
        [True, True],
    ]


def build_logo_file() -> io.BytesIO:
    logo_file = io.BytesIO()
    logo = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((18, 12, 62, 56), fill=(220, 40, 40, 255))
    draw.rectangle((36, 48, 45, 70), fill=(220, 40, 40, 255))
    logo.save(logo_file, format="PNG")
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


def test_generate_qr_png_supports_standard_quality():
    image_bytes = generate_qr_png("https://example.com", quality="standard")
    image = Image.open(io.BytesIO(image_bytes))

    assert image.size == (330, 330)


def test_generate_qr_png_supports_high_quality_by_default():
    image_bytes = generate_qr_png("https://example.com")
    image = Image.open(io.BytesIO(image_bytes))

    assert image.size == (528, 528)


def test_generate_qr_png_supports_very_high_quality():
    image_bytes = generate_qr_png("https://example.com", quality="very_high")
    image = Image.open(io.BytesIO(image_bytes))

    assert image.size == (792, 792)


def test_generate_qr_png_supports_custom_colors_and_shape():
    image_bytes = generate_qr_png(
        "https://example.com",
        foreground_color="#0f766e",
        background_color="#ffffff",
        module_style="rounded",
    )

    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_preserves_logo_colors():
    image_bytes = generate_qr_png(
        "https://example.com",
        foreground_color="#0f766e",
        background_color="#ffffff",
        module_style="circle",
        logo_file=build_logo_file(),
    )

    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    center = image.getpixel((image.width // 2, image.height // 2))
    assert center[0] > center[1]
    assert center[0] > center[2]


def test_clear_intersecting_modules_clears_whole_module():
    qr_code = FakeQRCode()

    clear_intersecting_modules(
        qr_code,
        (5, 5, 6, 6),
    )

    assert qr_code.modules == [
        [False, True],
        [True, True],
    ]


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


def test_generate_qr_png_rejects_unknown_quality():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("https://example.com", quality="ultra")


def test_generate_qr_png_rejects_blank_text():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("   ")
