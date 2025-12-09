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
                        "description": "Matches input fields with TOP 3 SAP CDS fields, separated by line breaks",
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
                                                    "description": "TOP 3 SAP CDS view name, separated by line breaks",
                                                },
                                                "field_id": {
                                                    "type": "string",
                                                    "description": "TOP 3 SAP CDS field names, separated by line breaks",
                                                },
                                                "field_desc": {
                                                    "type": "string",
                                                    "description": "SAP CDS field description",
                                                },
                                                "data_type": {
                                                    "type": "string",
                                                    "description": "SAP CDS field data type",
                                                },
                                                "length_total": {
                                                    "type": "string",
                                                    "description": "SAP CDS field total length",
                                                },
                                                "length_dec": {
                                                    "type": "string",
                                                    "description": "SAP CDS field decimal length",
                                                },
                                                "key_flag": {
                                                    "type": "string",
                                                    "description": "Whether the field is a key field - use '○' if true, empty string otherwise",
                                                },
                                                "obligatory": {
                                                    "type": "string",
                                                    "description": "Whether the field is required or optional - use '○' if required, empty string otherwise",
                                                },
                                                "sample_value": {
                                                    "type": "string",
                                                    "description": "Sample value for SAP CDS field, if not provided, generate a possible value",
                                                },
                                                "match": {
                                                    "type": "integer",
                                                    "description": "Match confidence percentage (0-100)",
                                                },
                                                "notes": {
                                                    "type": "string",
                                                    "description": "Notes explaining the match choice OR why no suitable match was found",
                                                },
                                            },
                                            "required": ["row_index","table_id","field_id","field_desc","data_type","length_total","length_dec","key_flag","obligatory","sample_value","match", "notes"]
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
                        "description": "Selects the top 3-10 most relevant CDS view names from a list based on the user's required interface fields and business context.",
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
                "description": "Matches input fields with SAP CDS fields STRICTLY from the provided context - NO field names outside the context are allowed",
                "parameters": {
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
                                        "description": "Whether the field is a key field - use '○' if true from context, empty string otherwise",
                                    },
                                    "obligatory": {
                                        "type": "string",
                                        "description": "Whether the field is required or optional from context - use '○' if required from context, empty string otherwise",
                                    },
                                    "sample_value": {
                                        "type": "string",
                                        "description": "Sample value for SAP CDS field",
                                    },
                                    "match": {
                                        "type": "integer",
                                        "description": "Match confidence percentage (0-100)",
                                    },
                                    "notes": {
                                        "type": "string",
                                        "description": "Notes explaining the match choice from context OR why no suitable match was found in the provided context",
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
                    "description": "Matches input fields with SAP CDS fields STRICTLY from the provided context - NO field names outside the context are allowed",
                    "parameters": {
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
                                            "description": "Whether the field is a key field - use '○' if true from context, empty string otherwise",
                                        },
                                        "obligatory": {
                                            "type": "string",
                                            "description": "Whether the field is required or optional from context - use '○' if required from context, empty string otherwise",
                                        },
                                        "sample_value": {
                                            "type": "string",
                                            "description": "Sample value for SAP CDS field",
                                        },
                                        "match": {
                                            "type": "integer",
                                            "description": "Match confidence percentage (0-100)",
                                        },
                                        "notes": {
                                            "type": "string",
                                            "description": "Notes explaining the match choice from context OR why no suitable match was found in the provided context",
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
