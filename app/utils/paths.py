"""Resolve asset paths for both dev and PyInstaller packaged runs."""

import sys
from pathlib import Path


def assets_dir() -> Path:
    """Return the directory containing bundled assets."""
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        return Path(sys._MEIPASS) / "assets"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent.parent / "assets"


def asset(name: str) -> Path:
    """Return the full path to a named asset file."""
    return assets_dir() / name
