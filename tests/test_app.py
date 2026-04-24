from app import create_app


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
