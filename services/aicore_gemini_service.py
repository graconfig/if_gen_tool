"""
SAP AI Core Gemini服务实现
"""

from typing import Dict, Any, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import time

from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from gen_ai_hub.proxy.native.google_vertexai.clients import GenerativeModel
from gen_ai_hub.proxy.native.openai import embeddings
from services.aicore_base_service import AIServiceBase
from utils.exceptions import AIServiceError


class AICoreGeminiService(AIServiceBase):
    """SAP AI Core Gemini服务实现"""

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
        self.provider = "gemini"
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
                self._track_llm_tokens(
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
            self._handle_llm_error(e, "Gemini")
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

            if hasattr(response, "usage") and response.usage:
                total_tokens = response.usage.total_tokens
                self._track_embedding_tokens(total_tokens, "sap_aicore")

            return [emb.embedding for emb in response.data]
        except Exception as e:
            self._handle_embedding_error(e, "Gemini")
            raise
