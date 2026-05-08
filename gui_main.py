"""
GUI entry point for SAP IF Design Generation Tool.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from core.config import ConfigurationManager
from utils.i18n import initialize_i18n
from gui.app import App


def main():
    config_manager = ConfigurationManager()
    language_config = config_manager.get_language_config()
    language = language_config.get("language", "ja")
    initialize_i18n(language)

    app = App(config_manager, language)
    app.mainloop()


if __name__ == "__main__":
    main()
