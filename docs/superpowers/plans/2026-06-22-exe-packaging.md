# EXE Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package if_gen_tool as a PyInstaller single-file Windows exe that reads `.env` from the exe directory and stores the user-selected work directory in `config.json`.

**Architecture:** Extract `get_base_path()` from `main.py` into `core/paths.py` as the single source of truth for the exe/dev root. Add `core/work_dir.py` to manage `config.json` (work directory selection). Wire a work-directory picker into startup and into the Config GUI frame. Finally, write a `if_gen_tool.spec` + `build.bat` to produce `dist/if_gen_tool.exe`.

**Tech Stack:** Python 3.11+, PyInstaller 6.x, customtkinter, tkinter.filedialog

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Create | `core/paths.py` | `get_base_path()` — single source of truth for app root |
| Create | `core/work_dir.py` | `get_work_dir()`, `set_work_dir()`, `prompt_work_dir()` |
| Modify | `main.py` | Remove `get_base_path()`, import from `core.paths`; `setup_directories()` accepts optional `base_dir` |
| Modify | `gui_main.py` | Load `.env` from `get_base_path()`; call `prompt_work_dir()` before App |
| Modify | `gui/frames/process_frame.py` | Replace `_get_base_dir()` + `_data_dir` with `get_work_dir()` |
| Modify | `gui/frames/config_frame.py` | Add Work Directory card at top |
| Create | `if_gen_tool.spec` | PyInstaller spec (onefile, windowed, data files, hidden imports) |
| Create | `build.bat` | One-click build script |

---

## Task 1: Extract `get_base_path()` into `core/paths.py`

**Files:**
- Create: `core/paths.py`
- Modify: `main.py` lines 24–34

- [ ] **Step 1: Create `core/paths.py`**

```python
"""App-root path resolution for both dev and PyInstaller frozen exe."""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """Return the directory containing the exe (frozen) or project root (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent
```

- [ ] **Step 2: Update `main.py` to import from `core.paths`**

Remove the existing `get_base_path()` definition (lines 24–34) and add an import at the top of the imports section:

```python
from core.paths import get_base_path
```

- [ ] **Step 3: Verify the app still launches**

```bash
venv\Scripts\python.exe gui_main.py
```

Expected: GUI opens without error.

- [ ] **Step 4: Commit**

```bash
git add core/paths.py main.py
git commit -m "refactor: extract get_base_path into core/paths"
```

---

## Task 2: Add `core/work_dir.py` — work directory management

**Files:**
- Create: `core/work_dir.py`

- [ ] **Step 1: Create `core/work_dir.py`**

```python
"""Work directory: where excel_input/, excel_output/, excel_archive/ live."""

import json
import os
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
            # User cancelled — show error and loop
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
```

- [ ] **Step 2: Verify import works**

```bash
venv\Scripts\python.exe -c "from core.work_dir import get_work_dir; print(get_work_dir())"
```

Expected: prints `None` (config.json doesn't exist yet).

- [ ] **Step 3: Commit**

```bash
git add core/work_dir.py
git commit -m "feat: add core/work_dir for config.json-based work directory management"
```

---

## Task 3: Wire work directory into `gui_main.py` startup

**Files:**
- Modify: `gui_main.py`

- [ ] **Step 1: Replace `gui_main.py` with the updated version**

```python
"""GUI entry point for SAP IF Design Generation Tool."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.paths import get_base_path
from dotenv import load_dotenv

# Load .env from exe/project root; create empty one if missing
_env_path = get_base_path() / ".env"
if not _env_path.exists():
    _env_path.touch()
load_dotenv(_env_path)

from core.config import ConfigurationManager
from core.work_dir import get_work_dir, prompt_work_dir
from utils.i18n import initialize_i18n
from gui.app import App


def main():
    config_manager = ConfigurationManager()
    language_config = config_manager.get_language_config()
    language = language_config.get("language", "ja")
    initialize_i18n(language)

    # Ensure work directory is configured
    if get_work_dir() is None:
        prompt_work_dir()

    app = App(config_manager, language)
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test first-run experience**

Delete `config.json` if it exists, then run:

```bash
venv\Scripts\python.exe gui_main.py
```

Expected: folder picker appears first, then main window opens.

- [ ] **Step 3: Test normal launch (config.json present)**

Run again without deleting `config.json`.

Expected: folder picker does NOT appear, main window opens directly.

- [ ] **Step 4: Commit**

```bash
git add gui_main.py
git commit -m "feat: load .env from app root; prompt work dir on first launch"
```

---

## Task 4: Update `process_frame.py` to use `get_work_dir()`

**Files:**
- Modify: `gui/frames/process_frame.py`

- [ ] **Step 1: Add import and replace `_get_base_dir` / `_data_dir` initialization**

At the top of the file, add:

```python
from core.work_dir import get_work_dir
```

Replace the `__init__` lines:

```python
        self._base_dir = self._get_base_dir()
        self._data_dir = self._base_dir / "data"
        self._input_dir = self._data_dir / Directories.EXCEL_INPUT
```

with:

```python
        self._input_dir = get_work_dir() / Directories.EXCEL_INPUT
```

- [ ] **Step 2: Remove `_get_base_dir` method**

Delete the entire `_get_base_dir` method (lines 41–46):

```python
    def _get_base_dir(self) -> Path:
        import sys
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent.parent
```

- [ ] **Step 3: Update `_run_all` to use `get_work_dir()` as `data_dir`**

In `_run_all`, replace:

```python
            base_dir = get_base_path()
            data_dir = setup_directories()
```

with:

```python
            data_dir = get_work_dir()
```

And remove the unused `from main import ... get_base_path` import from that block (keep `process_single_excel_file` and `setup_directories` only if still used; after this change `setup_directories` is no longer called here — remove it too).

The updated import block in `_run_all`:

```python
        from main import process_single_excel_file
        from utils.token_statistics import initialize_token_tracker
        from hana.hana_conn import HANADBClient
```

And initialize the token tracker using `get_base_path()`:

```python
            from core.paths import get_base_path
            initialize_token_tracker(get_base_path())
```

- [ ] **Step 4: Verify processing still works**

Place an `.xlsx` file in the `excel_input/` subfolder of the configured work directory, then run:

```bash
venv\Scripts\python.exe gui_main.py
```

Expected: process frame shows the file, processing runs without path errors.

- [ ] **Step 5: Commit**

```bash
git add gui/frames/process_frame.py
git commit -m "refactor: process_frame uses get_work_dir() instead of base_dir/data"
```

---

## Task 5: Add Work Directory card to `config_frame.py`

**Files:**
- Modify: `gui/frames/config_frame.py`

- [ ] **Step 1: Add imports at top of `config_frame.py`**

```python
from tkinter import filedialog
from core.work_dir import get_work_dir, set_work_dir
```

- [ ] **Step 2: Add `_build_work_dir_card()` method to `ConfigFrame`**

Add after `_build_ui`:

```python
    def _build_work_dir_card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=_("Work Directory"),
                     font=ctk.CTkFont(weight="bold", size=13)).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 4))

        self._work_dir_var = ctk.StringVar(value=str(get_work_dir() or ""))
        entry = ctk.CTkEntry(card, textvariable=self._work_dir_var,
                             font=ctk.CTkFont(size=11), state="readonly")
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(12, 4), pady=4)

        ctk.CTkButton(card, text=_("Browse"), width=70, height=28,
                      command=self._browse_work_dir).grid(
            row=1, column=2, padx=(0, 12), pady=4)

        ctk.CTkLabel(card, text="").grid(row=2, column=0, pady=(0, 4))
        return card

    def _browse_work_dir(self):
        chosen = filedialog.askdirectory(title=_("Select Work Directory"))
        if chosen:
            path = Path(chosen)
            try:
                test = path / ".write_test"
                test.touch(); test.unlink()
            except OSError:
                messagebox.showerror(_("Error"), _("Cannot write to: {}").format(path))
                return
            set_work_dir(path)
            self._work_dir_var.set(str(path))
```

- [ ] **Step 3: Insert the work dir card at the top of `_build_ui`**

In `_build_ui`, before the `groups = [...]` line, add:

```python
        work_dir_card = self._build_work_dir_card(scroll)
        work_dir_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        row = 1
```

And change the existing `row = 0` initializer to `row = 1` (it comes right after the groups list now).

- [ ] **Step 4: Verify Config frame**

Run `venv\Scripts\python.exe gui_main.py`, navigate to Config tab.

Expected: "Work Directory" card appears at the top, shows current path, Browse button opens folder picker.

- [ ] **Step 5: Commit**

```bash
git add gui/frames/config_frame.py
git commit -m "feat: add Work Directory picker to Config frame"
```

---

## Task 6: Create `if_gen_tool.spec`

**Files:**
- Create: `if_gen_tool.spec`

- [ ] **Step 1: Install PyInstaller**

```bash
venv\Scripts\pip.exe install pyinstaller
```

Expected: `Successfully installed pyinstaller-...`

- [ ] **Step 2: Create `if_gen_tool.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

added_datas = []
added_datas += collect_data_files('customtkinter')
added_datas += [('locale', 'locale')]

hidden_imports = []
hidden_imports += collect_submodules('hana_ml')
hidden_imports += collect_submodules('sap_ai_sdk_gen')
hidden_imports += collect_submodules('google.cloud.aiplatform')
hidden_imports += collect_submodules('google.genai')
hidden_imports += collect_submodules('aioboto3')
hidden_imports += collect_submodules('aiobotocore')
hidden_imports += [
    'pkg_resources.py2_warn',
    'charset_normalizer.md__mypyc',
    'grpc',
    'google.protobuf',
]

a = Analysis(
    ['gui_main.py'],
    pathex=[],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='if_gen_tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
```

- [ ] **Step 3: Commit**

```bash
git add if_gen_tool.spec
git commit -m "build: add PyInstaller spec for single-file exe"
```

---

## Task 7: Create `build.bat` and do a test build

**Files:**
- Create: `build.bat`

- [ ] **Step 1: Create `build.bat`**

```bat
@echo off
chcp 65001 > nul
echo === IF Gen Tool - Build EXE ===
cd /d "%~dp0"

call venv\Scripts\activate.bat

echo [1/3] Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [2/3] Running PyInstaller...
pyinstaller if_gen_tool.spec

if %ERRORLEVEL% neq 0 (
    echo BUILD FAILED.
    pause
    exit /b 1
)

echo [3/3] Done!
echo Output: dist\if_gen_tool.exe
dir dist\if_gen_tool.exe
pause
```

- [ ] **Step 2: Run the build**

Double-click `build.bat` or run:

```bash
cmd /c build.bat
```

Expected: `dist\if_gen_tool.exe` created, no errors.

- [ ] **Step 3: Test the exe**

```bash
dist\if_gen_tool.exe
```

Expected: folder picker appears (if first run), then main window.
Watch for any import errors in a visible console — if needed, temporarily set `console=True` in the spec to see errors.

- [ ] **Step 4: Fix any hidden import errors**

If the exe crashes with a ModuleNotFoundError, add the missing module to `hiddenimports` in `if_gen_tool.spec` and rebuild.

Common additions needed:
```python
hidden_imports += ['_cffi_backend', 'cffi', 'cryptography']
```

- [ ] **Step 5: Commit**

```bash
git add build.bat
git commit -m "build: add build.bat one-click build script"
```

---

## Task 8: Create delivery zip

**Files:**
- Create: `.env.example` (template for clients)

- [ ] **Step 1: Create `.env.example`**

```bash
# SAP AI Core
AICORE_AUTH_URL=https://
AICORE_CLIENT_ID=
AICORE_CLIENT_SECRET=
AICORE_BASE_URL=https://
AICORE_RESOURCE_GROUP=default

# HANA Cloud
HANA_ADDRESS=
HANA_PORT=443
HANA_USER=
HANA_PASSWORD=
HANA_SCHEMA=
HANA_SCHEMA_CUST=

# Processing
AI_PROVIDER=claude
LANGUAGE=ja
LLM_BATCH_SIZE=30
LLM_MAX_WORKERS=5
FILE_MAX_WORKERS=5
CUSTOM_FIELD_THRESHOLD=0.75
MATCH_THRESHOLD=0
UPLOAD_MODE=overwrite
Match_Number=3

# AI Models
CLAUDE_LLM_MODEL=anthropic--claude-4.6-sonnet
GEMINI_LLM_MODEL=gemini-2.5-pro
OPENAI_LLM_MODEL=gpt-4o
TEXT_EMBEDDING_MODEL=text-embedding-ada-002

# OData Verify (optional)
VERIFY_FLAG=false
ODATA_URL=
ODATA_USER=
ODATA_PASSWORD=
```

- [ ] **Step 2: Commit `.env.example`**

```bash
git add .env.example
git commit -m "docs: add .env.example for client delivery"
```

- [ ] **Step 3: Create delivery zip manually**

After a successful build, create the delivery zip:
```
if_gen_tool_<version>.zip
├── if_gen_tool.exe       (from dist/)
└── .env                  (copy of .env.example, renamed)
```

The client: double-clicks exe → Config tab → fills in credentials → selects work directory → done.

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Single-file exe (Task 6–7)
- ✅ `.env` from exe dir (Task 3)
- ✅ Work dir in `config.json` (Task 2)
- ✅ Prompt on first run (Task 3)
- ✅ Browse button in Config (Task 5)
- ✅ `process_frame` uses work dir (Task 4)
- ✅ `get_base_path()` unified (Task 1)
- ✅ Delivery zip structure (Task 8)

**Type/naming consistency:**
- `get_work_dir()` returns `Path | None` — used in Task 3 with None-check, Task 4 assumes non-None (safe: startup ensures it's set before App launches)
- `set_work_dir(path: Path)` — consistent across Task 2 and Task 5
- `get_base_path()` — consistent across all tasks
