"""
SAP AI Core Claude服务实现
"""

from typing import Dict, Any, List
import json
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import time

load_dotenv()

from gen_ai_hub.proxy.native.amazon.clients import Session
from gen_ai_hub.proxy.native.openai import embeddings

from utils.token_statistics import track_embedding_tokens, track_llm_tokens
from botocore.config import Config
from services.aicore_base_service import AIServiceBase
from utils.exceptions import AIServiceError


class AICoreClaudeService(AIServiceBase):
    """SAP AI Core Claude服务实现"""

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
        self.provider = "claude"
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            config = Config(
                read_timeout=300,
                connect_timeout=6,
                retries={"max_attempts": 3, "mode": "adaptive"},
            )
            self._llm_client = Session().client(
                model_name=self.llm_model, config=config
            )
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

        # conversation = [{"role": "user", "content": [{"text": prompt}]}]

        try:
            # response = self.llm_client.converse(
            #     messages=conversation,
            #     toolConfig=function_schema,
            #     additionalModelRequestFields={
            #         "betas": ["context-1m-2025-08-07"]
            #     }
            # # inferenceConfig={"temperature": 0.1, "topP": 0.9},
            # )

            invoke_messages = [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ]
            invoke_model_tools = self._convert_tool_schema_for_invoke_model(
                function_schema
            )
            model_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": invoke_messages,
                "tools": invoke_model_tools,
                "max_tokens": 64000,
                # "betas":["context-1m-2025-08-07"],
            }

            response_body = self.llm_client.invoke_model(body=json.dumps(model_body))

            response = json.loads(response_body.get("body").read())

            if "usage" in response:
                usage = response["usage"]
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                self._track_llm_tokens(
                    input_tokens, output_tokens, total_tokens, "sap_aicore_claude"
                )
            if "content" in response:
                for content_item in response["content"]:
                    if content_item.get("type") == "tool_use":
                        return content_item.get("input", {})

            # if "usage" in response:
            #     usage = response["usage"]
            #     input_tokens = usage.get("inputTokens", 0)
            #     output_tokens = usage.get("outputTokens", 0)
            #     total_tokens = usage.get("totalTokens", 0)
            #     track_llm_tokens(
            #         input_tokens, output_tokens, total_tokens, "sap_aicore_claude"
            #     )

            # if "output" in response and "message" in response["output"]:
            #     message = response["output"]["message"]
            #     if "content" in message:
            #         for content_item in message["content"]:
            #             if "toolUse" in content_item:
            #                 tool_use = content_item["toolUse"]
            #                 return tool_use.get("input", {})

            return {}

        except Exception as e:
            self._handle_llm_error(e, "Claude")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception, AIServiceError)),
        reraise=True,
    )
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = embeddings.create(input=texts, model_name=self.embedding_model)

            if hasattr(response, "usage") and response.usage:
                total_tokens = response.usage.total_tokens
                self._track_embedding_tokens(total_tokens, "sap_aicore")

            return [emb.embedding for emb in response.data]
        except Exception as e:
            self._handle_embedding_error(e, "Claude")
            raise

    def _convert_tool_schema_for_invoke_model(
        self, converse_schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        将 Bedrock Converse API 的工具格式转换为 Anthropic InvokeModel API 的原生格式。
        """
        native_tools = []
        for tool in converse_schema.get("tools", []):
            tool_spec = tool.get("toolSpec", {})
            if not tool_spec:
                continue

            # 提取并转换
            native_tool = {
                "name": tool_spec.get("name"),
                "description": tool_spec.get("description"),
                # 关键：提取 'inputSchema' 里的 'json' 对象，并重命名为 'input_schema'
                "input_schema": tool_spec.get("inputSchema", {}).get("json", {}),
            }
            native_tools.append(native_tool)
        return native_tools
