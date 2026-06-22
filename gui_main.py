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
