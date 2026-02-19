"""Brand assets helpers."""

from __future__ import annotations

import base64
from pathlib import Path


_ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
_LOGO_NAME = "alea_lumen_logo.png"
_LOGO_PATH = _ASSETS_DIR / _LOGO_NAME


def get_logo_path() -> Path | None:
    """Return the logo path if it exists."""
    if _LOGO_PATH.exists():
        return _LOGO_PATH
    return None


def get_logo_data_uri() -> str:
    """Return a data URI for the logo (PNG) or empty string if missing."""
    path = get_logo_path()
    if not path:
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
