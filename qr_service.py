from __future__ import annotations

import io
import re
from base64 import b64encode
from html import escape
from typing import BinaryIO, Final

import qrcode
from PIL import Image, UnidentifiedImageError
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import (
    HorizontalGradiantColorMask,
    RadialGradiantColorMask,
    SolidFillColorMask,
    SquareGradiantColorMask,
    VerticalGradiantColorMask,
)
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
DEFAULT_FOREGROUND_COLOR_2: Final[str] = "#0f766e"
DEFAULT_BACKGROUND_COLOR: Final[str] = "#ffffff"
DEFAULT_MODULE_STYLE: Final[str] = "square"
DEFAULT_EYE_STYLE: Final[str] = "square"
DEFAULT_QUALITY: Final[str] = "high"
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

MODULE_DRAWERS = {
    "square": SquareModuleDrawer,
    "rounded": lambda: RoundedModuleDrawer(radius_ratio=0.85),
    "circle": CircleModuleDrawer,
    "gapped": lambda: GappedSquareModuleDrawer(size_ratio=0.82),
    "vertical": lambda: VerticalBarsDrawer(horizontal_shrink=0.82),
    "horizontal": lambda: HorizontalBarsDrawer(vertical_shrink=0.82),
}

EYE_DRAWERS = {
    "square": SquareModuleDrawer,
    "rounded": lambda: RoundedModuleDrawer(radius_ratio=0.85),
    "circle": CircleModuleDrawer,
}

QUALITY_BOX_SIZES = {
    "low": 10,
    "medium": 16,
    "high": 24,
    "very_high": 30,
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


def build_color_mask(
    color_mode: str,
    foreground: tuple[int, int, int],
    foreground_2: tuple[int, int, int],
    background: tuple[int, int, int],
    transparent_background: bool,
):
    mode = resolve_color_mode(color_mode)
    back_color = (*background, 0) if transparent_background else background
    front_color = (*foreground, 255) if transparent_background else foreground
    front_color_2 = (*foreground_2, 255) if transparent_background else foreground_2

    if mode == "solid":
        return SolidFillColorMask(back_color=back_color, front_color=front_color)

    if mode == "horizontal":
        return HorizontalGradiantColorMask(
            back_color=back_color,
            left_color=front_color,
            right_color=front_color_2,
        )

    if mode == "vertical":
        return VerticalGradiantColorMask(
            back_color=back_color,
            top_color=front_color,
            bottom_color=front_color_2,
        )

    if mode == "radial":
        return RadialGradiantColorMask(
            back_color=back_color,
            center_color=front_color,
            edge_color=front_color_2,
        )

    return SquareGradiantColorMask(
        back_color=back_color,
        center_color=front_color,
        edge_color=front_color_2,
    )


def build_module_drawer(module_style: str):
    style = resolve_module_style(module_style)
    drawer_factory = MODULE_DRAWERS.get(style)
    return drawer_factory()


def resolve_module_style(module_style: str) -> str:
    style = DEFAULT_MODULE_STYLE if module_style is None else str(module_style).strip().lower()
    if not style:
        style = DEFAULT_MODULE_STYLE

    if style not in MODULE_DRAWERS:
        raise QRCodeRequestError("Selected QR code shape is not supported.")

    return style


def build_eye_drawer(eye_style: str, module_style: str):
    style = resolve_eye_style(eye_style)
    if style == "match":
        return build_module_drawer(module_style)

    return EYE_DRAWERS[style]()


def resolve_eye_style(eye_style: str) -> str:
    style = DEFAULT_EYE_STYLE if eye_style is None else str(eye_style).strip().lower()
    if not style:
        style = DEFAULT_EYE_STYLE

    if style != "match" and style not in EYE_DRAWERS:
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
    logo_size_ratio: float = DEFAULT_LOGO_SIZE_RATIO,
) -> tuple[Image.Image, tuple[int, int, int, int]] | None:
    logo_size = int(image_size * logo_size_ratio)
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


def trim_number(value: float | int) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def is_eye_module(row: int, col: int, module_count: int) -> bool:
    return (
        (row < 7 and col < 7)
        or (row < 7 and module_count - col < 8)
        or (module_count - row < 8 and col < 7)
    )


def svg_gradient_defs(
    color_mode: str,
    foreground: tuple[int, int, int],
    foreground_2: tuple[int, int, int],
) -> tuple[str, str]:
    mode = resolve_color_mode(color_mode)
    if mode == "solid":
        return "", color_to_hex(foreground)

    start_color = color_to_hex(foreground)
    end_color = color_to_hex(foreground_2)
    if mode == "horizontal":
        gradient = (
            '<linearGradient id="qr-gradient" x1="0%" y1="0%" x2="100%" y2="0%">'
        )
    elif mode == "vertical":
        gradient = (
            '<linearGradient id="qr-gradient" x1="0%" y1="0%" x2="0%" y2="100%">'
        )
    elif mode == "radial":
        gradient = '<radialGradient id="qr-gradient" cx="50%" cy="50%" r="70%">'
    else:
        gradient = (
            '<radialGradient id="qr-gradient" cx="50%" cy="50%" r="55%" '
            'fx="50%" fy="50%">'
        )

    tag_name = "radialGradient" if mode in {"radial", "square"} else "linearGradient"
    defs = (
        f"<defs>{gradient}"
        f'<stop offset="0%" stop-color="{start_color}"/>'
        f'<stop offset="100%" stop-color="{end_color}"/>'
        f"</{tag_name}></defs>"
    )
    return defs, "url(#qr-gradient)"


def svg_shape(style: str, x: int, y: int, box_size: int, fill: str) -> str:
    if style == "circle":
        radius = box_size / 2
        return (
            f'<circle cx="{trim_number(x + radius)}" cy="{trim_number(y + radius)}" '
            f'r="{trim_number(radius)}" fill="{fill}"/>'
        )

    if style == "gapped":
        ratio = 0.82
        size = box_size * ratio
        delta = (box_size - size) / 2
        return (
            f'<rect x="{trim_number(x + delta)}" y="{trim_number(y + delta)}" '
            f'width="{trim_number(size)}" height="{trim_number(size)}" fill="{fill}"/>'
        )

    if style == "rounded":
        radius = box_size * 0.32
        return (
            f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" '
            f'rx="{trim_number(radius)}" ry="{trim_number(radius)}" fill="{fill}"/>'
        )

    if style == "vertical":
        width = box_size * 0.62
        delta = (box_size - width) / 2
        radius = width / 2
        return (
            f'<rect x="{trim_number(x + delta)}" y="{y}" '
            f'width="{trim_number(width)}" height="{box_size}" '
            f'rx="{trim_number(radius)}" ry="{trim_number(radius)}" fill="{fill}"/>'
        )

    if style == "horizontal":
        height = box_size * 0.62
        delta = (box_size - height) / 2
        radius = height / 2
        return (
            f'<rect x="{x}" y="{trim_number(y + delta)}" '
            f'width="{box_size}" height="{trim_number(height)}" '
            f'rx="{trim_number(radius)}" ry="{trim_number(radius)}" fill="{fill}"/>'
        )

    return f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fill}"/>'


def logo_to_data_uri(logo: Image.Image) -> str:
    buffer = io.BytesIO()
    logo.save(buffer, format="PNG")
    encoded = b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def generate_qr_svg(
    text: str,
    *,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    foreground_color_2: str = DEFAULT_FOREGROUND_COLOR_2,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    eye_style: str = DEFAULT_EYE_STYLE,
    quality: str = DEFAULT_QUALITY,
    color_mode: str = DEFAULT_COLOR_MODE,
    transparent_background: bool | str = False,
    logo_size: str | float | int | None = DEFAULT_LOGO_SIZE_RATIO,
    logo_file: BinaryIO | None = None,
) -> bytes:
    value = "" if text is None else str(text).strip()
    if not value:
        raise QRCodeRequestError("Please enter a text or a link before generating a QR code.")

    foreground = normalize_hex_color(foreground_color, DEFAULT_FOREGROUND_COLOR, "QR color")
    foreground_2 = normalize_hex_color(
        foreground_color_2,
        DEFAULT_FOREGROUND_COLOR_2,
        "Second QR color",
    )
    background = normalize_hex_color(background_color, DEFAULT_BACKGROUND_COLOR, "Background color")
    is_transparent = parse_bool(transparent_background)
    if not is_transparent and contrast_ratio(foreground, background) < 3:
        raise QRCodeRequestError("QR color and background color need more contrast.")

    module_style = resolve_module_style(module_style)
    eye_style = resolve_eye_style(eye_style)
    color_mode = resolve_color_mode(color_mode)
    box_size = resolve_box_size(quality)
    logo_size_ratio = resolve_logo_size_ratio(logo_size)
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

    image_size = (qr_code.modules_count + qr_code.border * 2) * qr_code.box_size
    if logo:
        prepared_logo = prepare_logo(logo, image_size, logo_size_ratio)
        if prepared_logo:
            _, logo_box = prepared_logo
            clear_intersecting_modules(qr_code, logo_box)

    defs, fill = svg_gradient_defs(color_mode, foreground, foreground_2)
    background_rect = ""
    if not is_transparent:
        background_rect = (
            f'<rect width="100%" height="100%" fill="{color_to_hex(background)}"/>'
        )

    shapes = []
    module_count = qr_code.modules_count
    for row, module_row in enumerate(qr_code.modules):
        for col, is_active in enumerate(module_row):
            if not is_active:
                continue

            x = (col + qr_code.border) * box_size
            y = (row + qr_code.border) * box_size
            style = module_style
            if is_eye_module(row, col, module_count):
                style = module_style if eye_style == "match" else eye_style
            shapes.append(svg_shape(style, x, y, box_size, fill))

    logo_element = ""
    if prepared_logo:
        prepared_image, logo_box = prepared_logo
        left, top, right, bottom = logo_box
        logo_element = (
            f'<image x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" '
            f'href="{logo_to_data_uri(prepared_image)}"/>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{image_size}" '
        f'height="{image_size}" viewBox="0 0 {image_size} {image_size}" '
        f'role="img" aria-label="{escape(value)}">'
        f"{defs}{background_rect}{''.join(shapes)}{logo_element}</svg>"
    )
    return svg.encode("utf-8")


def generate_qr_png(
    text: str,
    *,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    foreground_color_2: str = DEFAULT_FOREGROUND_COLOR_2,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    eye_style: str = DEFAULT_EYE_STYLE,
    quality: str = DEFAULT_QUALITY,
    color_mode: str = DEFAULT_COLOR_MODE,
    transparent_background: bool | str = False,
    logo_size: str | float | int | None = DEFAULT_LOGO_SIZE_RATIO,
    logo_file: BinaryIO | None = None,
) -> bytes:
    value = "" if text is None else str(text).strip()
    if not value:
        raise QRCodeRequestError("Please enter a text or a link before generating a QR code.")

    foreground = normalize_hex_color(foreground_color, DEFAULT_FOREGROUND_COLOR, "QR color")
    foreground_2 = normalize_hex_color(
        foreground_color_2,
        DEFAULT_FOREGROUND_COLOR_2,
        "Second QR color",
    )
    background = normalize_hex_color(background_color, DEFAULT_BACKGROUND_COLOR, "Background color")
    is_transparent = parse_bool(transparent_background)
    if not is_transparent and contrast_ratio(foreground, background) < 3:
        raise QRCodeRequestError("QR color and background color need more contrast.")

    module_style = resolve_module_style(module_style)
    color_mode = resolve_color_mode(color_mode)
    box_size = resolve_box_size(quality)
    logo_size_ratio = resolve_logo_size_ratio(logo_size)
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
        prepared_logo = prepare_logo(logo, image_size, logo_size_ratio)
        if prepared_logo:
            _, logo_box = prepared_logo
            clear_intersecting_modules(qr_code, logo_box)

    image = qr_code.make_image(
        image_factory=StyledPilImage,
        module_drawer=build_module_drawer(module_style),
        eye_drawer=build_eye_drawer(eye_style, module_style),
        color_mask=build_color_mask(
            color_mode,
            foreground,
            foreground_2,
            background,
            is_transparent,
        ),
    )
    output_image = image.get_image()

    if prepared_logo:
        prepared_image, logo_box = prepared_logo
        output_image = paste_logo(output_image, prepared_image, logo_box)

    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_file(
    text: str,
    *,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    foreground_color_2: str = DEFAULT_FOREGROUND_COLOR_2,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    eye_style: str = DEFAULT_EYE_STYLE,
    quality: str = DEFAULT_QUALITY,
    color_mode: str = DEFAULT_COLOR_MODE,
    transparent_background: bool | str = False,
    logo_size: str | float | int | None = DEFAULT_LOGO_SIZE_RATIO,
    logo_file: BinaryIO | None = None,
) -> tuple[bytes, str, str]:
    file_format = resolve_output_format(output_format)
    generator = generate_qr_svg if file_format == "svg" else generate_qr_png
    file_bytes = generator(
        text,
        foreground_color=foreground_color,
        foreground_color_2=foreground_color_2,
        background_color=background_color,
        module_style=module_style,
        eye_style=eye_style,
        quality=quality,
        color_mode=color_mode,
        transparent_background=transparent_background,
        logo_size=logo_size,
        logo_file=logo_file,
    )
    mimetype = "image/svg+xml" if file_format == "svg" else "image/png"
    return file_bytes, mimetype, file_format
