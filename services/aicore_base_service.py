"""
Abstract base class for AI services.
Defines the common interface that all AI service implementations must follow,
while providing common functionality through mixin-style methods.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

from prompts.prompts_manager import get_prompt_manager
from prompts.schemas_manager import get_schema_manager
from utils.token_statistics import track_embedding_tokens, track_llm_tokens
from utils.i18n import _
from utils.sap_logger import logger


class AIServiceBase(ABC):
    """Abstract base class for all AI service implementations."""

    def __init__(
        self,
        llm_model: str,
        embedding_model: str,
        language: str = "en",
        llm_deployment_id: Optional[str] = None,
        embedding_deployment_id: Optional[str] = None,
    ):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.language = language
        self.llm_deployment_id = llm_deployment_id
        self.embedding_deployment_id = embedding_deployment_id
        self.provider = self.provider_name # Set provider name from property
        self.prompt_manager = get_prompt_manager()
        self.schema_manager = get_schema_manager()

    @abstractmethod
    def call_with_function(
        self, prompt: str, function_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the LLM with a function/tool schema."""
        pass

    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        pass

    def get_rag_matching_prompt(
        self, input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]
    ) -> str:
        """Get the RAG matching prompt using the new manager."""
        return self.prompt_manager.get(
            "field_matching", self.language, input_fields=input_fields, context=context
        )

    def get_view_selection_prompt(
        self, candidate_views_df: pd.DataFrame, input_fields: List[Dict[str, Any]]
    ) -> str:
        """Get the view selection prompt using the new manager."""
        return self.prompt_manager.get(
            "view_selection",
            self.language,
            candidate_views_df=candidate_views_df,
            input_fields=input_fields,
        )

    def get_view_selection_schema(self) -> Dict[str, Any]:
        """Get the view selection schema using the new manager."""
        return self.schema_manager.get(
            "view_selection", self.language, self.provider
        )

    def get_field_matching_schema(self) -> Dict[str, Any]:
        """Get the field matching schema using the new manager."""
        return self.schema_manager.get(
            "field_matching", self.language, self.provider
        )

    def _track_embedding_tokens(self, tokens: int, provider: str):
        """Track embedding token usage."""
        track_embedding_tokens(tokens, provider)

    def _track_llm_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        provider: str = None,
    ):
        """Track LLM token usage."""
        track_llm_tokens(input_tokens, output_tokens, total_tokens, provider)

    def _handle_embedding_error(self, error: Exception, provider_name: str) -> None:
        """Handle embedding generation errors with consistent logging."""
        error_msg = _("Failed to generate embeddings with {}: {}").format(
            provider_name, str(error)
        )
        logger.error(error_msg)
        raise error from error

    def _handle_llm_error(self, error: Exception, provider_name: str) -> None:
        """Handle LLM call errors with consistent logging."""
        error_msg = _("LLM function call failed with {}: {}").format(
            provider_name, str(error)
        )
        logger.error(error_msg)
        raise error from error

    @property
    def provider_name(self) -> str:
        """Get the provider name for this service."""
        class_name = self.__class__.__name__.lower()
        if "claude" in class_name:
            return "claude"
        elif "gemini" in class_name:
            return "gemini"
        elif "openai" in class_name:
            return "openai"
        else:
            return "unknown"