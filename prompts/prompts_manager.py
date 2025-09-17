"""
Dynamic prompt template manager with internationalization support.
Automatically selects appropriate language templates based on current locale.
"""

from typing import Dict, List, Any, Type

import pandas as pd

from utils.i18n import get_current_language
# Import all template classes
from prompts.prompts_en import EnPromptTemplates
from prompts.prompts_jp import JapanesePromptTemplates
from prompts.prompts_zh import ChinesePromptTemplates


class PromptTemplateManager:
    """Manages prompt templates for different languages."""

    _template_classes = {
        'en': EnPromptTemplates,
        'zh': ChinesePromptTemplates,
        'ja': JapanesePromptTemplates
    }

    @classmethod
    def get_template_class(cls, language: str = None) -> Type:
        """Get template class for specified language.
        
        Args:
            language: Language code (en, zh, ja). If None, uses current language.
            
        Returns:
            Template class for the specified language.
        """
        if language is None:
            language = get_current_language()

        # Fallback to English if language not supported
        return cls._template_classes.get(language, EnPromptTemplates)

    @classmethod
    def get_field_matching_prompt(cls, input_fields: List[Dict[str, Any]],
                                  context: List[Dict[str, Any]],
                                  language: str = None) -> str:
        """Get field matching prompt in specified language."""
        template_class = cls.get_template_class(language)
        return template_class.get_field_matching_prompt(input_fields, context)

    @classmethod
    def get_view_selection_prompt(cls, candidate_views_df: pd.DataFrame,
                                  input_fields: List[Dict[str, Any]],
                                  language: str = None) -> str:
        """Get view selection prompt in specified language."""
        template_class = cls.get_template_class(language)
        return template_class.get_view_selection_prompt(candidate_views_df, input_fields)

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported language codes."""
        return list(cls._template_classes.keys())

    @classmethod
    def is_language_supported(cls, language: str) -> bool:
        """Check if language is supported."""
        return language in cls._template_classes


# Global template manager functions for backward compatibility
def get_field_matching_prompt(input_fields: List[Dict[str, Any]],
                              context: List[Dict[str, Any]],
                              language: str = None) -> str:
    """Get field matching prompt using current or specified language."""
    return PromptTemplateManager.get_field_matching_prompt(input_fields, context, language)


def get_view_selection_prompt(candidate_views_df: pd.DataFrame,
                              input_fields: List[Dict[str, Any]],
                              language: str = None) -> str:
    """Get view selection prompt using current or specified language."""
    return PromptTemplateManager.get_view_selection_prompt(candidate_views_df, input_fields, language)
