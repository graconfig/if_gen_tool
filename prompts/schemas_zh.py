"""
Function schemas for different LLM providers - Chinese version.
Defines the structure for AI function calling capabilities.
"""

import os
from typing import Dict, Any


class ClaudeSchemas:
    @staticmethod
    def get_field_matching_tool() -> Dict[str, Any]:

        match_number = os.getenv("Match_Number", "1")

        return {
            "tools": [
                {
                    "toolSpec": {
                        "name": "review_field_matches",
                        "description": f"将输入字段与换行符分隔的TOP {match_number}个SAP CDS字段进行匹配，或分析已提供匹配结果的字段",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "review": {
                                        "type": "array",
                                        "description": "包含所有输入字段匹配结果（包括手动匹配的字段）的列表",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "row_index": {
                                                    "type": "integer",
                                                    "description": "输入字段的行索引",
                                                },
                                                "table_id": {
                                                    "type": "string",
                                                    "description": f"换行符分隔的TOP {match_number}个SAP CDS视图名，或手动匹配的精确视图名",
                                                },
                                                "field_id": {
                                                    "type": "string",
                                                    "description": f"换行符分隔的TOP {match_number}个SAP CDS字段名，或手动匹配的精确字段名",
                                                },
                                                "field_desc": {
                                                    "type": "string",
                                                    "description": "SAP CDS字段描述",
                                                },
                                                "data_type": {
                                                    "type": "string",
                                                    "description": "SAP CDS字段数据类型",
                                                },
                                                "length_total": {
                                                    "type": "string",
                                                    "description": "SAP CDS字段总长度",
                                                },
                                                "length_dec": {
                                                    "type": "string",
                                                    "description": "SAP CDS字段小数位长度",
                                                },
                                                "key_flag": {
                                                    "type": "string",
                                                    "description": "在提供的CDS上下文中该字段是否为键字段 - 为真时使用'○'，否则为空字符串",
                                                },
                                                "obligatory": {
                                                    "type": "string",
                                                    "description": "字段是否必填或可选 - 必填时使用'○'，否则为空字符串",
                                                },
                                                "sample_value": {
                                                    "type": "string",
                                                    "description": "SAP CDS字段的样例值，如果未提供则生成一个可能的值",
                                                },
                                                "match": {
                                                    "type": "string",
                                                    "description": "匹配置信度百分比（0-100）",
                                                },
                                                "notes": {
                                                    "type": "string",
                                                    "description": "说明匹配选择理由，或未找到合适匹配的原因，或对已提供匹配结果的分析",
                                                },
                                            },
                                            "required": ["row_index", "table_id", "field_id", "field_desc", "data_type", "length_total", "length_dec", "key_flag", "obligatory", "sample_value", "match", "notes"]
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
                        "description": "基于用户所需的接口字段和业务上下文，从列表中选择最相关的3-10个CDS视图名称。",
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
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "从提供的上下文中将输入字段与SAP CDS字段进行严格匹配 - 不允许使用上下文之外的字段名",
                "parameters": {
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
                                        "description": "该字段是否为键字段 - 如果来自上下文为真则使用'○'，否则为空字符串",
                                    },
                                    "obligatory": {
                                        "type": "string",
                                        "description": "字段是否必填或可选 - 来自上下文必填时使用'○'，否则为空字符串",
                                    },
                                    "sample_value": {
                                        "type": "string",
                                        "description": "SAP CDS字段的样例值",
                                    },
                                    "match": {
                                        "type": "string",
                                        "description": "匹配置信度百分比（0-100）",
                                    },
                                    "notes": {
                                        "type": "string",
                                        "description": "说明从上下文中选择匹配的理由，或在提供的上下文中为何没有找到合适匹配的原因",
                                    },
                                },
                                "required": ["row_index", "table_id", "field_id", "field_desc", "data_type",
                                             "length_total", "length_dec", "key_flag", "obligatory", "sample_value",
                                             "match", "notes"]
                            },
                        }
                    },
                    "required": ["review"],
                },
            },
        }

    @staticmethod
    def get_view_selection_tool() -> Dict[str, Any]:
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
        return {
            "function_declarations": [
                {
                    "name": "review_field_matches",
                    "description": "从提供的上下文中将输入字段与SAP CDS字段进行严格匹配 - 不允许使用上下文之外的字段名",
                    "parameters": {
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
                                            "description": "该字段是否为键字段 - 如果来自上下文为真则使用'○'，否则为空字符串",
                                        },
                                        "obligatory": {
                                            "type": "string",
                                            "description": "字段是否必填或可选 - 来自上下文必填时使用'○'，否则为空字符串",
                                        },
                                        "sample_value": {
                                            "type": "string",
                                            "description": "SAP CDS字段的样例值",
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
                                    "required": ["row_index", "table_id", "field_id", "field_desc",
                                                 "data_type", "length_total", "length_dec", "key_flag",
                                                 "obligatory", "sample_value", "match", "notes"]
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
