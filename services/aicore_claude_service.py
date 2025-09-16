"""
SAP AI Core Claude服务实现
"""

import logging
from typing import Dict, Any, List
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from gen_ai_hub.proxy.native.amazon.clients import Session
from gen_ai_hub.proxy.native.openai import embeddings

from prompts.prompts_manager import PromptTemplateManager
from prompts.schemas_manager import FunctionSchemas
from utils.token_statistics import track_embedding_tokens, track_llm_tokens
from botocore.config import Config


class AICoreClaudeService:
    """SAP AI Core Claude服务实现"""

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
        self.language = language
        self.logger = logging.getLogger(__name__)
        self._llm_client = None

    @property
    def llm_client(self):
        if self._llm_client is None:
            config = Config(
                read_timeout=300,
                connect_timeout=6,
                retries={"max_attempts": 3, "mode": "adaptive"},
            )
            self._llm_client = Session().client(model_name=self.llm_model,
                                                config=config)
        return self._llm_client

    def call_with_function(
            self, prompt: str, function_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
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

            invoke_messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            invoke_model_tools = self._convert_tool_schema_for_invoke_model(function_schema)
            model_body = {
                "anthropic_version":"bedrock-2023-05-31",
                "messages":invoke_messages,
                "tools":invoke_model_tools,
                "max_tokens":16384,
                # "betas":["context-1m-2025-08-07"],
            }

            response_body = self.llm_client.invoke_model(
                body=json.dumps(model_body)
            )

            response = json.loads(response_body.get('body').read())

            if "usage" in response:
                usage = response["usage"]
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                track_llm_tokens(
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
            raise RuntimeError(f"LLM function call failed: {e}") from e

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = embeddings.create(input=texts, model_name=self.embedding_model)

            if hasattr(response, "usage") and response.usage:
                total_tokens = response.usage.total_tokens
                track_embedding_tokens(total_tokens, "sap_aicore")

            return [emb.embedding for emb in response.data]
        except Exception as e:
            return []

    def get_rag_matching_prompt(
            self, input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]
    ) -> str:
        return PromptTemplateManager.get_field_matching_prompt(
            input_fields, context, 'en'
            # input_fields, context, self.language
        )

    def get_view_selection_prompt(
            self, candidate_views_df: pd.DataFrame, input_fields: List[Dict[str, Any]]
    ) -> str:
        return PromptTemplateManager.get_view_selection_prompt(
            candidate_views_df, input_fields, 'en'
            # candidate_views_df, input_fields, self.language
        )

    def get_view_selection_schema(self) -> Dict[str, Any]:
        """Get Claude-specific view selection schema."""
        return FunctionSchemas.get_view_selection_schema("claude","en")

    def get_field_matching_schema(self) -> Dict[str, Any]:
        """Get Claude-specific field matching schema."""
        return FunctionSchemas.get_field_matching_schema("claude","en")

    def _convert_tool_schema_for_invoke_model(self, converse_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                "input_schema": tool_spec.get("inputSchema", {}).get("json", {})
            }
            native_tools.append(native_tool)
        return native_tools
