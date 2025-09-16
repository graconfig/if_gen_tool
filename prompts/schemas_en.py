"""
Function schemas for different LLM providers - English version.
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
                        "description": "Matches input fields with SAP CDS fields STRICTLY from the provided context - NO field names outside the context are allowed",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "review": {
                                        "type": "array",
                                        "description": "A list containing the matching results for all input fields",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "row_index": {
                                                    "type": "integer",
                                                    "description": "Row index of the input field",
                                                },
                                                "table_id": {
                                                    "type": "string",
                                                    "description": "EXACT SAP CDS view name from context list - must match exactly, empty string if no match found",
                                                },
                                                "field_id": {
                                                    "type": "string",
                                                    "description": "EXACT SAP CDS field name from context list (without view prefix) - must match exactly, empty string if no match found",
                                                },
                                                "field_desc": {
                                                    "type": "string",
                                                    "description": "SAP CDS field description from context, empty string if no match found",
                                                },
                                                "data_type": {
                                                    "type": "string",
                                                    "description": "SAP CDS field data type from context, empty string if no match found",
                                                },
                                                "length_total": {
                                                    "type": "string",
                                                    "description": "SAP CDS field total length from context, empty string if no match found",
                                                },
                                                "length_dec": {
                                                    "type": "string",
                                                    "description": "SAP CDS field decimal length from context, empty string if no match found",
                                                },
                                                "key_flag": {
                                                    "type": "string",
                                                    "description": "Whether the field is a key field - use 'X' if true from context, empty string otherwise",
                                                },
                                                "match_confidence": {
                                                    "type": "integer",
                                                    "description": "Match confidence percentage (0-100)",
                                                },
                                                "notes": {
                                                    "type": "string",
                                                    "description": "Notes explaining the match choice from context OR why no suitable match was found in the provided context",
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
                        "description": "Selects the top 3-5 most relevant CDS view names from a list based on the user's required interface fields and business context.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "relevant_view_names": {
                                        "type": "array",
                                        "description": "A list of the names of the CDS views that are most relevant to the user's input.",
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
        Get OpenAI-compatible function schema for field matching.

        Returns:
            Dictionary containing OpenAI function configuration
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "Match input fields with SAP CDS fields based on semantic similarity",
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
        Get OpenAI-compatible function schema for field review.

        Returns:
            Dictionary containing OpenAI function configuration for field review
        """
        return {
            "type": "function",
            "function": {
                "name": "review_field_matches",
                "description": "Analyzes the compatibility between input and matched fields, returning a review with match rate, description, and alerts.",
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
        Get OpenAI-compatible function schema for selecting relevant CDS views.

        Returns:
            Dictionary containing OpenAI function configuration for view selection.
        """
        return {
            "type": "function",
            "function": {
                "name": "select_relevant_views",
                "description": "Selects the top 3-5 most relevant CDS view names from a list based on the user's required interface fields and business context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relevant_view_names": {
                            "type": "array",
                            "description": "A list of the names of the CDS views that are most relevant to the user's input.",
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
        Get Gemini-compatible function schema for field matching.

        Returns:
            Dictionary containing Gemini function configuration
        """
        return {
            "function_declarations": [
                {
                    "name": "review_field_matches",
                    "description": "Match input fields with SAP CDS fields based on semantic similarity",
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
                    "description": "Analyzes the compatibility between input and matched fields, returning a review with match rate, description, and alerts.",
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
                    "description": "Selects the top 3-5 most relevant CDS view names from a list based on the user's required interface fields and business context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relevant_view_names": {
                                "type": "array",
                                "description": "A list of the names of the CDS views that are most relevant to the user's input.",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["relevant_view_names"],
                    },
                }
            ]
        }
