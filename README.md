# QR Code Converter

A small Flask web app that generates a PNG QR code from text or a link.

The app does not store user data. It renders a web page, accepts text input, generates a QR code on the server, and sends the PNG back as a browser download.

## Features

- accepts free-form text or a URL
- generates the QR code with Python
- downloads the PNG directly from the browser
- sanitizes the output file name automatically
- ready for local development, Docker, and Render

## Tech Stack

- Python 3
- Flask for the web app
- `qrcode` + Pillow to generate the PNG image
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
|-- qr_service.py
|-- requirements.txt
|-- requirements-dev.txt
|-- templates/
|   `-- index.html
|-- static/
|   |-- app.js
|   `-- style.css
`-- tests/
    |-- test_app.py
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

1. Enter text or a link.
2. Choose an output file name.
3. Click `Generate and download`.
4. The browser starts downloading the PNG file.

## Where Is the File Saved?

Because this is a web app, the browser controls where the file is saved:

- either the file goes to the default download folder
- or the browser opens a `Save As` dialog, depending on its settings

## Run Tests

```powershell
pytest
```
