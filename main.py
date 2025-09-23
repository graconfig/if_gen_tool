"""
SAP IF Design Generation Tool.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from core.config import settings
from core.service_orchestrator import ServiceOrchestrator
from utils.exceptions import IFGenBaseException
from utils.i18n import initialize_i18n, _
from utils.sap_logger import logger
from utils.token_statistics import (
    initialize_token_tracker,
    save_and_print_usage,
)


def get_base_path() -> Path:
    """
    Get the base path for the application, accommodating both script and frozen exe.
    """
    if getattr(sys, "frozen", False):
        # If the application is run as a bundle (e.g., by PyInstaller)
        return Path(sys.executable).parent
    else:
        # If the application is run as a script
        return Path(__file__).parent


def setup_directories() -> Path:
    """Setup and validate application directories."""
    from core.consts import Directories

    base_dir = get_base_path()
    data_dir = base_dir / "data"

    # Create required directories if they don't exist
    required_dirs = [
        data_dir / Directories.EXCEL_INPUT,
        data_dir / Directories.EXCEL_OUTPUT,
        data_dir / Directories.EXCEL_ARCHIVE,
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Validate data directory exists
    if not data_dir.exists():
        error_msg = _("Data directory not found: {}").format(data_dir)
        raise FileNotFoundError(error_msg)

    return data_dir


def main():
    """Main application entry point."""
    project_start_time = datetime.now()

    parser = argparse.ArgumentParser(description=_("SAP IF Design Generation Tool"))
    parser.add_argument(
        "--file",
        type=str,
        help=_("Process specific Excel file (relative to input directory)"),
    )

    parser.add_argument(
        "--langu",
        type=str,
        choices=settings.language_config.supported_languages,
        help=_("Set interface language (en, zh, ja)"),
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["claude", "gemini", "openai"],
        help=_("Choose AI provider (claude, gemini, openai) - all via AI Core"),
    )

    args = parser.parse_args()

    # Initialize internationalization first
    # Determine language to use
    target_language = args.langu or settings.language_config.language
    initialize_i18n(target_language)

    try:
        # Setup directories
        data_dir = setup_directories()

        # Initialize token tracker
        base_dir = get_base_path()
        token_tracker = initialize_token_tracker(base_dir)

        # Initialize service orchestrator
        orchestrator = ServiceOrchestrator()

        if args.file:
            # Process specific file
            from core.consts import Directories

            file_path = data_dir / Directories.EXCEL_INPUT / args.file

            success = orchestrator.process_single_file(
                file_path, data_dir, args.provider, target_language
            )

            if not success:
                sys.exit(1)
        else:
            # Auto-process all Excel files in input directory
            success = orchestrator.process_all_files(
                data_dir, args.provider, target_language
            )

            if not success:
                sys.exit(1)

    except IFGenBaseException as e:
        # Handle our custom exceptions
        error_log_name = f"app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with logger.if_gen_logging(error_log_name) as error_log_path:
            logger.error(
                _("Application error: {}").format(str(e.message)),
                logger.get_excel_log_filename(error_log_name),
            )
            if e.error_code:
                logger.error(
                    _("Error code: {}").format(e.error_code),
                    logger.get_excel_log_filename(error_log_name),
                )

        try:
            additional_info = {
                "error": e.message,
                "error_code": e.error_code if e.error_code else "UNKNOWN_ERROR",
                "status": "failed",
            }
            save_and_print_usage(additional_info)
        except Exception:
            pass

        sys.exit(1)
    except Exception as e:
        # Handle unexpected exceptions
        error_log_name = f"app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with logger.if_gen_logging(error_log_name) as error_log_path:
            logger.error(
                _("Unexpected application error: {}").format(str(e)),
                logger.get_excel_log_filename(error_log_name),
            )
            logger.error(
                _("Error timestamp: {}").format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                logger.get_excel_log_filename(error_log_name),
            )

        try:
            additional_info = {
                "error": str(e),
                "error_code": "UNEXPECTED_ERROR",
                "status": "failed",
            }
            save_and_print_usage(additional_info)
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
