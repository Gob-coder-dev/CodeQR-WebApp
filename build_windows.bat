@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment was not found.
  echo Create it first, then install requirements-dev.txt.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --name "QR Code Converter" ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  launcher.py

echo.
echo Build complete.
echo Share the folder inside dist\QR Code Converter with end users.
pause
