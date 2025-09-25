"""
Configuration management.
"""

import os
from typing import Dict, Any

from core.consts import AIProvider, Languages


class ConfigurationManager:
    def __init__(self):
        pass

    def get_excel_config(self) -> Dict[str, Any]:
        return {
            "sheet_name": "IF項目定義",
            "header_row": 6,
            "start_row": 13,
            "batch_size": int(os.getenv("LLM_BATCH_SIZE", 30)),
            "max_concurrent_batches": int(os.getenv("LLM_MAX_WORKERS", 5)),
        }

    def get_file_config(self) -> Dict[str, Any]:
        return {
            "max_concurrent_files": int(os.getenv("FILE_MAX_WORKERS", 5)),
        }

    def get_column_mappings(self) -> Dict[str, Dict[str, str]]:
        # excel输入输出列映射
        return {
            "input_header_cols": {"module": "C", "if_name": "H", "if_desc": "I"},
            "input_row_cols": {
                "field_name": "C",
                "key_flag": "D",
                "obligatory": "E",
                "data_type": "I",
                "field_id": "H",
                "length_total": "J",
                "length_dec": "K",
                "field_text": "L",
                "sample_value": "N",
            },
            "output_columns": {
                "field_name": "S",
                "key_flag": "T",
                "obligatory": "U",
                "table_id": "V",
                "field_id": "W",
                "data_type": "X",
                "length_total": "Y",
                "length_dec": "Z",
                "notes": "AA",
                "sample_value": "AB",
                "match": "AC",
            },
        }

    def get_model_config(self) -> Dict[str, Any]:
        return {
            "default_provider": os.getenv("AI_PROVIDER", AIProvider.DEFAULT),
            # OpenAI models via AI Core
            "openai": {
                "provider_name": "SAP AICore OpenAI",
                "llm_model": os.getenv("OPENAI_LLM_MODEL", "gpt-4o"),
                "embedding_model": os.getenv(
                    "TEXT_EMBEDDING_MODEL", "text-embedding-ada-002"
                ),
                "llm_deployment_id": os.getenv("OPENAI_LLM_DEPLOYMENT_ID"),
                "embedding_deployment_id": os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_ID"),
            },
            "claude": {
                "provider_name": "SAP AICore Claude",
                "llm_model": os.getenv(
                    "CLAUDE_LLM_MODEL", "anthropic--claude-3-5-sonnet"
                ),
                "embedding_model": os.getenv(
                    "TEXT_EMBEDDING_MODEL", "text-embedding-ada-002"
                ),
            },
            # Gemini models via AI Core
            "gemini": {
                "provider_name": "SAP AICore Gemini",
                "llm_model": os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-pro"),
                "embedding_model": os.getenv(
                    "TEXT_EMBEDDING_MODEL", "text-embedding-002"
                ),
                "llm_deployment_id": os.getenv("GEMINI_LLM_DEPLOYMENT_ID"),
                "embedding_deployment_id": os.getenv("GEMINI_EMBEDDING_DEPLOYMENT_ID"),
            },
        }

    def get_language_config(self) -> Dict[str, Any]:
        return {
            "language": self._get_default_language(),
            "supported_languages": Languages.SUPPORTED,
        }

    def _get_default_language(self) -> str:
        """Get default language following priority order."""
        # Priority 1: Check environment variable
        env_lang = os.getenv("LANGUAGE", "").lower()
        if env_lang in Languages.SUPPORTED:
            return env_lang

        # Priority 2: Try to detect OS language
        try:
            import locale

            # Try different methods to get system locale
            system_locale = None

            # Method 1: Get default locale
            try:
                system_locale = locale.getdefaultlocale()[0]
            except (TypeError, ValueError):
                pass

            # Method 2: Get current locale if method 1 fails
            if not system_locale:
                try:
                    system_locale = locale.getlocale()[0]
                except (TypeError, ValueError):
                    pass

            # Method 3: Try Windows-specific method
            if not system_locale and os.name == "nt":
                try:
                    import ctypes

                    windll = ctypes.windll.kernel32
                    locale_id = windll.GetUserDefaultUILanguage()

                    # Common Windows locale IDs
                    if (
                        locale_id == 0x0804 or locale_id == 0x0404
                    ):  # Simplified/Traditional Chinese
                        return Languages.ZH
                    elif locale_id == 0x0411:  # Japanese
                        return Languages.JA
                    elif locale_id in [0x0409, 0x0809, 0x0C09]:  # English variants
                        return Languages.EN
                except Exception:
                    pass

            # Parse locale string if we have one
            if system_locale:
                system_locale = system_locale.lower()
                if system_locale.startswith("zh"):
                    return Languages.ZH
                elif system_locale.startswith("ja"):
                    return Languages.JA
                elif system_locale.startswith("en"):
                    return Languages.EN

        except Exception:
            # If locale detection fails, continue to fallback
            pass

        # Fallback: Check LANG environment variable (Unix-like systems)
        system_lang = os.getenv("LANG", "").lower()
        if system_lang.startswith("zh"):
            return Languages.ZH
        elif system_lang.startswith("ja"):
            return Languages.JA
        elif system_lang.startswith("en"):
            return Languages.EN

        # Priority 3: Final fallback to English
        return Languages.DEFAULT
