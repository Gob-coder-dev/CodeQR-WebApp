from __future__ import annotations

from urllib.parse import quote, urlencode

from qr_code.options import QRCodeRequestError, parse_bool


DEFAULT_QR_TYPE = "text"
SUPPORTED_QR_TYPES = {
    "text",
    "wifi",
    "email",
    "phone",
    "sms",
    "contact",
    "location",
}
WIFI_SECURITY_TYPES = {"WPA", "WEP", "nopass"}
LOCAL_PHONE_PREFIXES = {
    "fr": ("33", 10, "0"),
    "es": ("34", 9, ""),
    "en": ("1", 10, ""),
}


def payload_value(payload, key: str) -> str:
    return str(payload.get(key, "") or "").strip()


def require_value(payload, key: str, message: str) -> str:
    value = payload_value(payload, key)
    if not value:
        raise QRCodeRequestError(message)

    return value


def build_qr_payload(payload) -> str:
    qr_type = payload_value(payload, "qr_type").lower() or DEFAULT_QR_TYPE
    if qr_type not in SUPPORTED_QR_TYPES:
        raise QRCodeRequestError("Selected QR code type is not supported.")

    if qr_type == "text":
        return require_value(
            payload,
            "text",
            "Please enter a text or a link before generating a QR code.",
        )

    if qr_type == "wifi":
        return build_wifi_payload(payload)

    if qr_type == "email":
        return build_email_payload(payload)

    if qr_type == "phone":
        return f"tel:{normalize_phone_number(require_value(payload, 'phone_number', 'Please enter a phone number.'), payload)}"

    if qr_type == "sms":
        return build_sms_payload(payload)

    if qr_type == "contact":
        return build_contact_payload(payload)

    return build_location_payload(payload)


def escape_wifi_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace('"', '\\"')
        .replace(":", "\\:")
    )


def build_wifi_payload(payload) -> str:
    ssid = require_value(payload, "wifi_ssid", "Please enter a Wi-Fi network name.")
    raw_security = payload_value(payload, "wifi_security")
    if not raw_security:
        security = "WPA"
    elif raw_security.lower() in {"nopass", "none"}:
        security = "nopass"
    else:
        security = raw_security.upper()

    if security not in WIFI_SECURITY_TYPES:
        raise QRCodeRequestError("Selected Wi-Fi security type is not supported.")

    password = payload_value(payload, "wifi_password")
    hidden = "true" if parse_bool(payload.get("wifi_hidden")) else "false"

    return (
        f"WIFI:T:{security};"
        f"S:{escape_wifi_value(ssid)};"
        f"P:{escape_wifi_value(password)};"
        f"H:{hidden};;"
    )


def build_email_payload(payload) -> str:
    recipient = require_value(payload, "email_to", "Please enter an email recipient.")
    query = {
        key: value
        for key, value in {
            "subject": payload_value(payload, "email_subject"),
            "body": payload_value(payload, "email_body"),
        }.items()
        if value
    }

    if not query:
        return f"mailto:{recipient}"

    return f"mailto:{recipient}?{urlencode(query)}"


def build_sms_payload(payload) -> str:
    phone_number = require_value(payload, "sms_number", "Please enter an SMS phone number.")
    message = payload_value(payload, "sms_message")
    if not message:
        return f"sms:{normalize_phone_number(phone_number, payload)}"

    return f"sms:{normalize_phone_number(phone_number, payload)}?body={quote(message)}"


def normalize_phone_number(value: str, payload) -> str:
    raw_value = value.strip()
    has_plus = raw_value.startswith("+")
    digits = "".join(character for character in raw_value if character.isdigit())

    if has_plus:
        return f"+{digits}"

    if digits.startswith("00") and len(digits) > 2:
        return f"+{digits[2:]}"

    language = payload_value(payload, "ui_language").lower()
    country_code, expected_length, trunk_prefix = LOCAL_PHONE_PREFIXES.get(
        language,
        ("", 0, ""),
    )
    if country_code and len(digits) == expected_length:
        if trunk_prefix:
            if digits.startswith(trunk_prefix):
                return f"+{country_code}{digits[len(trunk_prefix):]}"
        else:
            return f"+{country_code}{digits}"

    return digits or raw_value


def escape_vcard_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def split_full_name(full_name: str) -> tuple[str, str]:
    name_parts = full_name.split()
    if len(name_parts) <= 1:
        return full_name, ""

    return " ".join(name_parts[:-1]), name_parts[-1]


def build_contact_payload(payload) -> str:
    first_name = payload_value(payload, "contact_first_name")
    last_name = payload_value(payload, "contact_last_name")
    legacy_full_name = payload_value(payload, "contact_name")
    if not first_name and not last_name and legacy_full_name:
        first_name, last_name = split_full_name(legacy_full_name)

    if not first_name or not last_name:
        raise QRCodeRequestError("Please enter a contact first name and last name.")

    full_name = f"{first_name} {last_name}".strip()
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{escape_vcard_value(last_name)};{escape_vcard_value(first_name)};;;",
        f"FN:{escape_vcard_value(full_name)}",
    ]

    optional_fields = [
        ("contact_org", "ORG"),
        ("contact_phone", "TEL;TYPE=CELL"),
        ("contact_email", "EMAIL;TYPE=INTERNET"),
        ("contact_url", "URL"),
    ]
    for field_name, vcard_name in optional_fields:
        value = payload_value(payload, field_name)
        if value:
            if field_name == "contact_phone":
                value = normalize_phone_number(value, payload)
            lines.append(f"{vcard_name}:{escape_vcard_value(value)}")

    lines.append("END:VCARD")
    return "\r\n".join(lines)


def build_location_payload(payload) -> str:
    latitude = require_value(payload, "location_latitude", "Please enter a latitude.")
    longitude = require_value(payload, "location_longitude", "Please enter a longitude.")
    validate_coordinate(latitude, -90, 90, "Latitude")
    validate_coordinate(longitude, -180, 180, "Longitude")
    return f"geo:{latitude},{longitude}"


def validate_coordinate(value: str, minimum: int, maximum: int, field_name: str) -> None:
    try:
        coordinate = float(value)
    except ValueError as error:
        raise QRCodeRequestError(f"{field_name} must be a valid number.") from error

    if coordinate < minimum or coordinate > maximum:
        raise QRCodeRequestError(f"{field_name} is outside the valid range.")
