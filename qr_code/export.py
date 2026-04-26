from __future__ import annotations

import io
from html import escape
from typing import BinaryIO

import qrcode
from qrcode.image.styledpil import StyledPilImage

from qr_code.options import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_BORDER_SIZE,
    DEFAULT_COLOR_MODE,
    DEFAULT_ERROR_CORRECTION,
    DEFAULT_EYE_STYLE,
    DEFAULT_FOREGROUND_COLOR,
    DEFAULT_FOREGROUND_COLOR_2,
    DEFAULT_LOGO_SIZE_RATIO,
    DEFAULT_MODULE_STYLE,
    DEFAULT_QUALITY,
    QRCodeRequestError,
    color_to_hex,
    contrast_ratio,
    normalize_hex_color,
    parse_bool,
    resolve_border_size,
    resolve_box_size,
    resolve_color_mode,
    resolve_error_correction,
    resolve_eye_style,
    resolve_logo_size_ratio,
    resolve_module_style,
)
from qr_code.rendering import (
    EYE_DRAWERS,
    MODULE_DRAWERS,
    build_color_mask,
    build_eye_drawer,
    build_module_drawer,
    clear_intersecting_modules,
    is_eye_module,
    load_logo_image,
    logo_to_data_uri,
    paste_logo,
    prepare_logo,
    svg_gradient_defs,
    svg_shape,
)


def generate_qr_svg(
    text: str,
    *,
    foreground_color: str = DEFAULT_FOREGROUND_COLOR,
    foreground_color_2: str = DEFAULT_FOREGROUND_COLOR_2,
    background_color: str = DEFAULT_BACKGROUND_COLOR,
    module_style: str = DEFAULT_MODULE_STYLE,
    eye_style: str = DEFAULT_EYE_STYLE,
    quality: str = DEFAULT_QUALITY,
    error_correction: str = DEFAULT_ERROR_CORRECTION,
    border_size: str = DEFAULT_BORDER_SIZE,
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

    module_style = resolve_module_style(module_style, MODULE_DRAWERS)
    eye_style = resolve_eye_style(eye_style, EYE_DRAWERS)
    color_mode = resolve_color_mode(color_mode)
    box_size = resolve_box_size(quality)
    logo_size_ratio = resolve_logo_size_ratio(logo_size)
    logo = load_logo_image(logo_file)
    correction_level = resolve_error_correction(error_correction, has_logo=logo is not None)
    border = resolve_border_size(border_size)
    prepared_logo = None

    qr_code = qrcode.QRCode(
        version=None,
        error_correction=correction_level,
        box_size=box_size,
        border=border,
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
    error_correction: str = DEFAULT_ERROR_CORRECTION,
    border_size: str = DEFAULT_BORDER_SIZE,
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

    module_style = resolve_module_style(module_style, MODULE_DRAWERS)
    color_mode = resolve_color_mode(color_mode)
    box_size = resolve_box_size(quality)
    logo_size_ratio = resolve_logo_size_ratio(logo_size)
    logo = load_logo_image(logo_file)
    correction_level = resolve_error_correction(error_correction, has_logo=logo is not None)
    border = resolve_border_size(border_size)
    prepared_logo = None
    qr_code = qrcode.QRCode(
        version=None,
        error_correction=correction_level,
        box_size=box_size,
        border=border,
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
