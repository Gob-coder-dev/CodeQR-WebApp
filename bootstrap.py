from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        runtime_root = getattr(sys, "_MEIPASS", None)
        if runtime_root:
            return Path(runtime_root)

    return Path(__file__).resolve().parent


def get_venv_python(root: Path | None = None) -> Path | None:
    base_dir = root or project_root()

    if os.name == "nt":
        candidate = base_dir / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = base_dir / ".venv" / "bin" / "python"

    return candidate if candidate.exists() else None


def ensure_project_interpreter() -> None:
    if getattr(sys, "frozen", False):
        return

    venv_python = get_venv_python()
    if not venv_python:
        return

    current_python = Path(sys.executable).resolve()
    if current_python == venv_python.resolve():
        return

    original_args = getattr(sys, "orig_argv", None)
    interpreter_args = original_args[1:] if original_args else sys.argv
    raise SystemExit(subprocess.call([str(venv_python), *interpreter_args]))
