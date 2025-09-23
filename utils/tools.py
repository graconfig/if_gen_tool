"""
Common utility functions used across the application.
"""

import os
import re
import locale
import ctypes
from typing import List
from utils.i18n import _


def detect_system_language() -> str:
    """
    Detects the system's default language and returns a two-letter code.
    Follows a priority order: ENV VAR -> OS LOCALE -> FALLBACK.
    """
    # Supported language codes
    SUPPORTED_LANGUAGES = {"en", "zh", "ja"}
    DEFAULT_LANGUAGE = "en"

    # Priority 1: Check explicit environment variable
    env_lang = os.getenv("LANGUAGE", "").lower()
    if env_lang in SUPPORTED_LANGUAGES:
        return env_lang

    # Priority 2: Try to detect OS language
    try:
        system_locale = None
        # Method A: Get default locale
        try:
            system_locale = locale.getdefaultlocale()[0]
        except (TypeError, ValueError, IndexError):
            pass

        # Method B: Windows-specific
        if not system_locale and os.name == "nt":
            try:
                locale_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                # Common Windows locale IDs
                lang_map = {
                    0x0404: "zh", 0x0804: "zh",  # Chinese (Taiwan, PRC)
                    0x0411: "ja",              # Japanese
                    0x0409: "en", 0x0809: "en"  # English (US, UK)
                }
                if locale_id in lang_map:
                    return lang_map[locale_id]
            except Exception:
                pass

        # Parse locale string if we have one (e.g., "en_US.UTF-8")
        if system_locale:
            lang_code = system_locale.split('_')[0].lower()
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code

    except Exception:
        # If locale detection fails, continue to next fallback
        pass

    # Priority 3: Fallback to LANG environment variable (Unix-like systems)
    system_lang = os.getenv("LANG", "").lower()
    if system_lang:
        lang_code = system_lang.split('_')[0]
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code

    # Final fallback
    return DEFAULT_LANGUAGE


def sanitize_text(text: str) -> str:
    """Sanitize text for safe database queries.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text with escaped quotes
    """
    if not text:
        return ""
    return text.replace("'", "''").replace('"', '""')


def format_in_clause(items: List[str]) -> str:
    """Format a list of items into an SQL IN clause.

    Args:
        items: List of items to format

    Returns:
        Formatted SQL IN clause string
    """
    if not items:
        return "('')"
    formatted_items = [f"'{sanitize_text(str(item))}'" for item in items]
    return f"({', '.join(formatted_items)})"


def parse_notes(notes_text: str) -> tuple[str, str]:
    """Parse notes text to extract percentage and description.

    Expected format: "XX% - Description" or "XX%: Description" or "Description (XX%)"

    Args:
        notes_text: Notes text to parse

    Returns:
        Tuple of (percentage, description)
    """
    if not notes_text:
        return "", ""

    # Pattern 1: "XX% - Description" or "XX%: Description"
    pattern1 = r"^(\d+%)\s*[-:]\s*(.+)$"
    match1 = re.match(pattern1, notes_text.strip())
    if match1:
        return match1.group(1), match1.group(2).strip()

    # Pattern 2: "Description (XX%)"
    pattern2 = r"^(.+)\s*\((\d+%)\)\s*$"
    match2 = re.match(pattern2, notes_text.strip())
    if match2:
        return match2.group(2), match2.group(1).strip()

    # Pattern 3: Just percentage "XX%"
    pattern3 = r"^(\d+%)\s*$"
    match3 = re.match(pattern3, notes_text.strip())
    if match3:
        return match3.group(1), ""

    # Pattern 4: Contains percentage anywhere
    pattern4 = r"(\d+%)"
    match4 = re.search(pattern4, notes_text)
    if match4:
        percentage = match4.group(1)
        # Remove percentage from description
        description = re.sub(r"\s*\d+%\s*[-:()]*\s*", " ", notes_text).strip()
        return percentage, description

    # No percentage found, return everything as description
    return "", notes_text.strip()


def clean_field_id(raw_field_id: str) -> str:
    """Clean field ID to remove view name prefix.

    Args:
        raw_field_id: Raw field ID that may contain view name prefix

    Returns:
        Clean field ID without view name prefix
    """
    if not raw_field_id:
        return ""

    # Remove view name prefix (e.g., "I_TIMESHEETRECORD.RECEIVERCOSTCENTER" -> "RECEIVERCOSTCENTER")
    if "." in raw_field_id:
        return raw_field_id.split(".")[-1]
    else:
        return raw_field_id


def normalize_key_flag(key_flag_raw) -> str:
    """Normalize key flag value to standard format.

    Args:
        key_flag_raw: Raw key flag value

    Returns:
        Normalized key flag ("X" for true, "" for false)
    """
    if isinstance(key_flag_raw, bool):
        return "X" if key_flag_raw else ""
    elif isinstance(key_flag_raw, str):
        return "X" if key_flag_raw.lower() in ["true", "y", "yes", "x"] else ""
    else:
        return ""

def format_execution_time(self, seconds: float) -> str:
    """将执行时间格式化为 hh:mm:ss (仅适用于24小时内)。

    Args:
        seconds: 以秒为单位的时间

    Returns:
        格式化的时间字符串 "hh:mm:ss"
    """
    # gmtime 将秒数转换为一个时间结构体（UTC时间）
    # strftime 根据指定的格式（%H:%M:%S）将该结构体格式化为字符串
    """将秒数转换为小时、分钟、秒的格式"""
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    return _("{}h {}m {:.2f}s").format(hours, minutes, seconds)

    #return time.strftime("%H:%M:%S", time.gmtime(seconds))