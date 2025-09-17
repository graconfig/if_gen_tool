"""
SAP-style file logger for IF Design Generation Tool.
Based on the SAP solution logging patterns for Excel file processing.
"""

import base64
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final, Optional

try:
    import pytz
except ImportError:
    pytz = None

# Translation function will be imported dynamically


def get_translation_function():
    """Get translation function dynamically to avoid import-time issues."""
    try:
        from utils.i18n import _

        # Test if _ is properly initialized
        _ = _
        return _
    except (ImportError, NameError):
        # Fallback if i18n is not available or not initialized
        return lambda x: x


class TZFormatter(logging.Formatter):
    """Timezone-aware formatter for log messages."""

    def __init__(
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None, timezone=None
    ):
        super().__init__(fmt, datefmt)
        self.timezone = timezone

    def formatTime(self, record, datefmt: Optional[str] = None) -> str:
        if self.timezone and pytz:
            dt = datetime.fromtimestamp(record.created, self.timezone)
        else:
            dt = datetime.fromtimestamp(record.created)

        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec="milliseconds")
        return s


class ExcelFileLogger(Logger):
    """SAP-style file logger for Excel file processing."""

    DEFAULT_TIMEZONE = "Asia/Tokyo"

    def __init__(
        self,
        name: str,
        log_dir: str,
        level: int = logging.INFO,
        timezone: Optional[str] = DEFAULT_TIMEZONE,
    ):
        super().__init__(name, level)
        self.log_dir = log_dir
        self.file_handlers: dict[str, RotatingFileHandler] = {}
        self.file_levels: dict[str, int] = {}
        self.excel_log_filenames: dict[str, str] = {}  # Cache for Excel log filenames

        # Setup timezone
        if pytz and timezone:
            try:
                self.timezone = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                print(f"Unknown timezone: {timezone}. Falling back to UTC.")
                self.timezone = pytz.UTC if pytz else None
        else:
            self.timezone = None

        self.console_formatter = TZFormatter(
            "%(asctime)s %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            timezone=self.timezone,
        )

        # Do not initialize default log file anymore

    def _setup_handler(self, file_name: str, level: int) -> None:
        log_file = os.path.join(self.log_dir, file_name)
        handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(self.console_formatter)
        handler.setLevel(level)
        self.file_handlers[file_name] = handler
        self.file_levels[file_name] = level
        self.addHandler(handler)

    def _log_to_file(
        self, level: int, msg: str, file_name: Optional[str], *args, **kwargs
    ) -> None:
        """Log message to specific file and console."""
        if file_name is None:
            # If no file name provided, just log to console
            record = self.makeRecord(
                self.name,
                level,
                "",
                0,
                msg,
                args,
                None,
                func=None,
                extra=None,
                **kwargs,
            )
            console_msg = self.console_formatter.format(record)
            print(console_msg)
            return

        elif file_name and not file_name.endswith(".log"):
            file_name += ".log"

        if file_name not in self.file_levels:
            self._setup_handler(file_name, self.level)

        file_level = self.file_levels[file_name]
        if level >= file_level:
            record = self.makeRecord(
                self.name,
                level,
                "",
                0,
                msg,
                args,
                None,
                func=None,
                extra=None,
                **kwargs,
            )
            self.file_handlers[file_name].emit(record)

            # Also log to console with safe Unicode handling
            console_msg = self.console_formatter.format(record)
            try:
                print(console_msg)
            except UnicodeEncodeError:
                # Fallback to UTF-8 encoding if console doesn't support Unicode
                print(console_msg.encode("utf-8", errors="replace").decode("utf-8"))

    def debug(self, msg: str, file_name: Optional[str] = None, *args, **kwargs) -> None:
        self._log_to_file(logging.DEBUG, msg, file_name, *args, **kwargs)

    def info(self, msg: str, file_name: Optional[str] = None, *args, **kwargs) -> None:
        self._log_to_file(logging.INFO, msg, file_name, *args, **kwargs)

    def warning(
        self, msg: str, file_name: Optional[str] = None, *args, **kwargs
    ) -> None:
        self._log_to_file(logging.WARNING, msg, file_name, *args, **kwargs)

    def error(self, msg: str, file_name: Optional[str] = None, *args, **kwargs) -> None:
        self._log_to_file(logging.ERROR, msg, file_name, *args, **kwargs)

    def start_excel_logging(self, excel_filename: str) -> str:
        """Start logging for a specific Excel file."""
        translate = get_translation_function()  # Get translation function dynamically

        # Check if this is an application log (starts with special prefixes)
        if excel_filename.startswith(
            ("error_", "app_", "log_", "batch_", "summary_", "project_end_")
        ):
            # For application logs, use the filename as-is
            log_filename = (
                excel_filename
                if excel_filename.endswith(".log")
                else f"{excel_filename}.log"
            )
        else:
            # For Excel files, generate timestamp + Excel filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_stem = Path(excel_filename).stem
            log_filename = f"{timestamp}_{excel_stem}.log"

        # Cache the log filename for this Excel file
        self.excel_log_filenames[excel_filename] = log_filename

        # Setup handler for this specific Excel file
        self._setup_handler(log_filename, self.level)

        # Write header
        self.info("=" * 80, log_filename)
        self.info(
            translate("SAP IF Design Generation Tool - Processing Log"), log_filename
        )
        if excel_filename.startswith("log_"):
            self.info(translate("Application Log"), log_filename)
        else:
            self.info(translate("Excel File: {}").format(excel_filename), log_filename)
        self.info(
            translate("Start Time: {}").format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            log_filename,
        )
        return os.path.join(self.log_dir, log_filename)

    def get_excel_log_filename(self, excel_filename: str) -> str:
        """Get the log filename for a specific Excel file."""
        # Return cached filename if exists
        if excel_filename in self.excel_log_filenames:
            return self.excel_log_filenames[excel_filename]

        # If not cached, this means start_excel_logging hasn't been called yet
        # Generate the same filename format but don't cache it (let start_excel_logging do that)
        if (
            excel_filename.startswith("error_")
            or excel_filename.startswith("app_")
            or excel_filename.startswith("log_")
            or excel_filename.startswith("batch_")
            or excel_filename.startswith("summary_")
            or excel_filename.startswith("project_end_")
        ):
            # For application logs, use the filename as-is
            log_filename = (
                excel_filename
                if excel_filename.endswith(".log")
                else f"{excel_filename}.log"
            )
        else:
            # For Excel files, generate timestamp + Excel filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_stem = Path(excel_filename).stem
            log_filename = f"{timestamp}_{excel_stem}.log"

        # Cache it for consistency
        self.excel_log_filenames[excel_filename] = log_filename
        return log_filename


def setup_logger(name: str, log_dir: str, level: int) -> ExcelFileLogger:
    """Setup and return a configured ExcelFileLogger."""
    os.makedirs(log_dir, exist_ok=True)
    return ExcelFileLogger(name, log_dir, level)


def get_logger(
    name: str, log_dir: str = "logs", level: int = logging.INFO
) -> ExcelFileLogger:
    """Get or create a logger instance."""
    key_components = [name, log_dir, str(level)]
    key = (
        base64.urlsafe_b64encode("|".join(key_components).encode()).decode().rstrip("=")
    )
    logger_key = f"ExcelFileLogger_{key}"

    __logger = logging.getLogger(logger_key)
    if not isinstance(__logger, ExcelFileLogger):
        __logger = setup_logger(name, log_dir, level)

    return __logger


# Global logger instance
logger: Final[ExcelFileLogger] = get_logger("if_gen_tool", level=logging.INFO)


@contextmanager
def if_gen_logging(excel_filename: str):
    """Context manager for Excel file logging."""
    log_path = logger.start_excel_logging(excel_filename)
    try:
        yield log_path
    finally:
        pass  # Logger handles cleanup automatically
