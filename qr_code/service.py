from __future__ import annotations

from typing import BinaryIO

from qr_code.export import generate_qr_png, generate_qr_svg
from qr_code.options import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_BORDER_SIZE,
    DEFAULT_COLOR_MODE,
    DEFAULT_ERROR_CORRECTION,
    DEFAULT_EYE_STYLE,
    DEFAULT_FILE_STEM,
    DEFAULT_FOREGROUND_COLOR,
    DEFAULT_FOREGROUND_COLOR_2,
    DEFAULT_LOGO_SIZE_RATIO,
    DEFAULT_MODULE_STYLE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_QUALITY,
    MAX_FILE_STEM_LENGTH,
    MAX_LOGO_BYTES,
    MAX_LOGO_SIZE_RATIO,
    MIN_LOGO_SIZE_RATIO,
    QRCodeRequestError,
    build_download_name,
    color_to_hex,
    contrast_ratio,
    normalize_hex_color,
    parse_bool,
    relative_luminance,
    resolve_border_size,
    resolve_box_size,
    resolve_color_mode,
    resolve_error_correction,
    resolve_eye_style as _resolve_eye_style,
    resolve_logo_size_ratio,
    resolve_module_style as _resolve_module_style,
    resolve_output_format,
)
from qr_code.rendering import (
    EYE_DRAWERS,
    MODULE_DRAWERS,
    boxes_intersect,
    build_color_mask,
    build_eye_drawer,
    build_module_drawer,
    clear_intersecting_modules,
    crop_transparent_padding,
    is_eye_module,
    load_logo_image,
    logo_to_data_uri,
    paste_logo,
    prepare_logo,
    svg_gradient_defs,
    svg_shape,
    trim_number,
)


def resolve_module_style(module_style: str) -> str:
    return _resolve_module_style(module_style, MODULE_DRAWERS)


def resolve_eye_style(eye_style: str) -> str:
    return _resolve_eye_style(eye_style, EYE_DRAWERS)


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
    error_correction: str = DEFAULT_ERROR_CORRECTION,
    border_size: str = DEFAULT_BORDER_SIZE,
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
        error_correction=error_correction,
        border_size=border_size,
        color_mode=color_mode,
        transparent_background=transparent_background,
        logo_size=logo_size,
        logo_file=logo_file,
    )
    mimetype = "image/svg+xml" if file_format == "svg" else "image/png"
    return file_bytes, mimetype, file_format


__all__ = [
    "DEFAULT_BACKGROUND_COLOR",
    "DEFAULT_BORDER_SIZE",
    "DEFAULT_COLOR_MODE",
    "DEFAULT_ERROR_CORRECTION",
    "DEFAULT_EYE_STYLE",
    "DEFAULT_FILE_STEM",
    "DEFAULT_FOREGROUND_COLOR",
    "DEFAULT_FOREGROUND_COLOR_2",
    "DEFAULT_LOGO_SIZE_RATIO",
    "DEFAULT_MODULE_STYLE",
    "DEFAULT_OUTPUT_FORMAT",
    "DEFAULT_QUALITY",
    "MAX_FILE_STEM_LENGTH",
    "MAX_LOGO_BYTES",
    "MAX_LOGO_SIZE_RATIO",
    "MIN_LOGO_SIZE_RATIO",
    "QRCodeRequestError",
    "EYE_DRAWERS",
    "MODULE_DRAWERS",
    "boxes_intersect",
    "build_color_mask",
    "build_download_name",
    "build_eye_drawer",
    "build_module_drawer",
    "clear_intersecting_modules",
    "color_to_hex",
    "contrast_ratio",
    "crop_transparent_padding",
    "generate_qr_file",
    "generate_qr_png",
    "generate_qr_svg",
    "is_eye_module",
    "load_logo_image",
    "logo_to_data_uri",
    "normalize_hex_color",
    "parse_bool",
    "paste_logo",
    "prepare_logo",
    "relative_luminance",
    "resolve_border_size",
    "resolve_box_size",
    "resolve_color_mode",
    "resolve_error_correction",
    "resolve_eye_style",
    "resolve_logo_size_ratio",
    "resolve_module_style",
    "resolve_output_format",
    "svg_gradient_defs",
    "svg_shape",
    "trim_number",
]
