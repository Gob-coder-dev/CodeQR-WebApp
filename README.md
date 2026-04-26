# QR Code Converter

A small Flask web app that generates customizable QR codes from links, text, Wi-Fi credentials, email, phone, SMS, contact cards, or locations.

The app does not store user data. It renders a web page, accepts form input, generates the QR code on the server, and returns an image preview that can be downloaded or copied from the browser.

## Features

- supports QR codes for text/URL, Wi-Fi, email, phone, SMS, vCard contact, and location
- generates PNG or SVG files with Python
- shows a preview before download
- can copy the generated QR code image to the clipboard
- supports solid colors and gradients
- supports custom foreground, secondary, background, and caption colors
- supports transparent backgrounds
- customizes module shapes and QR eye styles
- supports central logos with cleaned QR modules underneath
- supports logo size, resolution quality, error correction, and margin size
- can add a caption below the QR code
- displays readability warnings for risky settings
- sanitizes the output file name automatically
- ready for local development, Docker, and Render

## Tech Stack

- Python 3
- Flask for the web app
- `qrcode` + Pillow to generate PNG and SVG QR codes
- Waitress for production serving
- Docker for deployment packaging

## Project Structure

```text
.
|-- app.py
|-- bootstrap.py
|-- Dockerfile
|-- render.yaml
|-- serve.py
|-- qr_payload.py
|-- qr_service.py
|-- qr_code/
|   |-- __init__.py
|   |-- export.py
|   |-- options.py
|   |-- payload.py
|   |-- rendering.py
|   `-- service.py
|-- requirements.txt
|-- requirements-dev.txt
|-- templates/
|   `-- index.html
|-- static/
|   |-- css/
|   |   |-- base.css
|   |   |-- delight.css
|   |   |-- forms.css
|   |   |-- language-switcher.css
|   |   |-- layout.css
|   |   |-- preview.css
|   |   `-- style.css
|   `-- js/
|       |-- app.js
|       |-- color-utils.js
|       |-- delight.js
|       |-- form-options.js
|       |-- i18n.js
|       |-- language.js
|       |-- preview.js
|       `-- qr-api.js
`-- tests/
    |-- test_app.py
    |-- test_qr_payload.py
    `-- test_qr_service.py
```

## Local Installation

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Local Run

For a production-like local run:

```powershell
python serve.py
```

For the Flask development server:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:10000
```

If you run `app.py`, the default local URL is:

```text
http://127.0.0.1:5000
```

If a local `.venv` exists, `app.py` and `serve.py` automatically reuse it even when they are started from another Python interpreter.

## Docker

Build the image:

```powershell
docker build -t qr-code-converter .
```

Run the container:

```powershell
docker run --rm -p 10000:10000 -e PORT=10000 qr-code-converter
```

Open:

```text
http://127.0.0.1:10000
```

## Deploy on Render

This repository now includes:

- a `Dockerfile`
- a `render.yaml`
- a `/health` endpoint for Render health checks

### Recommended setup

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service from the repository.
3. Let Render build from the included `Dockerfile`.
4. Use `/health` as the health check path.

If you use the included `render.yaml`, Render can read the service definition directly from the repo root.

## Usage

1. Choose a QR code type.
2. Fill in the fields for that type.
3. Choose an output file name.
4. Open advanced options if you want to customize the design.
5. Click `Generate preview`.
6. Download or copy the generated QR code.

Supported QR code types:

- Link or free-form text
- Wi-Fi network
- Email
- Phone call
- SMS
- Contact card
- Location

Advanced options include:

- PNG or SVG export
- resolution quality
- error correction level
- QR code margin
- foreground/background colors
- gradients
- transparent background
- module and eye shapes
- central logo
- caption below the image

The readability panel gives non-blocking warnings when settings may reduce scan reliability, such as low contrast, small margins, large logos, or transparent backgrounds with light QR colors.

## Frontend Notes

Frontend behavior is split by responsibility:

- `static/js/language.js`: language metadata and translated text resources.
- `static/js/i18n.js`: browser-language detection, language menu, and text application.
- `static/js/color-utils.js`: color normalization, picker/hex sync, and color easter-egg checks.
- `static/js/form-options.js`: form validation, conditional fields, and advanced options.
- `static/js/delight.js`: small contextual surprises. Search for `delightRules` to adjust those hidden UI messages.
- `static/js/preview.js`: preview state, downloads, and clipboard copy.
- `static/js/qr-api.js`: QR generation API call and response handling.
- `static/js/app.js`: orchestration and event binding.
- `static/css/style.css`: CSS entry point that imports `base.css`, `layout.css`, `forms.css`, `preview.css`, `delight.css`, and `language-switcher.css`.

Backend QR generation is split by responsibility:

- `qr_code/options.py`: constants, request errors, option resolution, color validation, and file-name sanitization.
- `qr_code/rendering.py`: module/eye drawing, color masks, logo preparation, and SVG shape helpers.
- `qr_code/export.py`: PNG/SVG byte generation.
- `qr_code/payload.py`: typed QR payload builders for text, Wi-Fi, email, phone, SMS, contact, and location.
- `qr_code/service.py`: public QR service API and file-format dispatch.
- `qr_service.py` and `qr_payload.py`: thin compatibility imports for older local imports and tests.

## API Endpoint

The main generation endpoint is:

```text
POST /api/qr-code
```

It accepts form data or JSON. Common fields include:

- `qr_type`
- `text`
- `filename`
- `output_format`
- `foreground_color`
- `foreground_color_2`
- `background_color`
- `color_mode`
- `module_style`
- `eye_style`
- `quality`
- `error_correction`
- `border_size`
- `transparent_background`
- `logo`
- `logo_size`
- `caption_enabled`
- `caption_text`
- `caption_size`
- `caption_color`

The endpoint returns an image attachment with either `image/png` or `image/svg+xml`.

## Where Is the File Saved?

Because this is a web app, the browser controls where the file is saved:

- either the file goes to the default download folder
- or the browser opens a `Save As` dialog, depending on its settings

## Run Tests

```powershell
pytest
```
