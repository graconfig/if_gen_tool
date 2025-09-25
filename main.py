"""
SAP IF Design Generation Tool.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.config import ConfigurationManager
from utils.i18n import initialize_i18n, _
from utils.sap_logger import if_gen_logging, logger
from excel.excel_processor import ExcelProcessor
from utils.ai_connectivity import auto_select_ai_service
from utils.token_statistics import (
    initialize_token_tracker,
    set_current_provider,
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
        raise FileNotFoundError(_("Data directory not found: {}").format(data_dir))

    return data_dir


def get_excel_files(data_dir: Path) -> list:
    """Get all Excel files from input directory."""
    from core.consts import Directories, FileExtensions

    input_dir = data_dir / Directories.EXCEL_INPUT

    if not input_dir.exists():
        return []

    excel_files = []
    for ext in [FileExtensions.XLSX, ".xls"]:
        excel_files.extend(input_dir.glob(f"*{ext}"))

    return excel_files


def format_execution_time(seconds):
    """将秒数转换为小时、分钟、秒的格式"""
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    return _("{}h {}m {:.2f}s").format(hours, minutes, seconds)


def process_single_excel_file(
    file_path, data_dir, config_manager, target_language, provider, project_start_time
):
    """
    Process a single Excel file with its own configuration and logging.
    This function is thread-safe and handles all processing for one file.
    """
    service_name = "unknown"

    try:
        # Use Excel file logging for the entire process
        with if_gen_logging(file_path.name) as log_path:
            logger.info(
                _("Language: {}").format(target_language),
                logger.get_excel_log_filename(file_path.name),
            )

            # Get configuration from environment variables
            excel_config = config_manager.get_excel_config()

            # Auto-select AI service
            logger.info("=" * 80, logger.get_excel_log_filename(file_path.name))

            logger.info(
                _("[Step 1]: Detecting available AI services..."),
                logger.get_excel_log_filename(file_path.name),
            )

            # Use the specified provider
            ai_service, service_name = auto_select_ai_service(
                config_manager,
                provider,
                target_language,
                logger.get_excel_log_filename(file_path.name),
            )

            # Set current provider for token tracking
            set_current_provider(service_name)

            logger.info(
                _("[Step 2]: Excel Processing..."),
                logger.get_excel_log_filename(file_path.name),
            )

            # Initialize Excel processor with AI service (using environment config)
            excel_processor = ExcelProcessor(data_dir, ai_service, config_manager)

            logger.info(
                _("Processing file: {}").format(file_path.name),
                logger.get_excel_log_filename(file_path.name),
            )

            # Set current file for token tracking
            from utils.token_statistics import set_current_file

            set_current_file(file_path.name)

            file_start_time = datetime.now()
            logger.info(
                _("Processing file: {} start time: {}").format(
                    file_path.name,
                    file_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
                logger.get_excel_log_filename(file_path.name),
            )

            excel_processor.process_file(file_path)

            file_end_time = datetime.now()
            logger.info(
                _("Completed: {} ✅").format(file_path.name),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info("-" * 80, logger.get_excel_log_filename(file_path.name))

            # 计算当前文件的单独处理时间
            file_seconds = (file_end_time - file_start_time).total_seconds()
            # 计算从项目开始到当前文件完成的累计时间
            project_elapsed_seconds = (
                file_end_time - project_start_time
            ).total_seconds()

            # 输出时间信息
            logger.info(
                _("Processing {} completed at: {}").format(
                    file_path.name,
                    file_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                _("File processing time: {}").format(
                    format_execution_time(file_seconds)
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                _("Total project time: {}").format(
                    format_execution_time(project_elapsed_seconds)
                ),
                logger.get_excel_log_filename(file_path.name),
            )

            # Project end time in same log file
            project_end_time = datetime.now()
            total_project_seconds = (
                project_end_time - project_start_time
            ).total_seconds()
            logger.info(
                _("[File End Time]: {} =====").format(
                    project_end_time.strftime("%Y-%m-%d %H:%M:%S")
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                _("Total Time: {}").format(
                    format_execution_time(total_project_seconds)
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                _("File processing completed successfully"),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                "=" * 80,
                logger.get_excel_log_filename(file_path.name),
            )

            # Save per-file token usage
            from utils.token_statistics import save_file_token_usage

            additional_info = {
                "ai_provider": service_name,
                "processed_files": file_path.name,
                "total_files": 1,
                "batch_size": excel_config["batch_size"],
                "max_threads": excel_config["max_concurrent_batches"],
            }
            token_file = save_file_token_usage(file_path.name, additional_info)

            return True, None

    except Exception as e:
        # Handle errors with proper logging
        try:
            logger.error(
                f"❌ Failed to process {file_path.name}: {e}",
                logger.get_excel_log_filename(file_path.name),
            )
            # Project end time even for errors
            project_end_time = datetime.now()
            total_project_seconds = (
                project_end_time - project_start_time
            ).total_seconds()
            logger.info(
                _("[File End Time]: {} =====").format(
                    project_end_time.strftime("%Y-%m-%d %H:%M:%S")
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                _("Total Time: {}").format(
                    format_execution_time(total_project_seconds)
                ),
                logger.get_excel_log_filename(file_path.name),
            )
            logger.info(
                "=" * 50,
                logger.get_excel_log_filename(file_path.name),
            )

            # Save per-file token usage even for errors
            from utils.token_statistics import save_file_token_usage

            additional_info = {
                "ai_provider": service_name,
                "processed_files": file_path.name,
                "total_files": 1,
                "error": str(e),
                "status": "failed",
            }
            token_file = save_file_token_usage(file_path.name, additional_info)
        except Exception:
            # If even error logging fails, just print to console
            print(f"❌ Critical error processing {file_path.name}: {e}")

        return False, str(e)


def main():
    """Main application entry point."""
    project_start_time = datetime.now()

    # Initialize service_name to prevent "possibly unbound" error
    service_name = "unknown"

    parser = argparse.ArgumentParser(description=_("SAP IF Design Generation Tool"))
    parser.add_argument(
        "--file",
        type=str,
        help=_("Process specific Excel file (relative to input directory)"),
    )

    parser.add_argument(
        "--langu",
        type=str,
        choices=["en", "zh", "ja"],
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
    config_manager = ConfigurationManager()
    language_config = config_manager.get_language_config()

    # Determine language to use
    target_language = args.langu or language_config.get("language", "en")
    initialize_i18n(target_language)

    try:
        # Setup directories
        data_dir = setup_directories()

        # Initialize token tracker
        base_dir = get_base_path()
        token_tracker = initialize_token_tracker(base_dir)

        if args.file:
            # Process specific file
            from core.consts import Directories

            file_path = data_dir / Directories.EXCEL_INPUT / args.file
            if file_path.exists():
                # Process single file using the same function as multi-file processing
                success, error_msg = process_single_excel_file(
                    file_path,
                    data_dir,
                    config_manager,
                    target_language,
                    args.provider,
                    project_start_time,
                )

                if not success:
                    logger.error(f"Failed to process file: {error_msg}")
                    sys.exit(1)
            else:
                # File not found - use general application log
                app_log_name = f"app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with if_gen_logging(app_log_name) as app_log_path:
                    logger.error(
                        _("File not found: {}").format(args.file),
                        logger.get_excel_log_filename(app_log_name),
                    )
                    sys.exit(1)
        else:
            # Auto-process all Excel files in input directory with multi-threading
            excel_files = get_excel_files(data_dir)

            if not excel_files:
                # No files found - use general application log
                app_log_name = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with if_gen_logging(app_log_name) as app_log_path:
                    logger.info(
                        _("Language: {}").format(target_language),
                        logger.get_excel_log_filename(app_log_name),
                    )
                    logger.error(
                        _("❌ No Excel files found in data/excel_input/ directory"),
                        logger.get_excel_log_filename(app_log_name),
                    )
                    logger.error(
                        _(
                            "❌ Please add Excel files to process or use --file to specify a file"
                        ),
                        logger.get_excel_log_filename(app_log_name),
                    )
                    logger.info(
                        _("Application ended - No files to process"),
                        logger.get_excel_log_filename(app_log_name),
                    )
                return

            # Get processing configuration from environment variables
            file_config = config_manager.get_file_config()
            max_concurrent_files = file_config["max_concurrent_files"]

            logger.info(_("Found {} Excel files to process").format(len(excel_files)))

            # Process files in parallel using ThreadPoolExecutor
            successful_files = []
            failed_files = []

            with ThreadPoolExecutor(
                max_workers=max_concurrent_files, thread_name_prefix="FileProcessor"
            ) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(
                        process_single_excel_file,
                        file_path,
                        data_dir,
                        config_manager,
                        target_language,
                        args.provider,
                        project_start_time,
                    ): file_path
                    for file_path in excel_files
                }

                # Process results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        success, error_msg = future.result()
                        if success:
                            successful_files.append(file_path.name)
                            logger.info(_("✅ Successfully processed: {}").format(file_path.name))
                        else:
                            failed_files.append((file_path.name, error_msg))
                            logger.error(_( "❌ Failed to process: {} - {}").format(file_path.name,error_msg))
                    except Exception as e:
                        failed_files.append((file_path.name, str(e)))
                        logger.error(_("❌ Exception processing: {} - {}").format(file_path.name,e))

    except Exception as e:
        # Create error log with proper context
        error_log_name = f"app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with if_gen_logging(error_log_name) as error_log_path:
            logger.error(
                _("❌ Application error: {}").format(e),
                logger.get_excel_log_filename(error_log_name),
            )
            logger.error(
                _("Application error occurred: {}").format(str(e)),
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
                "ai_provider": service_name,
                "error": str(e),
                "status": "failed",
            }
            save_and_print_usage(additional_info)
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
