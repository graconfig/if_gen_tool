"""
Service Orchestrator for the application.
Handles the coordination of services and business logic.
"""

import concurrent.futures
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from tqdm import tqdm

from core.config import settings
from utils.i18n import _
from utils.sap_logger import logger
from excel.excel_processor import ExcelProcessor
from utils.ai_connectivity import auto_select_ai_service
from utils.tools import format_execution_time


class ServiceOrchestrator:
    """Orchestrates the services and business logic for the application."""

    def __init__(self):
        # The orchestrator now directly uses the global settings object
        self.settings = settings

    def process_single_file(
        self,
        file_path: Path,
        data_dir: Path,
        provider_override: Optional[str] = None,
        target_language: str = "en",
    ) -> bool:
        """Process a single Excel file.

        Args:
            file_path: Path to the Excel file to process
            data_dir: Path to the data directory
            provider_override: Optional AI provider to use
            target_language: Language to use for processing

        Returns:
            True if processing was successful, False otherwise
        """
        if not file_path.exists():
            logger.error(_("File not found: {}").format(file_path))
            return False

        try:
            # Use Excel file logging context manager for the entire process
            with logger.if_gen_logging(file_path.name) as log_path:
                logger.info(
                    _("Language: {}").format(target_language),
                    logger.get_excel_log_filename(file_path.name),
                )

                # Auto-select AI service
                logger.info("=" * 80, logger.get_excel_log_filename(file_path.name))
                logger.info(
                    _("[Step 1]: Detecting available AI services..."),
                    logger.get_excel_log_filename(file_path.name),
                )

                # Use the specified provider
                ai_service, service_name = auto_select_ai_service(
                    provider_override,
                    target_language,
                    logger.get_excel_log_filename(file_path.name),
                )

                logger.info( "-" *80,
                    logger.get_excel_log_filename(file_path.name),
                )

                logger.info(
                    _("[Step 2]: Excel Processing..."),
                    logger.get_excel_log_filename(file_path.name),
                )

                # Initialize Excel processor with AI service
                excel_processor = ExcelProcessor(data_dir, ai_service, self.settings)

                logger.info(
                    _("Processing specific file: {}").format(file_path.name),
                    logger.get_excel_log_filename(file_path.name),
                )
                logger.info(
                    _("Log file created: {}").format(log_path),
                    logger.get_excel_log_filename(file_path.name),
                )

                try:
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

                    # Calculate processing time
                    file_seconds = (file_end_time - file_start_time).total_seconds()
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

                    # Save per-file token usage
                    from utils.token_statistics import save_file_token_usage

                    additional_info = {
                        "ai_provider": service_name,
                        "processed_files": file_path.name,
                        "total_files": 1,
                    }
                    token_file = save_file_token_usage(file_path.name, additional_info)

                    return True

                except Exception as e:
                    logger.error(
                        f"❌ Failed to process {file_path.name}: {str(e)}",
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
                    return False

        except Exception as e:
            # Create error log with proper context
            error_log_name = f"app_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with logger.if_gen_logging(error_log_name) as error_log_path:
                logger.error(
                    _("❌ Application error: {}").format(str(e)),
                    logger.get_excel_log_filename(error_log_name),
                )
            return False

    def process_all_files(
        self,
        data_dir: Path,
        provider_override: Optional[str] = None,
        target_language: str = "en",
    ) -> bool:
        """Process all Excel files in the input directory in parallel.

        Args:
            data_dir: Path to the data directory
            provider_override: Optional AI provider to use
            target_language: Language to use for processing

        Returns:
            True if at least one file was processed successfully, False otherwise
        """
        from core.consts import Directories, FileExtensions

        input_dir = data_dir / Directories.EXCEL_INPUT
        excel_files = sorted(
            [
                p
                for ext in [FileExtensions.XLSX, ".xls"]
                for p in input_dir.glob(f"*{ext}")
            ]
        )

        if not excel_files:
            app_log_name = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with logger.if_gen_logging(app_log_name) as app_log_path:
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
            return False

        success_count = 0
        total_files = len(excel_files)
        max_workers = self.settings.excel.max_concurrent_batches

        with tqdm(
            total=total_files, desc=_("Processing Excel files"), unit="file", ncols=100
        ) as pbar:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                future_to_file = {
                    executor.submit(
                        self.process_single_file,
                        file_path,
                        data_dir,
                        provider_override,
                        target_language,
                    ): file_path
                    for file_path in excel_files
                }

                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        if future.result():
                            success_count += 1
                    except Exception as exc:
                        logger.error(
                            _("Error processing file {}: {}").format(
                                file_path.name, exc
                            )
                        )
                    finally:
                        pbar.update(1)
                        pbar.set_postfix_str(
                            _("Success: {}/{}").format(success_count, total_files)
                        )

        logger.info(
            _("Processed {}/{} files successfully").format(success_count, total_files)
        )
        return success_count > 0
