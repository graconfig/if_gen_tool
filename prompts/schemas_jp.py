"""
Function schemas for different LLM providers - Japanese version.
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
                        "description": f"入力フィールドと改行区切りのTOP {match_number} SAP CDSフィールドをマッチングする、または既にマッチング結果が提供されているフィールドを分析する",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "review": {
                                        "type": "array",
                                        "description": "すべての入力フィールドのマッチング結果（手動マッチング済みのものを含む）を含むリスト",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "row_index": {
                                                    "type": "integer",
                                                    "description": "入力フィールドの行インデックス",
                                                },
                                                "table_id": {
                                                    "type": "string",
                                                    "description": f"改行区切りのTOP {match_number} SAP CDSビュー名、または手動マッチングの正確なビュー名",
                                                },
                                                "field_id": {
                                                    "type": "string",
                                                    "description": f"改行区切りのTOP {match_number} SAP CDSフィールド名、または手動マッチングの正確なフィールド名",
                                                },
                                                "field_desc": {
                                                    "type": "string",
                                                    "description": "SAP CDSフィールドの説明",
                                                },
                                                "data_type": {
                                                    "type": "string",
                                                    "description": "SAP CDSフィールドのデータ型",
                                                },
                                                "length_total": {
                                                    "type": "string",
                                                    "description": "SAP CDSフィールドの総桁数",
                                                },
                                                "length_dec": {
                                                    "type": "string",
                                                    "description": "SAP CDSフィールドの小数点以下桁数",
                                                },
                                                "key_flag": {
                                                    "type": "string",
                                                    "description": "提供されたCDSコンテキストでキーフィールドかどうか - 真の場合は'○'、それ以外は空文字列",
                                                },
                                                "obligatory": {
                                                    "type": "string",
                                                    "description": "フィールドが必須か任意か - 必須の場合は'○'、それ以外は空文字列",
                                                },
                                                "sample_value": {
                                                    "type": "string",
                                                    "description": "SAP CDSフィールドのサンプル値。提供されていない場合は可能な値を生成",
                                                },
                                                "match": {
                                                    "type": "string",
                                                    "description": "マッチング信頼度パーセンテージ（0-100）",
                                                },
                                                "notes": {
                                                    "type": "string",
                                                    "description": "マッチング選択理由の説明、または適切なマッチングが見つからなかった理由、もしくは提供されたマッチングの分析",
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
                        "description": "ユーザーの必要なインターフェースフィールドとビジネスコンテキストに基づいて、リストから最も関連性の高いCDSビュー名のトップ3-10を選択する。",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "relevant_view_names": {
                                        "type": "array",
                                        "description": "ユーザーの入力に最も関連性の高いCDSビューの名前のリスト。",
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
                "description": "提供されたコンテキストからSAP CDSフィールドと入力フィールドを厳密にマッチングする - コンテキスト外のフィールド名は一切許可されない",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "review": {
                            "type": "array",
                            "description": "すべての入力フィールドのマッチング結果を含むリスト",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "row_index": {
                                        "type": "integer",
                                        "description": "入力フィールドの行インデックス",
                                    },
                                    "table_id": {
                                        "type": "string",
                                        "description": "コンテキストリストからの正確なSAP CDSビュー名 - 完全一致する必要があり、一致が見つからない場合は空文字列",
                                    },
                                    "field_id": {
                                        "type": "string",
                                        "description": "コンテキストリストからの正確なSAP CDSフィールド名（ビュープレフィックスなし） - 完全一致する必要があり、一致が見つからない場合は空文字列",
                                    },
                                    "field_desc": {
                                        "type": "string",
                                        "description": "コンテキストからのSAP CDSフィールド説明、一致が見つからない場合は空文字列",
                                    },
                                    "data_type": {
                                        "type": "string",
                                        "description": "コンテキストからのSAP CDSフィールドデータタイプ、一致が見つからない場合は空文字列",
                                    },
                                    "length_total": {
                                        "type": "string",
                                        "description": "コンテキストからのSAP CDSフィールド総長、一致が見つからない場合は空文字列",
                                    },
                                    "length_dec": {
                                        "type": "string",
                                        "description": "コンテキストからのSAP CDSフィールド小数点以下長、一致が見つからない場合は空文字列",
                                    },
                                    "key_flag": {
                                        "type": "string",
                                        "description": "フィールドがキーフィールドかどうか - コンテキストから真の場合は'○'を使用、そうでなければ空文字列",
                                    },
                                    "obligatory": {
                                        "type": "string",
                                        "description": "フィールドが必須か任意か - コンテキストから必須の場合は'○'を使用、そうでなければ空文字列",
                                    },
                                    "sample_value": {
                                        "type": "string",
                                        "description": "SAP CDSフィールドのサンプル値",
                                    },
                                    "match": {
                                        "type": "string",
                                        "description": "マッチング信頼度パーセンテージ（0-100）",
                                    },
                                    "notes": {
                                        "type": "string",
                                        "description": "コンテキストからのマッチング選択理由の説明、または提供されたコンテキストで適切なマッチングが見つからなかった理由",
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
                "description": "ユーザーの必要なインターフェースフィールドとビジネスコンテキストに基づいて、最も関連性の高いCDSビュー名のトップ3-5を選択する。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relevant_view_names": {
                            "type": "array",
                            "description": "ユーザーの入力に最も関連性の高いCDSビューの名前のリスト。",
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
                    "description": "提供されたコンテキストからSAP CDSフィールドと入力フィールドを厳密にマッチングする - コンテキスト外のフィールド名は一切許可されない",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "review": {
                                "type": "array",
                                "description": "すべての入力フィールドのマッチング結果を含むリスト",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "row_index": {
                                            "type": "integer",
                                            "description": "入力フィールドの行インデックス",
                                        },
                                        "table_id": {
                                            "type": "string",
                                            "description": "コンテキストリストからの正確なSAP CDSビュー名 - 完全一致する必要があり、一致が見つからない場合は空文字列",
                                        },
                                        "field_id": {
                                            "type": "string",
                                            "description": "コンテキストリストからの正確なSAP CDSフィールド名（ビュープレフィックスなし） - 完全一致する必要があり、一致が見つからない場合は空文字列",
                                        },
                                        "field_desc": {
                                            "type": "string",
                                            "description": "コンテキストからのSAP CDSフィールド説明、一致が見つからない場合は空文字列",
                                        },
                                        "data_type": {
                                            "type": "string",
                                            "description": "コンテキストからのSAP CDSフィールドデータタイプ、一致が見つからない場合は空文字列",
                                        },
                                        "length_total": {
                                            "type": "string",
                                            "description": "コンテキストからのSAP CDSフィールド総長、一致が見つからない場合は空文字列",
                                        },
                                        "length_dec": {
                                            "type": "string",
                                            "description": "コンテキストからのSAP CDSフィールド小数点以下長、一致が見つからない場合は空文字列",
                                        },
                                        "key_flag": {
                                            "type": "string",
                                            "description": "フィールドがキーフィールドかどうか - コンテキストから真の場合は'○'を使用、そうでなければ空文字列",
                                        },
                                        "obligatory": {
                                            "type": "string",
                                            "description": "フィールドが必須か任意か - コンテキストから必須の場合は'○'を使用、そうでなければ空文字列",
                                        },
                                        "sample_value": {
                                            "type": "string",
                                            "description": "SAP CDSフィールドのサンプル値",
                                        },
                                        "match": {
                                            "type": "integer",
                                            "description": "マッチング信頼度パーセンテージ（0-100）",
                                        },
                                        "notes": {
                                            "type": "string",
                                            "description": "コンテキストからのマッチング選択理由の説明、または提供されたコンテキストで適切なマッチングが見つからなかった理由",
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
                    "description": "ユーザーの必要なインターフェースフィールドとビジネスコンテキストに基づいて、最も関連性の高いCDSビュー名のトップ3-10を選択する。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relevant_view_names": {
                                "type": "array",
                                "description": "ユーザーの入力に最も関連性の高いCDSビューの名前のリスト。",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["relevant_view_names"],
                    },
                }
            ]
        }
