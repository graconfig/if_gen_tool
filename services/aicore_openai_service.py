"""
SAP AI Core OpenAI服务实现
"""

import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv
from gen_ai_hub.proxy.native.openai import chat, embeddings

from prompts.prompts_manager import PromptTemplateManager
from prompts.schemas_manager import FunctionSchemas
from utils.token_statistics import track_embedding_tokens, track_llm_tokens

load_dotenv()


class AICoreOpenAIService:
    """SAP AI Core OpenAI服务实现"""

    def __init__(
            self,
            llm_model: str,
            embedding_model: str,
            language: str = "en",
            llm_deployment_id: str = None,
            embedding_deployment_id: str = None,
    ):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.llm_deployment_id = llm_deployment_id
        self.embedding_deployment_id = embedding_deployment_id
        self.language = language
        self.logger = logging.getLogger(__name__)
        self._llm_client = None

    def call_with_function(
            self, prompt: str, function_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        messages = [{"role": "user", "content": prompt}]

        # Convert function schema to OpenAI tools format
        tools = [function_schema] if function_schema.get("type") == "function" else []

        # Prepare request parameters - use deployment_id if available, otherwise use model_name
        request_params = {
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto" if tools else None,
        }

        if self.llm_deployment_id:
            request_params["deployment_id"] = self.llm_deployment_id
        else:
            request_params["model_name"] = self.llm_model

        try:
            response = chat.completions.create(**request_params)

            if hasattr(response, "usage"):
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                track_llm_tokens(
                    input_tokens, output_tokens, total_tokens, "sap_aicore"
                )

            # Extract tool call results
            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                return json.loads(tool_call.function.arguments)

            return {}

        except Exception as e:
            raise RuntimeError(f"LLM function call failed: {e}") from e

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Prepare request parameters - use deployment_id if available, otherwise use model_name
        request_params = {"input": texts}

        if self.embedding_deployment_id:
            request_params["deployment_id"] = self.embedding_deployment_id
        else:
            request_params["model_name"] = self.embedding_model

        try:
            response = embeddings.create(**request_params)

            # Track embedding token usage
            if hasattr(response, "usage") and response.usage:
                total_tokens = response.usage.total_tokens
                track_embedding_tokens(total_tokens, "sap_aicore_openai")

            return [emb.embedding for emb in response.data]
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            return []

    def get_rag_matching_prompt(
            self, input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]
    ) -> str:
        return PromptTemplateManager.get_field_matching_prompt(
            input_fields, context, 'en'
            # input_fields, context, self.language
        )

    def get_view_selection_prompt(
            self, candidate_views_df, input_fields: List[Dict[str, Any]]
    ) -> str:
        return PromptTemplateManager.get_view_selection_prompt(
            candidate_views_df, input_fields, 'en'
            # candidate_views_df, input_fields, self.language
        )

    def get_view_selection_schema(self) -> Dict[str, Any]:
        """Get OpenAI-specific view selection schema."""
        return FunctionSchemas.get_view_selection_schema("openai","en")

    def get_field_matching_schema(self) -> Dict[str, Any]:
        """Get OpenAI-specific field matching schema."""
        return FunctionSchemas.get_field_matching_schema("openai","en")
