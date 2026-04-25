import io

from PIL import Image, ImageDraw

from app import create_app


def build_logo_file() -> io.BytesIO:
    logo_file = io.BytesIO()
    logo = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((18, 12, 62, 56), fill=(220, 40, 40, 255))
    draw.rectangle((36, 48, 45, 70), fill=(220, 40, 40, 255))
    logo.save(logo_file, format="PNG")
    logo_file.seek(0)
    return logo_file


def test_index_page_renders():
    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Convertisseur QR" in response.data
    assert b"QR code personnalis" in response.data
    assert b"Logo central" in response.data
    assert b"foreground-color-hex" in response.data
    assert b"background-color-hex" in response.data
    assert b"preview-image" in response.data
    assert b"output-format" in response.data
    assert b"eye-style" in response.data
    assert b"transparent-background" in response.data
    assert b"logo-size" in response.data


def test_qr_code_endpoint_returns_png_download():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        json={"text": "https://example.com", "filename": "example"},
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert "attachment" in response.headers["Content-Disposition"]
    assert "example.png" in response.headers["Content-Disposition"]


def test_qr_code_endpoint_accepts_advanced_form_options():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "custom",
            "foreground_color": "#0f766e",
            "background_color": "#ffffff",
            "module_style": "rounded",
            "quality": "very_high",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert Image.open(io.BytesIO(response.data)).size == (990, 990)
    assert "custom.png" in response.headers["Content-Disposition"]


def test_qr_code_endpoint_accepts_logo_upload():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "with-logo",
            "foreground_color": "#000000",
            "background_color": "#ffffff",
            "module_style": "circle",
            "logo": (build_logo_file(), "logo.png"),
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert "with-logo.png" in response.headers["Content-Disposition"]


def test_qr_code_endpoint_returns_svg_download():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "custom",
            "output_format": "svg",
            "foreground_color": "#000000",
            "background_color": "#ffffff",
            "module_style": "circle",
            "eye_style": "rounded",
            "color_mode": "horizontal",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert response.data.startswith(b"<svg")
    assert "custom.svg" in response.headers["Content-Disposition"]


def test_qr_code_endpoint_rejects_invalid_advanced_option():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "custom",
            "foreground_color": "#ffffff",
            "background_color": "#ffffff",
        },
    )

    assert response.status_code == 400
    assert response.json == {
        "error": "QR color and background color need more contrast."
    }


def test_qr_code_endpoint_rejects_invalid_quality():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "custom",
            "quality": "ultra",
        },
    )

    assert response.status_code == 400
    assert response.json == {
        "error": "Selected QR code quality is not supported."
    }


def test_qr_code_endpoint_rejects_empty_text():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        json={"text": "   ", "filename": "example"},
    )

    assert response.status_code == 400
    assert response.json == {
        "error": "Please enter a text or a link before generating a QR code."
    }


def test_health_endpoint_returns_ok():
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
