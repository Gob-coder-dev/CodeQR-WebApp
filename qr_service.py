from __future__ import annotations

import io
import re
from typing import BinaryIO, Final

import qrcode
from PIL import Image, UnidentifiedImageError
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import (
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
    HorizontalBarsDrawer,
    RoundedModuleDrawer,
    SquareModuleDrawer,
    VerticalBarsDrawer,
)


DEFAULT_FILE_STEM: Final[str] = "qr-code"
DEFAULT_FOREGROUND_COLOR: Final[str] = "#000000"
DEFAULT_BACKGROUND_COLOR: Final[str] = "#ffffff"
DEFAULT_MODULE_STYLE: Final[str] = "square"
DEFAULT_QUALITY: Final[str] = "high"
MAX_FILE_STEM_LENGTH: Final[int] = 80
MAX_LOGO_BYTES: Final[int] = 2 * 1024 * 1024
LOGO_IMAGE_RATIO: Final[float] = 0.22
INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
WHITESPACE = re.compile(r"\s+")
MULTIPLE_DASHES = re.compile(r"-{2,}")
HEX_COLOR = re.compile(r"^#?[0-9a-fA-F]{6}$")

MODULE_DRAWERS = {
    "square": SquareModuleDrawer,
    "rounded": lambda: RoundedModuleDrawer(radius_ratio=0.85),
    "circle": CircleModuleDrawer,
    "gapped": lambda: GappedSquareModuleDrawer(size_ratio=0.82),
    "vertical": lambda: VerticalBarsDrawer(horizontal_shrink=0.82),
    "horizontal": lambda: HorizontalBarsDrawer(vertical_shrink=0.82),
}

QUALITY_BOX_SIZES = {
    "low": 10,
    "medium": 16,
    "high": 24,
    "very_high": 30,
}


class QRCodeRequestError(ValueError):
    """Raised when a QR code request is invalid."""


def build_download_name(raw_name: str) -> str:
    stem = "" if raw_name is None else str(raw_name).strip()

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


def build_module_drawer(module_style: str):
    style = DEFAULT_MODULE_STYLE if module_style is None else str(module_style).strip().lower()
    if not style:
        style = DEFAULT_MODULE_STYLE
    drawer_factory = MODULE_DRAWERS.get(style)
    if drawer_factory is None:
        raise QRCodeRequestError("Selected QR code shape is not supported.")

    return drawer_factory()


def resolve_box_size(quality: str) -> int:
    value = DEFAULT_QUALITY if quality is None else str(quality).strip().lower()
    if not value:
        value = DEFAULT_QUALITY

    box_size = QUALITY_BOX_SIZES.get(value)
    if box_size is None:
        raise QRCodeRequestError("Selected QR code quality is not supported.")

    return box_size


def load_logo_image(logo_file: BinaryIO | None) -> Image.Image | None:
    if logo_file is None:
        return None

    logo_bytes = logo_file.read(MAX_LOGO_BYTES + 1)
    if not logo_bytes:
        return None

    if len(logo_bytes) > MAX_LOGO_BYTES:
        raise QRCodeRequestError("Logo image must be 2 MB or smaller.")

    try:
        logo = Image.open(io.BytesIO(logo_bytes))
        logo.load()
    except (OSError, UnidentifiedImageError) as error:
        raise QRCodeRequestError("Logo must be a valid PNG, JPEG, or WebP image.") from error

    return logo.convert("RGBA")


def paste_logo(
    image: Image.Image,
    logo: Image.Image,
    logo_box: tuple[int, int, int, int],
) -> Image.Image:
    canvas = image.convert("RGBA")
    logo_left, logo_top, _, _ = logo_box
    canvas.alpha_composite(logo, (logo_left, logo_top))
    return canvas


def prepare_logo(
    logo: Image.Image,
    image_size: int,
) -> tuple[Image.Image, tuple[int, int, int, int]] | None:
    logo_size = int(image_size * LOGO_IMAGE_RATIO)
    logo = crop_transparent_padding(logo)
    if logo is None:
        return None

    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
    if logo.width == 0 or logo.height == 0:
        return None

    logo_left = (image_size - logo.width) // 2
    logo_top = (image_size - logo.height) // 2
    logo_box = (logo_left, logo_top, logo_left + logo.width, logo_top + logo.height)
    return logo, logo_box


def crop_transparent_padding(logo: Image.Image) -> Image.Image | None:
    logo = logo.copy()
    alpha_bbox = logo.getchannel("A").getbbox()
    if alpha_bbox is None:
        return None

    return logo.crop(alpha_bbox)


def clear_intersecting_modules(
    qr_code: qrcode.QRCode,
    clear_box: tuple[int, int, int, int],
) -> None:
    box_size = qr_code.box_size
    border = qr_code.border

    for row, module_row in enumerate(qr_code.modules):
        for col, is_active in enumerate(module_row):
            if not is_active:
                continue

            left = (col + border) * box_size
            top = (row + border) * box_size
            right = left + box_size
            bottom = top + box_size

            if not boxes_intersect((left, top, right, bottom), clear_box):
                continue

            qr_code.modules[row][col] = False


def boxes_intersect(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    first_left, first_top, first_right, first_bottom = first
    second_left, second_top, second_right, second_bottom = second
    return (
        first_left < second_right
        and first_right > second_left
        and first_top < second_bottom
        and first_bottom > second_top
    )


def generate_qr_png(
    text: str,
    *,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    quality: str = DEFAULT_QUALITY,
    logo_file: BinaryIO | None = None,
) -> bytes:
    value = "" if text is None else str(text).strip()
    if not value:
        raise QRCodeRequestError("Please enter a text or a link before generating a QR code.")

    foreground = normalize_hex_color(foreground_color, DEFAULT_FOREGROUND_COLOR, "QR color")
    background = normalize_hex_color(background_color, DEFAULT_BACKGROUND_COLOR, "Background color")
    if contrast_ratio(foreground, background) < 3:
        raise QRCodeRequestError("QR color and background color need more contrast.")

    box_size = resolve_box_size(quality)
    logo = load_logo_image(logo_file)
    prepared_logo = None
    qr_code = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H if logo else ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr_code.add_data(value)
    qr_code.make(fit=True)

    if logo:
        image_size = (qr_code.modules_count + qr_code.border * 2) * qr_code.box_size
        prepared_logo = prepare_logo(logo, image_size)
        if prepared_logo:
            _, logo_box = prepared_logo
            clear_intersecting_modules(qr_code, logo_box)

    image = qr_code.make_image(
        image_factory=StyledPilImage,
        module_drawer=build_module_drawer(module_style),
        color_mask=SolidFillColorMask(
            back_color=background,
            front_color=foreground,
        ),
    )
    output_image = image.get_image()

    if prepared_logo:
        prepared_image, logo_box = prepared_logo
        output_image = paste_logo(output_image, prepared_image, logo_box)

    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    return buffer.getvalue()
