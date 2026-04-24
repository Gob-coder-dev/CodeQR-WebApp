# QR Code Converter

A small local web app that generates a PNG QR code from text or a link.

The app runs on your computer with Flask. The user enters a value, chooses a file name, and the browser downloads the generated image.

## Features

- accepts free-form text or a URL
- generates the QR code with Python
- downloads the PNG directly from the browser
- sanitizes the output file name automatically
- simple responsive interface that works on Windows and macOS
- one-click Windows launcher for local use

## Tech Stack

- Python 3
- Flask for the local web server
- `qrcode` + Pillow to generate the PNG image
- HTML, CSS, and JavaScript for the interface

## Project Structure

```text
.
|-- app.py
|-- launcher.py
|-- launch_qr_code_converter.bat
|-- build_windows.bat
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

## Installation

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

## Run the App

Preferred local launcher:

```powershell
python launcher.py
```

Development server:

```powershell
python app.py
```

Then open your browser at:

```text
http://127.0.0.1:5000
```

If a local `.venv` exists, `app.py` and `launcher.py` automatically reuse it even when they are started from another Python interpreter.

## One-Click Local Launch on Windows

If the project dependencies are already installed, you can start the app by double-clicking:

```text
launch_qr_code_converter.bat
```

This starts the local server and opens the browser automatically.

## Windows App for Non-Technical Users

If you want other people to launch the project without using Python, PowerShell, or a terminal, build the packaged Windows app.

Double-click:

```text
build_windows.bat
```

The packaged app will be created in:

```text
dist/QR Code Converter/
```

Share that full folder with end users. They only need to double-click:

```text
QR Code Converter.exe
```

No Python installation is required on their machine.

## Usage

1. Enter text or a link.
2. Choose an output file name.
3. Click `Generate and download`.
4. The browser starts downloading the PNG file.

## Where Is the File Saved?

Because this is a local web app, the browser controls where the file is saved:

- either the file goes to the default download folder
- or the browser opens a `Save As` dialog, depending on its settings

## Run Tests

```powershell
pytest
```

## Possible Next Steps

- add a QR code preview before download
- allow color customization
- allow image size configuration
- build a macOS `.app` version on a Mac
