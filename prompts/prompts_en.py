"""
Optimized English AI prompt templates for SAP field matching
Default language templates for the system
"""

from typing import Dict, List, Any

import pandas as pd


class EnPromptTemplates:
    """English prompt templates collection"""

    @staticmethod
    def get_field_matching_prompt(
            input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]
    ) -> str:
        """Generate optimized two-stage field matching prompt"""
        prompt_parts = [
            "You are an SAP expert for intelligent field mapping.",
            "",
            "**Task:** Find the best CDS field matches for the following input fields. A pre-filtered, highly relevant list of CDS fields is provided as context. Your task is to perform the detailed field-level matching.",
            "",
            "Critical Rules:",
            "• Use ONLY exact field/view names from provided context",
            "• Set empty strings if no suitable match found",
            "",
            "Weighted Matching Criteria (total 100%):",
            "1.field_text semantic similarity (60%, primary)",
            "2. Business context alignment (20%)",
            "3.data_type compatibility (15%)",
            "4.length/precision alignment (5%)",
            "Note: Semantic meaning > technical attributes; fuzzy match for descriptions.",
            "",
            "Input Fields to Match (row_index:field_name;field_desc;key_flag;data_type;field_id;length_total):",
        ]

        # Add input fields with enhanced details
        for field in input_fields:
            row_idx = getattr(field, "row_index")
            field_name = getattr(field, "field_name", "")
            field_text = getattr(field, "field_text", "")
            is_key = getattr(field, 'key_flag')
            data_type = getattr(field, "data_type", "")
            field_id  = getattr(field, "field_id", "")
            length_total = getattr(field, "length_total", "")
            prompt_parts.append(
                f"{row_idx};{field_name};{field_text};{is_key};{data_type};{field_id};{length_total}")

        prompt_parts.append("")
        prompt_parts.extend(
            [
                f"Available CDS Context ({len(context)} fields):",
                "*CDSViewFormat: table_id;field_id;key_flag;field_desc;data_type;length_total;length_dec*",
                "",
            ]
        )

        # Group context by view for better organization
        compacted_context = []
        for ctx in context:
            view_name = ctx.get('view_name', '')
            field_name = ctx.get('field_name', '')
            is_key = 'X' if ctx.get('is_key', False) else ''
            field_desc = ctx.get('field_desc', '')
            data_type = ctx.get('data_type', '')
            length_total = ctx.get('length_total', '')
            length_dec = ctx.get('length_dec', '')

            compacted_context.append(
                f"{view_name};{field_name};{is_key};{field_desc};{data_type};{length_total};{length_dec}"
            )
        prompt_parts.extend(compacted_context)
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("---")

        prompt_parts.extend(
            [
                "Output Requirements(Use review_field_matches function with EXACT row_index from input):",
                "For each field provide (exact row_index):",
                "• table_id: Exact CDS view name from context (e.g., 'I_TIMESHEETRECORD')",
                "• field_id: Technical field name only (e.g., 'RECEIVERCOSTCENTER')",
                "• field_desc: Human-readable description from CDS context",
                "• data_type, length_total, length_dec: From matched CDS field",
                "• key_flag: 'X' if CDS field is marked as key, empty otherwise",
                "",
                "Review notes in Japanese",
                "[A one-sentence summary]",
                "[CDS View selection reasoning]",
                "[Semantic similarity: X% | Technical compatibility: Y% | Overall confidence: Z%]",
                "[Required transformations or direct mapping]",
                "[Data type, length, or structural concerns, or 'None']",
                "[Specific developer action required]",
                "[Question for business analyst if clarification needed, or 'None']",
            ]
        )

        return "\n".join(prompt_parts)

    @staticmethod
    def get_view_selection_prompt(
            candidate_views_df: pd.DataFrame, input_fields: List[Dict[str, Any]]
    ) -> str:
        """
        Generates a prompt to instruct the LLM to select the most relevant CDS views.
        """
        prompt_parts = [
            "You are an expert SAP data modeler. Your task is to select the most relevant CDS views from a provided list that are suitable for an interface based on its required fields.",
            "",
            "**Primary Goal:** Identify and select the CDS views that are most likely to contain the data needed for the interface.",
            "",
            "**Critical Instructions:**",
            "1.**Analyze the Interface Context:** Carefully review the module, interface name, and the descriptions of the input fields to understand the business purpose of the interface.",
            "2.**Evaluate Candidate Views:** For each candidate CDS view, assess its description to determine its relevance to the interface's purpose.",
            "3.**Prioritize Semantic Relevance:** The selection should be based on the semantic meaning and business context, not just keyword matching.",
            "4.**Return Only a List of Names:** Your final output must be a list of the names of the selected CDS views.",
            "",
            "---",
            "",
            "**Interface Context:**",
        ]

        if input_fields:
            first_field = input_fields[0]
            module = getattr(first_field, "module", "N/A")
            if_name = getattr(first_field, "if_name", "N/A")
            if_desc = getattr(first_field, "if_desc", "N/A")

            prompt_parts.extend(
                [
                    f"-**Module:** {module}",
                    f"-**Interface Name:** {if_name}",
                    f"-**Interface Description:** {if_desc}",
                    "",
                    "Required Fields for the Interface:",
                    "format:field_name,field_description",
                ]
            )

            for field in input_fields:
                field_name = getattr(field, "field_name", "N/A")
                field_text = getattr(field, "field_text", "N/A")
                prompt_parts.append(
                    f"{field_name},{field_text}"
                )

        prompt_parts.extend(
            [
                "",
                "**Candidate CDS Views:**",
                "Here is a list of candidate CDS views. Please select the most relevant ones."
                "format:CDSViewName,CDSViewDescription",
            ]
        )

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f"{view_name},{view_desc}")

        prompt_parts.extend(
            [
                "",
                "**Your Task:**",
                "Based on the interface context and the list of candidate views, please call the `select_relevant_views` function with a list of the names of the most appropriate CDS views.",
                "Consider the overall business purpose of the interface and how well each candidate view's description aligns with it.",
            ]
        )

        return "\n".join(prompt_parts)
