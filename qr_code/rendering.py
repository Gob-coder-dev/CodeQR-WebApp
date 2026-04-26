from __future__ import annotations

import io
from base64 import b64encode
from typing import BinaryIO

import qrcode
from PIL import Image, UnidentifiedImageError
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

from qr_code.options import (
    DEFAULT_LOGO_SIZE_RATIO,
    DEFAULT_MODULE_STYLE,
    MAX_LOGO_BYTES,
    QRCodeRequestError,
    color_to_hex,
    resolve_color_mode,
    resolve_eye_style,
    resolve_module_style,
)


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
    style = resolve_module_style(module_style, MODULE_DRAWERS)
    drawer_factory = MODULE_DRAWERS.get(style)
    return drawer_factory()


def build_eye_drawer(eye_style: str, module_style: str):
    style = resolve_eye_style(eye_style, EYE_DRAWERS)
    if style == "match":
        return build_module_drawer(module_style)

    return EYE_DRAWERS[style]()


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
