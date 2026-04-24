import io

from PIL import Image

from app import create_app


def build_logo_file() -> io.BytesIO:
    logo_file = io.BytesIO()
    Image.new("RGBA", (80, 80), (15, 118, 110, 255)).save(logo_file, format="PNG")
    logo_file.seek(0)
    return logo_file


def test_index_page_renders():
    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Convertisseur QR" in response.data


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
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert "custom.png" in response.headers["Content-Disposition"]


def test_qr_code_endpoint_accepts_logo_upload():
    client = create_app().test_client()

    response = client.post(
        "/api/qr-code",
        data={
            "text": "https://example.com",
            "filename": "with-logo",
            "foreground_color": "#102033",
            "background_color": "#ffffff",
            "module_style": "circle",
            "logo": (build_logo_file(), "logo.png"),
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert "with-logo.png" in response.headers["Content-Disposition"]


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
