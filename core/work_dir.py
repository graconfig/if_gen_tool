"""Work directory: where excel_input/, excel_output/, excel_archive/ live."""

import json
from pathlib import Path
from tkinter import filedialog, messagebox

from core.consts import Directories
from core.paths import get_base_path

_CONFIG_FILE = "config.json"
_WORK_DIR_KEY = "work_dir"


def _config_path() -> Path:
    return get_base_path() / _CONFIG_FILE


def get_work_dir() -> Path | None:
    """Return configured work directory, or None if not set."""
    cfg = _config_path()
    if not cfg.exists():
        return None
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        val = data.get(_WORK_DIR_KEY)
        return Path(val) if val else None
    except Exception:
        return None


def set_work_dir(path: Path) -> None:
    """Persist work directory and create required subdirectories."""
    cfg = _config_path()
    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            pass
    data[_WORK_DIR_KEY] = str(path)
    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    for sub in [Directories.EXCEL_INPUT, Directories.EXCEL_OUTPUT,
                Directories.EXCEL_ARCHIVE, "logs", "upload"]:
        (path / sub).mkdir(parents=True, exist_ok=True)


def prompt_work_dir() -> Path:
    """Show folder-picker until the user picks a writable directory. Returns chosen path."""
    while True:
        chosen = filedialog.askdirectory(title="Select work directory for IF Gen Tool")
        if not chosen:
            messagebox.showerror(
                "Work Directory Required",
                "A work directory is required to run the application.\n"
                "Please select a folder where input/output files will be stored."
            )
            continue
        path = Path(chosen)
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except OSError:
            messagebox.showerror(
                "Cannot Write",
                f"Cannot write to:\n{path}\n\nPlease select a different folder."
            )
            continue
        set_work_dir(path)
        return path
