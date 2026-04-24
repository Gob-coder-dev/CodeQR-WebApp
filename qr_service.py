from __future__ import annotations

import io
import re
from typing import BinaryIO, Final

import qrcode
from PIL import Image, ImageOps, UnidentifiedImageError
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
DEFAULT_FOREGROUND_COLOR: Final[str] = "#102033"
DEFAULT_BACKGROUND_COLOR: Final[str] = "#ffffff"
DEFAULT_MODULE_STYLE: Final[str] = "square"
MAX_FILE_STEM_LENGTH: Final[int] = 80
MAX_LOGO_BYTES: Final[int] = 2 * 1024 * 1024
LOGO_CLEAR_AREA_RATIO: Final[float] = 0.28
LOGO_ART_RATIO: Final[float] = 0.22
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


def build_logo_mask(logo: Image.Image, target_size: int) -> Image.Image | None:
    alpha = logo.getchannel("A")
    has_transparency = alpha.getextrema()[0] < 255

    if has_transparency:
        mask = alpha
    else:
        grayscale = ImageOps.grayscale(logo)
        mask = grayscale.point(lambda value: 255 if value < 245 else 0)

    bbox = mask.getbbox()
    if bbox is None:
        return None

    mask = mask.crop(bbox)
    mask.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    canvas = Image.new("L", (target_size, target_size), 0)
    position = (
        (target_size - mask.width) // 2,
        (target_size - mask.height) // 2,
    )
    canvas.paste(mask, position)
    return canvas


def paste_integrated_logo(
    image: Image.Image,
    logo: Image.Image,
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
) -> Image.Image:
    canvas = image.convert("RGBA")
    width, _ = canvas.size
    clear_size = int(width * LOGO_CLEAR_AREA_RATIO)
    logo_size = int(width * LOGO_ART_RATIO)

    left = (width - clear_size) // 2
    top = left
    logo_left = (width - logo_size) // 2
    logo_top = logo_left

    background_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    background_patch = Image.new("RGBA", (clear_size, clear_size), (*background, 255))
    background_layer.paste(background_patch, (left, top))
    canvas = Image.alpha_composite(canvas, background_layer)

    logo_mask = build_logo_mask(logo, logo_size)
    if logo_mask is None:
        return canvas

    logo_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    logo_patch = Image.new("RGBA", (logo_size, logo_size), (*foreground, 255))
    logo_layer.paste(logo_patch, (logo_left, logo_top), logo_mask)
    return Image.alpha_composite(canvas, logo_layer)


def generate_qr_png(
    text: str,
    *,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    logo_file: BinaryIO | None = None,
) -> bytes:
    value = "" if text is None else str(text).strip()
    if not value:
        raise QRCodeRequestError("Please enter a text or a link before generating a QR code.")

    foreground = normalize_hex_color(foreground_color, DEFAULT_FOREGROUND_COLOR, "QR color")
    background = normalize_hex_color(background_color, DEFAULT_BACKGROUND_COLOR, "Background color")
    if contrast_ratio(foreground, background) < 3:
        raise QRCodeRequestError("QR color and background color need more contrast.")

    logo = load_logo_image(logo_file)
    qr_code = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H if logo else ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr_code.add_data(value)
    qr_code.make(fit=True)

    image = qr_code.make_image(
        image_factory=StyledPilImage,
        module_drawer=build_module_drawer(module_style),
        color_mask=SolidFillColorMask(
            back_color=background,
            front_color=foreground,
        ),
    )
    output_image = image.get_image()

    if logo:
        output_image = paste_integrated_logo(output_image, logo, foreground, background)

    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    return buffer.getvalue()
