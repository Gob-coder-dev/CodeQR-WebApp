import pytest

from qr_payload import build_qr_payload
from qr_service import QRCodeRequestError


def test_build_qr_payload_keeps_text_type_as_raw_value():
    assert build_qr_payload({"qr_type": "text", "text": "https://example.com"}) == (
        "https://example.com"
    )


def test_build_qr_payload_builds_wifi_payload():
    payload = build_qr_payload(
        {
            "qr_type": "wifi",
            "wifi_ssid": "Cafe;Demo",
            "wifi_security": "WPA",
            "wifi_password": "pa:ss",
            "wifi_hidden": "on",
        }
    )

    assert payload == "WIFI:T:WPA;S:Cafe\\;Demo;P:pa\\:ss;H:true;;"


def test_build_qr_payload_supports_wifi_without_password():
    payload = build_qr_payload(
        {
            "qr_type": "wifi",
            "wifi_ssid": "Open Network",
            "wifi_security": "nopass",
        }
    )

    assert payload == "WIFI:T:nopass;S:Open Network;P:;H:false;;"


def test_build_qr_payload_builds_email_payload():
    payload = build_qr_payload(
        {
            "qr_type": "email",
            "email_to": "contact@example.com",
            "email_subject": "Bonjour",
            "email_body": "Message de test",
        }
    )

    assert payload == "mailto:contact@example.com?subject=Bonjour&body=Message+de+test"


def test_build_qr_payload_builds_phone_payload():
    assert build_qr_payload({"qr_type": "phone", "phone_number": "+33 6 12 34 56 78"}) == (
        "tel:+33612345678"
    )


def test_build_qr_payload_normalizes_french_local_phone_payload():
    assert build_qr_payload(
        {
            "qr_type": "phone",
            "phone_number": "06 12 34 56 78",
            "ui_language": "fr",
        }
    ) == "tel:+33612345678"


def test_build_qr_payload_builds_sms_payload():
    payload = build_qr_payload(
        {
            "qr_type": "sms",
            "sms_number": "+33 6 12 34 56 78",
            "sms_message": "Bonjour a tous",
        }
    )

    assert payload == "sms:+33612345678?body=Bonjour%20a%20tous"


def test_build_qr_payload_builds_contact_payload():
    payload = build_qr_payload(
        {
            "qr_type": "contact",
            "contact_first_name": "Jean",
            "contact_last_name": "Dupont",
            "contact_org": "Demo",
            "contact_phone": "+33 1 23 45 67 89",
            "contact_email": "mail@example.com",
            "contact_url": "https://example.com",
        }
    )

    assert payload == "\r\n".join(
        [
            "BEGIN:VCARD",
            "VERSION:3.0",
            "N:Dupont;Jean;;;",
            "FN:Jean Dupont",
            "ORG:Demo",
            "TEL;TYPE=CELL:+33123456789",
            "EMAIL;TYPE=INTERNET:mail@example.com",
            "URL:https://example.com",
            "END:VCARD",
        ]
    )


def test_build_qr_payload_keeps_legacy_contact_name_compatible():
    payload = build_qr_payload(
        {
            "qr_type": "contact",
            "contact_name": "Yanis Demo",
        }
    )

    assert "N:Demo;Yanis;;;" in payload
    assert "FN:Yanis Demo" in payload


def test_build_qr_payload_builds_location_payload():
    assert build_qr_payload(
        {
            "qr_type": "location",
            "location_latitude": "48.8566",
            "location_longitude": "2.3522",
        }
    ) == "geo:48.8566,2.3522"


def test_build_qr_payload_rejects_invalid_location():
    with pytest.raises(QRCodeRequestError):
        build_qr_payload(
            {
                "qr_type": "location",
                "location_latitude": "120",
                "location_longitude": "2.3522",
            }
        )


def test_build_qr_payload_rejects_unknown_type():
    with pytest.raises(QRCodeRequestError):
        build_qr_payload({"qr_type": "event"})
