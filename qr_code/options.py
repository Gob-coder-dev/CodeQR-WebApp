from __future__ import annotations

import re
from typing import Final

from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)


DEFAULT_FILE_STEM: Final[str] = "qr-code"
DEFAULT_FOREGROUND_COLOR: Final[str] = "#000000"
DEFAULT_FOREGROUND_COLOR_2: Final[str] = "#0f766e"
DEFAULT_BACKGROUND_COLOR: Final[str] = "#ffffff"
DEFAULT_MODULE_STYLE: Final[str] = "square"
DEFAULT_EYE_STYLE: Final[str] = "square"
DEFAULT_QUALITY: Final[str] = "high"
DEFAULT_ERROR_CORRECTION: Final[str] = "medium"
DEFAULT_BORDER_SIZE: Final[str] = "standard"
DEFAULT_COLOR_MODE: Final[str] = "solid"
DEFAULT_OUTPUT_FORMAT: Final[str] = "png"
DEFAULT_LOGO_SIZE_RATIO: Final[float] = 0.22
MIN_LOGO_SIZE_RATIO: Final[float] = 0.1
MAX_LOGO_SIZE_RATIO: Final[float] = 0.3
MAX_FILE_STEM_LENGTH: Final[int] = 80
MAX_LOGO_BYTES: Final[int] = 2 * 1024 * 1024

INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
WHITESPACE = re.compile(r"\s+")
MULTIPLE_DASHES = re.compile(r"-{2,}")
HEX_COLOR = re.compile(r"^#?[0-9a-fA-F]{6}$")

QUALITY_BOX_SIZES = {
    "low": 10,
    "medium": 16,
    "high": 24,
    "very_high": 30,
}

ERROR_CORRECTION_LEVELS = {
    "low": ERROR_CORRECT_L,
    "medium": ERROR_CORRECT_M,
    "quartile": ERROR_CORRECT_Q,
    "high": ERROR_CORRECT_H,
}

BORDER_SIZES = {
    "small": 2,
    "standard": 4,
    "large": 6,
}

COLOR_MODES = {"solid", "horizontal", "vertical", "radial", "square"}
OUTPUT_FORMATS = {"png", "svg"}


class QRCodeRequestError(ValueError):
    """Raised when a QR code request is invalid."""


def build_download_name(raw_name: str, extension: str = "png") -> str:
    stem = "" if raw_name is None else str(raw_name).strip()
    extension = resolve_output_format(extension)

    for suffix in (".png", ".svg"):
        if stem.lower().endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    stem = INVALID_FILE_CHARS.sub("-", stem)
    stem = WHITESPACE.sub("-", stem)
    stem = MULTIPLE_DASHES.sub("-", stem)
    stem = stem.strip(" .-_")

    if not stem:
        stem = DEFAULT_FILE_STEM

    stem = stem[:MAX_FILE_STEM_LENGTH].rstrip(" .-_")

    if not stem:
        stem = DEFAULT_FILE_STEM

    return f"{stem}.{extension}"


def normalize_hex_color(raw_color: str, default_color: str, field_name: str) -> tuple[int, int, int]:
    color = default_color if raw_color is None else str(raw_color).strip()
    if not color:
        color = default_color

    if not HEX_COLOR.fullmatch(color):
        raise QRCodeRequestError(f"{field_name} must be a hexadecimal color.")

    color = color.removeprefix("#")
    return tuple(int(color[index : index + 2], 16) for index in (0, 2, 4))


def relative_luminance(color: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        value = value / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(value) for value in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
) -> float:
    darker, lighter = sorted(
        (relative_luminance(foreground), relative_luminance(background))
    )
    return (lighter + 0.05) / (darker + 0.05)


def color_to_hex(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def resolve_module_style(module_style: str, supported_styles) -> str:
    style = DEFAULT_MODULE_STYLE if module_style is None else str(module_style).strip().lower()
    if not style:
        style = DEFAULT_MODULE_STYLE

    if style not in supported_styles:
        raise QRCodeRequestError("Selected QR code shape is not supported.")

    return style


def resolve_eye_style(eye_style: str, supported_styles) -> str:
    style = DEFAULT_EYE_STYLE if eye_style is None else str(eye_style).strip().lower()
    if not style:
        style = DEFAULT_EYE_STYLE

    if style != "match" and style not in supported_styles:
        raise QRCodeRequestError("Selected QR code eye style is not supported.")

    return style


def resolve_box_size(quality: str) -> int:
    value = DEFAULT_QUALITY if quality is None else str(quality).strip().lower()
    if not value:
        value = DEFAULT_QUALITY

    box_size = QUALITY_BOX_SIZES.get(value)
    if box_size is None:
        raise QRCodeRequestError("Selected QR code quality is not supported.")

    return box_size


def resolve_error_correction(error_correction: str, has_logo: bool = False) -> int:
    value = (
        DEFAULT_ERROR_CORRECTION
        if error_correction is None
        else str(error_correction).strip().lower()
    )
    if not value:
        value = "high" if has_logo else DEFAULT_ERROR_CORRECTION

    level = ERROR_CORRECTION_LEVELS.get(value)
    if level is None:
        raise QRCodeRequestError("Selected error correction level is not supported.")

    if has_logo:
        return ERROR_CORRECT_H

    return level


def resolve_border_size(border_size: str) -> int:
    value = DEFAULT_BORDER_SIZE if border_size is None else str(border_size).strip().lower()
    if not value:
        value = DEFAULT_BORDER_SIZE

    border = BORDER_SIZES.get(value)
    if border is None:
        raise QRCodeRequestError("Selected QR code margin is not supported.")

    return border


def resolve_output_format(output_format: str) -> str:
    value = DEFAULT_OUTPUT_FORMAT if output_format is None else str(output_format).strip().lower()
    if not value:
        value = DEFAULT_OUTPUT_FORMAT

    if value not in OUTPUT_FORMATS:
        raise QRCodeRequestError("Selected file format is not supported.")

    return value


def resolve_color_mode(color_mode: str) -> str:
    value = DEFAULT_COLOR_MODE if color_mode is None else str(color_mode).strip().lower()
    if not value:
        value = DEFAULT_COLOR_MODE

    if value not in COLOR_MODES:
        raise QRCodeRequestError("Selected color mode is not supported.")

    return value


def resolve_logo_size_ratio(raw_ratio: str | float | int | None) -> float:
    if raw_ratio is None or raw_ratio == "":
        return DEFAULT_LOGO_SIZE_RATIO

    try:
        ratio = float(raw_ratio)
    except (TypeError, ValueError) as error:
        raise QRCodeRequestError("Logo size must be a number.") from error

    if ratio > 1:
        ratio = ratio / 100

    if ratio < MIN_LOGO_SIZE_RATIO or ratio > MAX_LOGO_SIZE_RATIO:
        raise QRCodeRequestError("Logo size must stay between 10% and 30%.")

    return ratio


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value

    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
