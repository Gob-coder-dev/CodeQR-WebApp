import pytest

from qr_service import QRCodeRequestError, build_download_name, generate_qr_png


def test_build_download_name_adds_extension_when_missing():
    assert build_download_name("my-file") == "my-file.png"


def test_build_download_name_sanitizes_invalid_characters():
    assert build_download_name('bad:/\\name?.png') == "bad-name.png"


def test_build_download_name_uses_default_for_blank_input():
    assert build_download_name("   ") == "qr-code.png"


def test_generate_qr_png_returns_png_signature():
    image_bytes = generate_qr_png("https://example.com")
    assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_png_rejects_blank_text():
    with pytest.raises(QRCodeRequestError):
        generate_qr_png("   ")
