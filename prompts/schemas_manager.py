"""
Function schemas for different LLM providers.
Defines the structure for AI function calling capabilities.
"""

from typing import Dict, Any

from utils.i18n import get_current_language


class FunctionSchemas:
    """Unified function schemas manager for different LLM providers."""

    @staticmethod
    def _get_language_specific_schemas(language: str = None):
        """Get language-specific schema module."""
        if language is None:
            language = get_current_language()

        if language == "zh":
            from . import schemas_zh

            return schemas_zh
        elif language == "ja":
            from . import schemas_jp

            return schemas_jp
        else:  # default to English
            from . import schemas_en

            return schemas_en

    @staticmethod
    def get_field_matching_schema(
            provider: str, language: str = None
    ) -> Dict[str, Any]:
        """Get field matching schema for specific provider and language."""
        provider = provider.lower()
        schemas_module = FunctionSchemas._get_language_specific_schemas(language)

        if provider == "claude":
            return schemas_module.ClaudeSchemas.get_field_matching_tool()
        elif provider == "openai":
            return schemas_module.OpenAISchemas.get_field_matching_tool()
        elif provider == "gemini":
            return schemas_module.GeminiSchemas.get_field_matching_tool()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def get_view_selection_schema(
            provider: str, language: str = None
    ) -> Dict[str, Any]:
        """Get view selection schema for specific provider and language."""
        provider = provider.lower()
        schemas_module = FunctionSchemas._get_language_specific_schemas(language)

        if provider == "claude":
            return schemas_module.ClaudeSchemas.get_view_selection_tool()
        elif provider == "openai":
            return schemas_module.OpenAISchemas.get_view_selection_tool()
        elif provider == "gemini":
            return schemas_module.GeminiSchemas.get_view_selection_tool()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
