# EXE Packaging Design

**Date:** 2026-06-22  
**Tool:** PyInstaller single-file exe  
**Target:** Windows 10/11 64-bit

---

## Deliverable Structure

```
if_gen_tool.zip
├── if_gen_tool.exe        ← PyInstaller --onefile
└── .env                   ← pre-filled with non-sensitive defaults, sensitive fields empty
```

Runtime-created (not shipped):
```
<exe directory>/
├── config.json            ← work directory path
└── <work directory>/
    ├── excel_input/
    ├── excel_output/
    ├── excel_archive/
    └── logs/
```

---

## Architecture

### 1. Path Resolution (reuse `get_base_path()` in `main.py`)

`main.py` already has `get_base_path()` that handles the frozen/dev distinction. Move it to `core/paths.py` so it can be imported by GUI modules without importing `main.py`. All `.env` loading and `config.json` read/write use `get_base_path()`.

### 2. Work Directory Config (`core/work_dir.py` — new file)

Manages `config.json` at `get_base_path() / "config.json"`:
- `get_work_dir() -> Path | None` — reads `work_dir` key
- `set_work_dir(path: Path)` — writes `work_dir` key, creates subdirectories

`setup_directories()` in `main.py` gains an optional `base_dir` parameter; when provided it uses that instead of `get_base_path() / "data"`.

### 3. Startup Flow (`gui_main.py` — modified)

```
load_dotenv(get_base_path() / ".env")
  → if .env missing: create empty one
get_work_dir()
  → if None: show folder-picker dialog (blocking)
  → validate write permission; re-prompt on failure
  → create excel_input/, excel_output/, excel_archive/, logs/
launch App()
```

### 4. Config Frame (`gui/frames/config_frame.py` — modified)

Add "Work Directory" card at the top with:
- Text entry showing current path (read-only)
- "Browse" button → `filedialog.askdirectory()`
- Saved to `config.json` via `set_work_dir()`

Existing `.env` fields and save logic unchanged.

### 5. Excel / HANA path references

`process_frame.py` uses `self._base_dir / "data"` via its own `_get_base_dir()`; `main.py` CLI uses `setup_directories()`. Both must be updated to read from `get_work_dir()` instead of hardcoding `base_dir / "data"`. `_get_base_dir()` in `process_frame.py` will be replaced with a call to `get_work_dir()`.

### 6. PyInstaller Spec (`if_gen_tool.spec` — new file)

Key directives:
- `collect_data_files('customtkinter')` — theme assets
- `datas=[('locale', 'locale')]` — i18n `.mo` files
- `hiddenimports` for: `hana_ml`, `sap_ai_sdk_gen`, `google.cloud.aiplatform`, `google.genai`, `aioboto3`, `protobuf`
- `--onefile --windowed --name if_gen_tool`

### 7. Build Script (`build.bat` — new file)

```bat
@echo off
call venv\Scripts\activate
pip install pyinstaller
pyinstaller if_gen_tool.spec
echo Done: dist\if_gen_tool.exe
pause
```

---

## Error Handling

| Scenario | Handling |
|----------|---------|
| `.env` missing on startup | Auto-create empty `.env`; user fills via Config |
| Work dir not configured | Blocking folder-picker dialog before main window |
| Work dir not writable | Error dialog, re-prompt |
| locale `.mo` missing | Fall back to English, no crash |
| Antivirus block | Document: add exe to whitelist |

---

## Out of Scope

- Code signing (no certificate available)
- Auto-update mechanism
- Installer wizard (NSIS/Inno Setup)
