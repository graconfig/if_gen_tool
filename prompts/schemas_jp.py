"""
Function schemas for different LLM providers - Japanese version.
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
                        "description": "提供されたコンテキストからSAP CDSフィールドと入力フィールドを厳密にマッチングする - コンテキスト外のフィールド名は一切許可されない",
                        "inputSchema": {
                            "json": {
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
                                                    "description": "フィールドがキーフィールドかどうか - コンテキストから真の場合は'X'を使用、そうでなければ空文字列",
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
                                            "required": ["row_index","table_id","field_id","field_desc","data_type","length_total","length_dec","key_flag","match_confidence", "notes"]
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
                        "description": "ユーザーの必要なインターフェースフィールドとビジネスコンテキストに基づいて、最も関連性の高いCDSビュー名のトップ3-5を選択する。",
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
        """
        フィールドマッチング用のOpenAI互換関数スキーマを取得します。

        Returns:
            OpenAI関数設定を含む辞書
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "セマンティック類似性に基づいて入力フィールドをSAP CDSフィールドとマッチングする",
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
        フィールドレビュー用のOpenAI互換関数スキーマを取得します。

        Returns:
            フィールドレビュー用のOpenAI関数設定を含む辞書
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "入力フィールドとマッチングされたフィールド間の互換性を分析し、マッチング率、説明、アラートを含むレビューを返す。",
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
        関連CDSビュー選択用のOpenAI互換関数スキーマを取得します。

        Returns:
            ビュー選択用のOpenAI関数設定を含む辞書。
        """
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
        """
        フィールドマッチング用のGemini互換関数スキーマを取得します。

        Returns:
            Gemini関数設定を含む辞書
        """
        return {
            "function_declarations": [
                {
                    "name": "review_field_matches",
                    "description": "セマンティック類似性に基づいて入力フィールドをSAP CDSフィールドとマッチングする",
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
                    "description": "入力フィールドとマッチングされたフィールド間の互換性を分析し、マッチング率、説明、アラートを含むレビューを返す。",
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
                }
            ]
        }
