"""
Internationalization (i18n) module using gettext for multi-language support.
Supports Chinese (zh), Japanese (ja), and English (en).
"""

import gettext
import os
from pathlib import Path
from typing import Optional


class LanguageManager:
    """Manages language settings and gettext translations."""

    SUPPORTED_LANGUAGES = {"en": "English", "zh": "中文", "ja": "日本語"}

    DEFAULT_LANGUAGE = "ja"  # Changed default to Japanese
    DOMAIN = "if_gen_tool"

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent

        self.base_dir = base_dir
        self.locale_dir = base_dir / "locale"
        self.current_language = self.DEFAULT_LANGUAGE
        self._translator = None

        # Initialize with default language
        self.set_language(self._get_default_language())

    def _get_default_language(self) -> str:
        """Get default language by calling the centralized utility function."""
        from utils.tools import detect_system_language
        return detect_system_language()

    def set_language(self, language: str) -> bool:
        """Set current language for translations."""
        if language not in self.SUPPORTED_LANGUAGES:
            print(
                f"Warning: Unsupported language '{language}'. Using '{self.DEFAULT_LANGUAGE}'."
            )
            language = self.DEFAULT_LANGUAGE

        self.current_language = language

        try:
            if language == "en":
                # For English, use NullTranslations (no translation needed)
                self._translator = gettext.NullTranslations()
            else:
                # Load translation for other languages
                mo_path = (
                    self.locale_dir / language / "LC_MESSAGES" / f"{self.DOMAIN}.mo"
                )
                if mo_path.exists():
                    try:
                        with open(mo_path, "rb") as f:
                            self._translator = gettext.GNUTranslations(f)
                    except Exception as e:
                        print(
                            f"Error loading translation file {mo_path}: {e}. Using fallback."
                        )
                        self._translator = gettext.NullTranslations()
                else:
                    # Fallback to NullTranslations if file doesn't exist
                    print(f"Translation file not found: {mo_path}. Using fallback.")
                    self._translator = gettext.NullTranslations()
        except Exception as e:
            print(f"Error loading translation for '{language}': {e}. Using fallback.")
            self._translator = gettext.NullTranslations()

        return True

    def get_current_language(self) -> str:
        """Get current language code."""
        return self.current_language

    def get_language_name(self, language: Optional[str] = None) -> str:
        """Get human-readable language name."""
        lang = language or self.current_language
        return self.SUPPORTED_LANGUAGES.get(lang, lang)

    def translate(self, message: str) -> str:
        """Translate a message using current language settings."""
        if self._translator is None:
            return message
        return self._translator.gettext(message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Translate message with plural form support."""
        if self._translator is None:
            return singular if n == 1 else plural
        return self._translator.ngettext(singular, plural, n)


# Global language manager instance
_language_manager = None


def get_language_manager() -> LanguageManager:
    """Get global language manager instance."""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def set_language(language: str) -> bool:
    """Set global language for the application."""
    return get_language_manager().set_language(language)


def get_current_language() -> str:
    """Get current language code."""
    return get_language_manager().get_current_language()


def _(message: str) -> str:
    """Translate message using current language settings.

    This is the standard gettext shorthand function for translation.
    Usage: _("Hello, World!")
    """
    return get_language_manager().translate(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate message with plural form support.

    Usage: ngettext("1 file", "{} files", count).format(count)
    """
    return get_language_manager().ngettext(singular, plural, n)


def initialize_i18n(
    language: Optional[str] = None, base_dir: Optional[Path] = None
) -> None:
    """Initialize internationalization for the application.

    Args:
        language: Language code to use (en, zh, ja). If None, uses default detection.
        base_dir: Base directory for the project. If None, auto-detects.
    """
    global _language_manager

    if base_dir is None:
        base_dir = Path(__file__).parent.parent

    _language_manager = LanguageManager(base_dir)

    if language:
        _language_manager.set_language(language)
