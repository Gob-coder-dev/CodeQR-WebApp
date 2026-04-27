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

SVG_GAPPED_RATIO = 0.82
SVG_BAR_RATIO = 0.82
SVG_ROUNDED_RADIUS_RATIO = 0.42


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
    image_size: int | None = None,
) -> tuple[str, str]:
    mode = resolve_color_mode(color_mode)
    if mode == "solid":
        return "", color_to_hex(foreground)

    start_color = color_to_hex(foreground)
    end_color = color_to_hex(foreground_2)
    if image_size is None:
        horizontal_coords = 'x1="0%" y1="0%" x2="100%" y2="0%"'
        vertical_coords = 'x1="0%" y1="0%" x2="0%" y2="100%"'
        radial_coords = 'cx="50%" cy="50%" r="70%"'
        square_coords = 'cx="50%" cy="50%" r="55%" fx="50%" fy="50%"'
        gradient_units = ""
    else:
        midpoint = trim_number(image_size / 2)
        horizontal_coords = f'x1="0" y1="0" x2="{image_size}" y2="0"'
        vertical_coords = f'x1="0" y1="0" x2="0" y2="{image_size}"'
        radial_coords = (
            f'cx="{midpoint}" cy="{midpoint}" '
            f'r="{trim_number(image_size * 0.7)}"'
        )
        square_coords = (
            f'cx="{midpoint}" cy="{midpoint}" '
            f'r="{trim_number(image_size * 0.55)}" '
            f'fx="{midpoint}" fy="{midpoint}"'
        )
        gradient_units = ' gradientUnits="userSpaceOnUse"'

    if mode == "horizontal":
        gradient = f'<linearGradient id="qr-gradient" {horizontal_coords}{gradient_units}>'
    elif mode == "vertical":
        gradient = f'<linearGradient id="qr-gradient" {vertical_coords}{gradient_units}>'
    elif mode == "radial":
        gradient = f'<radialGradient id="qr-gradient" {radial_coords}{gradient_units}>'
    else:
        gradient = f'<radialGradient id="qr-gradient" {square_coords}{gradient_units}>'

    tag_name = "radialGradient" if mode in {"radial", "square"} else "linearGradient"
    defs = (
        f"<defs>{gradient}"
        f'<stop offset="0%" stop-color="{start_color}"/>'
        f'<stop offset="100%" stop-color="{end_color}"/>'
        f"</{tag_name}></defs>"
    )
    return defs, "url(#qr-gradient)"


def module_position(row: int, col: int, border: int, box_size: int) -> tuple[int, int]:
    return (col + border) * box_size, (row + border) * box_size


def is_styled_module(
    style_grid: list[list[str | None]],
    row: int,
    col: int,
    style: str,
) -> bool:
    return (
        0 <= row < len(style_grid)
        and 0 <= col < len(style_grid[row])
        and style_grid[row][col] == style
    )


def svg_path_element(path_data: list[str], fill: str) -> list[str]:
    if not path_data:
        return []

    return [f'<path d="{"".join(path_data)}" fill="{fill}"/>']


def svg_rect(
    x: float | int,
    y: float | int,
    width: float | int,
    height: float | int,
    fill: str,
    *,
    radius: float | int = 0,
) -> str:
    radius_attributes = ""
    if radius:
        radius_attributes = (
            f' rx="{trim_number(radius)}" ry="{trim_number(radius)}"'
        )

    return (
        f'<rect x="{trim_number(x)}" y="{trim_number(y)}" '
        f'width="{trim_number(width)}" height="{trim_number(height)}"'
        f'{radius_attributes} fill="{fill}"/>'
    )


def svg_square_runs(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    path_data = []
    module_count = len(style_grid)
    for row in range(module_count):
        col = 0
        while col < module_count:
            if style_grid[row][col] != "square":
                col += 1
                continue

            start_col = col
            while col < module_count and style_grid[row][col] == "square":
                col += 1

            x, y = module_position(row, start_col, border, box_size)
            width = (col - start_col) * box_size
            right = x + width
            bottom = y + box_size
            path_data.append(
                f"M{trim_number(x)},{trim_number(y)}"
                f"H{trim_number(right)}V{trim_number(bottom)}"
                f"H{trim_number(x)}z"
            )

    return svg_path_element(path_data, fill)


def svg_rounded_module_path(
    style_grid: list[list[str | None]],
    row: int,
    col: int,
    border: int,
    box_size: int,
) -> str:
    x, y = module_position(row, col, border, box_size)
    right = x + box_size
    bottom = y + box_size
    radius = box_size * SVG_ROUNDED_RADIUS_RATIO

    has_north = is_styled_module(style_grid, row - 1, col, "rounded")
    has_east = is_styled_module(style_grid, row, col + 1, "rounded")
    has_south = is_styled_module(style_grid, row + 1, col, "rounded")
    has_west = is_styled_module(style_grid, row, col - 1, "rounded")

    round_nw = not has_north and not has_west
    round_ne = not has_north and not has_east
    round_se = not has_south and not has_east
    round_sw = not has_south and not has_west

    top_left_x = x + radius if round_nw else x
    top_right_x = right - radius if round_ne else right
    right_top_y = y + radius if round_ne else y
    right_bottom_y = bottom - radius if round_se else bottom
    bottom_right_x = right - radius if round_se else right
    bottom_left_x = x + radius if round_sw else x
    left_bottom_y = bottom - radius if round_sw else bottom
    left_top_y = y + radius if round_nw else y

    parts = [
        f"M{trim_number(top_left_x)},{trim_number(y)}",
        f"L{trim_number(top_right_x)},{trim_number(y)}",
    ]
    if round_ne:
        parts.append(
            f"Q{trim_number(right)},{trim_number(y)} "
            f"{trim_number(right)},{trim_number(right_top_y)}"
        )
    else:
        parts.append(f"L{trim_number(right)},{trim_number(y)}")

    parts.append(f"L{trim_number(right)},{trim_number(right_bottom_y)}")
    if round_se:
        parts.append(
            f"Q{trim_number(right)},{trim_number(bottom)} "
            f"{trim_number(bottom_right_x)},{trim_number(bottom)}"
        )
    else:
        parts.append(f"L{trim_number(right)},{trim_number(bottom)}")

    parts.append(f"L{trim_number(bottom_left_x)},{trim_number(bottom)}")
    if round_sw:
        parts.append(
            f"Q{trim_number(x)},{trim_number(bottom)} "
            f"{trim_number(x)},{trim_number(left_bottom_y)}"
        )
    else:
        parts.append(f"L{trim_number(x)},{trim_number(bottom)}")

    parts.append(f"L{trim_number(x)},{trim_number(left_top_y)}")
    if round_nw:
        parts.append(
            f"Q{trim_number(x)},{trim_number(y)} "
            f"{trim_number(top_left_x)},{trim_number(y)}"
        )
    else:
        parts.append(f"L{trim_number(x)},{trim_number(y)}")

    parts.append("z")
    return "".join(parts)


def svg_rounded_modules(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    path_data = []
    for row, module_row in enumerate(style_grid):
        for col, style in enumerate(module_row):
            if style == "rounded":
                path_data.append(svg_rounded_module_path(style_grid, row, col, border, box_size))

    return svg_path_element(path_data, fill)


def svg_vertical_runs(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    shapes = []
    module_count = len(style_grid)
    width = box_size * SVG_BAR_RATIO
    delta = (box_size - width) / 2
    radius = width / 2

    for col in range(module_count):
        row = 0
        while row < module_count:
            if style_grid[row][col] != "vertical":
                row += 1
                continue

            start_row = row
            while row < module_count and style_grid[row][col] == "vertical":
                row += 1

            x, y = module_position(start_row, col, border, box_size)
            height = (row - start_row) * box_size
            shapes.append(
                svg_rect(x + delta, y, width, height, fill, radius=radius)
            )

    return shapes


def svg_horizontal_runs(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    shapes = []
    module_count = len(style_grid)
    height = box_size * SVG_BAR_RATIO
    delta = (box_size - height) / 2
    radius = height / 2

    for row in range(module_count):
        col = 0
        while col < module_count:
            if style_grid[row][col] != "horizontal":
                col += 1
                continue

            start_col = col
            while col < module_count and style_grid[row][col] == "horizontal":
                col += 1

            x, y = module_position(row, start_col, border, box_size)
            width = (col - start_col) * box_size
            shapes.append(
                svg_rect(x, y + delta, width, height, fill, radius=radius)
            )

    return shapes


def svg_unit_modules(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    shapes = []
    for row, module_row in enumerate(style_grid):
        for col, style in enumerate(module_row):
            if style not in {"circle", "gapped"}:
                continue

            x, y = module_position(row, col, border, box_size)
            shapes.append(svg_shape(style, x, y, box_size, fill))

    return shapes


def svg_shapes_from_grid(
    style_grid: list[list[str | None]],
    border: int,
    box_size: int,
    fill: str,
) -> list[str]:
    return [
        *svg_square_runs(style_grid, border, box_size, fill),
        *svg_rounded_modules(style_grid, border, box_size, fill),
        *svg_vertical_runs(style_grid, border, box_size, fill),
        *svg_horizontal_runs(style_grid, border, box_size, fill),
        *svg_unit_modules(style_grid, border, box_size, fill),
    ]


def svg_shape(style: str, x: int, y: int, box_size: int, fill: str) -> str:
    if style == "circle":
        radius = box_size / 2
        return (
            f'<circle cx="{trim_number(x + radius)}" cy="{trim_number(y + radius)}" '
            f'r="{trim_number(radius)}" fill="{fill}"/>'
        )

    if style == "gapped":
        size = box_size * SVG_GAPPED_RATIO
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
        width = box_size * SVG_BAR_RATIO
        delta = (box_size - width) / 2
        radius = width / 2
        return (
            f'<rect x="{trim_number(x + delta)}" y="{y}" '
            f'width="{trim_number(width)}" height="{box_size}" '
            f'rx="{trim_number(radius)}" ry="{trim_number(radius)}" fill="{fill}"/>'
        )

    if style == "horizontal":
        height = box_size * SVG_BAR_RATIO
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
