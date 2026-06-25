"""GUI entry point for SAP IF Design Generation Tool."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# In windowed (no-console) mode sys.stdout/stderr are None; redirect to devnull
# to prevent 'NoneType has no attribute write' from any print/buffer.write calls
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

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

    # Re-point logger to work directory's logs/ folder
    from utils.sap_logger import logger
    work_dir = get_work_dir()
    log_dir = str(work_dir / "logs")
    logger.log_dir = log_dir
    import os; os.makedirs(log_dir, exist_ok=True)

    app = App(config_manager, language)
    app.mainloop()


if __name__ == "__main__":
    main()
