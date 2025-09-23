"""
SAP AI Core OpenAI服务实现
"""

import json
from typing import Dict, Any, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import time

from gen_ai_hub.proxy.native.openai import chat, embeddings
from services.aicore_base_service import AIServiceBase
from utils.exceptions import AIServiceError


class AICoreOpenAIService(AIServiceBase):
    """SAP AI Core OpenAI服务实现"""

    def __init__(
        self,
        llm_model: str,
        embedding_model: str,
        language: str = "en",
        llm_deployment_id: str = None,
        embedding_deployment_id: str = None,
    ):
        super().__init__(
            llm_model,
            embedding_model,
            language,
            llm_deployment_id,
            embedding_deployment_id,
        )
        self.provider = "openai"
        self._llm_client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception, AIServiceError)),
        reraise=True,
    )
    def call_with_function(
        self, prompt: str, function_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 记录开始时间
        start_time = time.time()

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
                self._track_llm_tokens(
                    input_tokens, output_tokens, total_tokens, "sap_aicore"
                )

            # Extract tool call results
            if response.choices and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                return json.loads(tool_call.function.arguments)

            return {}

        except Exception as e:
            self._handle_llm_error(e, "OpenAI")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception, AIServiceError)),
        reraise=True,
    )
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
                self._track_embedding_tokens(total_tokens, "sap_aicore_openai")

            return [emb.embedding for emb in response.data]
        except Exception as e:
            self._handle_embedding_error(e, "OpenAI")
            raise
