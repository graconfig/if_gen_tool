"""
Function schemas for different LLM providers - Chinese version.
Defines the structure for AI function calling capabilities.
"""

from typing import Dict, Any


class ClaudeSchemas:
    @staticmethod
    def get_field_matching_tool() -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "toolSpec": {
                        "name": "review_field_matches",
                        "description": "从提供的上下文中将输入字段与SAP CDS字段进行严格匹配 - 不允许使用上下文之外的字段名",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "review": {
                                        "type": "array",
                                        "description": "包含所有输入字段匹配结果的列表",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "row_index": {
                                                    "type": "integer",
                                                    "description": "输入字段的行索引",
                                                },
                                                "table_id": {
                                                    "type": "string",
                                                    "description": "来自上下文列表的精确SAP CDS视图名 - 必须完全匹配，如果没有找到匹配则为空字符串",
                                                },
                                                "field_id": {
                                                    "type": "string",
                                                    "description": "来自上下文列表的精确SAP CDS字段名（不含视图前缀） - 必须完全匹配，如果没有找到匹配则为空字符串",
                                                },
                                                "field_desc": {
                                                    "type": "string",
                                                    "description": "来自上下文的SAP CDS字段描述，如果没有找到匹配则为空字符串",
                                                },
                                                "data_type": {
                                                    "type": "string",
                                                    "description": "来自上下文的SAP CDS字段数据类型，如果没有找到匹配则为空字符串",
                                                },
                                                "length_total": {
                                                    "type": "string",
                                                    "description": "来自上下文的SAP CDS字段总长度，如果没有找到匹配则为空字符串",
                                                },
                                                "length_dec": {
                                                    "type": "string",
                                                    "description": "来自上下文的SAP CDS字段小数位长度，如果没有找到匹配则为空字符串",
                                                },
                                                "key_flag": {
                                                    "type": "string",
                                                    "description": "该字段是否为键字段 - 如果来自上下文为真则使用'X'，否则为空字符串",
                                                },
                                                "match": {
                                                    "type": "integer",
                                                    "description": "匹配置信度百分比（0-100）",
                                                },
                                                "notes": {
                                                    "type": "string",
                                                    "description": "说明从上下文中选择匹配的理由，或在提供的上下文中为何没有找到合适匹配的原因",
                                                },
                                            },
                                            "required": [
                                                "row_index",
                                                "match_confidence",
                                                "notes",
                                            ],
                                        },
                                    }
                                },
                                "required": ["review"],
                            }
                        },
                    }
                }
            ]
        }

    @staticmethod
    def get_view_selection_tool() -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "toolSpec": {
                        "name": "select_relevant_views",
                        "description": "基于用户所需的接口字段和业务上下文，从列表中选择最相关的3-5个CDS视图名称。",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "relevant_view_names": {
                                        "type": "array",
                                        "description": "与用户输入最相关的CDS视图名称列表。",
                                        "items": {"type": "string"},
                                    }
                                },
                                "required": ["relevant_view_names"],
                            }
                        },
                    }
                }
            ]
        }


class OpenAISchemas:
    @staticmethod
    def get_field_matching_tool() -> Dict[str, Any]:
        """
        获取字段匹配的OpenAI兼容函数架构。

        Returns:
            包含OpenAI函数配置的字典
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "基于语义相似性将输入字段与SAP CDS字段进行匹配",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "review": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "row_index": {"type": "integer"},
                                    "table_id": {"type": "string"},
                                    "field_id": {"type": "string"},
                                    "field_desc": {"type": "string"},
                                    "data_type": {"type": "string"},
                                    "length_total": {"type": "string"},
                                    "length_dec": {"type": "string"},
                                    "key_flag": {"type": "string"},
                                    "match_confidence": {"type": "integer"},
                                    "notes": {"type": "string"},
                                },
                                "required": ["row_index", "match_confidence", "notes"],
                            },
                        }
                    },
                    "required": ["review"],
                },
            },
        }

    @staticmethod
    def get_field_review_tool() -> Dict[str, Any]:
        """
        获取字段评估的OpenAI兼容函数架构。

        Returns:
            包含字段评估OpenAI函数配置的字典
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "分析输入字段与匹配字段之间的兼容性，返回包含匹配率、描述和警告的评估。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "review": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "row_index": {"type": "integer"},
                                    "match_rate": {"type": "integer"},
                                    "match_description": {"type": "string"},
                                    "notes": {"type": "string"},
                                    "data_type_alert": {"type": "boolean"},
                                    "length_alert": {"type": "boolean"},
                                    "decimal_alert": {"type": "boolean"},
                                    "key_field_alert": {"type": "boolean"},
                                },
                                "required": [
                                    "row_index",
                                    "match_rate",
                                    "match_description",
                                ],
                            },
                        }
                    },
                    "required": ["review"],
                },
            },
        }

    @staticmethod
    def get_view_selection_tool() -> Dict[str, Any]:
        """
        获取相关CDS视图选择的OpenAI兼容函数架构。

        Returns:
            包含视图选择OpenAI函数配置的字典。
        """
        return {
            "type": "function",
            "function": {
                "name": "select_relevant_views",
                "description": "基于用户所需的接口字段和业务上下文，从列表中选择最相关的3-5个CDS视图名称。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relevant_view_names": {
                            "type": "array",
                            "description": "与用户输入最相关的CDS视图名称列表。",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["relevant_view_names"],
                },
            },
        }


class GeminiSchemas:
    @staticmethod
    def get_field_matching_tool() -> Dict[str, Any]:
        """
        获取字段匹配的Gemini兼容函数架构。

        Returns:
            包含Gemini函数配置的字典
        """
        return {
            "function_declarations": [
                {
                    "name": "review_field_matches",
                    "description": "基于语义相似性将输入字段与SAP CDS字段进行匹配",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "review": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "row_index": {"type": "integer"},
                                        "table_id": {"type": "string"},
                                        "field_id": {"type": "string"},
                                        "field_desc": {"type": "string"},
                                        "data_type": {"type": "string"},
                                        "length_total": {"type": "string"},
                                        "length_dec": {"type": "string"},
                                        "key_flag": {"type": "string"},
                                        "match_confidence": {"type": "integer"},
                                        "notes": {"type": "string"},
                                    },
                                    "required": [
                                        "row_index",
                                        "match_confidence",
                                        "notes",
                                    ],
                                },
                            }
                        },
                        "required": ["review"],
                    },
                }
            ]
        }

    @staticmethod
    def get_field_review_tool() -> Dict[str, Any]:
        return {
            "function_declarations": [
                {
                    "name": "review_field_matches",
                    "description": "分析输入字段与匹配字段之间的兼容性，返回包含匹配率、描述和警告的评估。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "review": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "row_index": {"type": "integer"},
                                        "match_rate": {"type": "integer"},
                                        "match_description": {"type": "string"},
                                        "notes": {"type": "string"},
                                        "data_type_alert": {"type": "boolean"},
                                        "length_alert": {"type": "boolean"},
                                        "decimal_alert": {"type": "boolean"},
                                        "key_field_alert": {"type": "boolean"},
                                    },
                                    "required": [
                                        "row_index",
                                        "match_rate",
                                        "match_description",
                                    ],
                                },
                            }
                        },
                        "required": ["review"],
                    },
                }
            ]
        }

    @staticmethod
    def get_view_selection_tool() -> Dict[str, Any]:
        return {
            "function_declarations": [
                {
                    "name": "select_relevant_views",
                    "description": "基于用户所需的接口字段和业务上下文，从列表中选择最相关的3-5个CDS视图名称。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relevant_view_names": {
                                "type": "array",
                                "description": "与用户输入最相关的CDS视图名称列表。",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["relevant_view_names"],
                    },
                }
            ]
        }
