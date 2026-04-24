@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment was not found.
  echo.
  echo Ask the project owner for the packaged app, or install the project dependencies first.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" launcher.py
