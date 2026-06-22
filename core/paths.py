"""App-root path resolution for both dev and PyInstaller frozen exe."""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """Return the directory containing the exe (frozen) or project root (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent
