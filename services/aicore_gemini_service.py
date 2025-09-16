"""
SAP AI Core Gemini服务实现
"""

import logging
from typing import Dict, Any, List

from dotenv import load_dotenv
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from gen_ai_hub.proxy.native.google_vertexai.clients import GenerativeModel
from gen_ai_hub.proxy.native.openai import embeddings

from prompts.prompts_manager import PromptTemplateManager
from prompts.schemas_manager import FunctionSchemas
from utils.token_statistics import track_embedding_tokens, track_llm_tokens

load_dotenv()


class AICoreGeminiService:
    """SAP AI Core Gemini服务实现"""

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
        self._proxy_client = None

    @property
    def proxy_client(self):
        if self._proxy_client is None:
            self._proxy_client = get_proxy_client("gen-ai-hub")
        return self._proxy_client

    @property
    def llm_client(self):
        if self._llm_client is None:
            if self.llm_deployment_id:
                kwargs = {"deployment_id": self.llm_deployment_id}
            else:
                kwargs = {"model_name": self.llm_model}
            self._llm_client = GenerativeModel(proxy_client=self.proxy_client, **kwargs)
        return self._llm_client

    def call_with_function(
            self, prompt: str, function_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Convert prompt to Gemini content format
        content = [{"role": "user", "parts": [{"text": prompt}]}]

        # Use function_schema directly as it's already in the correct format
        tools = [function_schema] if function_schema else []

        try:
            response = self.llm_client.generate_content(
                content,
                tools=tools if tools else None,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                },
            )

            # Track token usage if available
            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                input_tokens = getattr(usage, "prompt_token_count", 0)
                output_tokens = getattr(usage, "candidates_token_count", 0)
                total_tokens = getattr(usage, "total_token_count", 0)
                track_llm_tokens(
                    input_tokens, output_tokens, total_tokens, "sap_aicore_gemini"
                )

            # Extract function call results
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(
                        candidate.content, "parts"
                ):
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call"):
                            # Extract function call arguments
                            function_call = part.function_call
                            if hasattr(function_call, "args"):
                                return dict(function_call.args)

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

            if hasattr(response, "usage") and response.usage:
                total_tokens = response.usage.total_tokens
                track_embedding_tokens(total_tokens, "sap_aicore")

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
        """Get Gemini-specific view selection schema."""
        return FunctionSchemas.get_view_selection_schema("gemini","en")

    def get_field_matching_schema(self) -> Dict[str, Any]:
        """Get Gemini-specific field matching schema."""
        return FunctionSchemas.get_field_matching_schema("gemini","en")
