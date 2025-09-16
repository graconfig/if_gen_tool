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
            "You are an SAP expert for intelligent field mapping with two-stage matching strategy.",
            "",
            "Task: Find best CDS field matches using two-stage approach",
            "",
            "Critical Rules:",
            "• Use ONLY exact field/view names from provided context",
            "• Set empty strings if no suitable match found",
            "• NEVER create or modify field names",
            "• If no match exists in context, leave fields empty",
            "",
            "Two-Stage Matching Strategy:",
            "**Stage 1: Smart CDS View Pre-filtering**",
            "- Analyze Module + Interface alignment for business domain relevance",
            "- Score views by semantic similarity to interface description",
            "- Prioritize views with matching business context (production, finance, etc.)",
            "- Consider view naming patterns and functional areas",
            "",
            "**Stage 2: Intelligent Field-Level Matching**",
            "- Within filtered CDS Views, apply weighted matching criteria:",
            "  • field_text semantic similarity (60% weight) - PRIMARY criterion",
            "  • Business context alignment (20% weight) - Domain relevance",
            "  • data_type compatibility (15% weight) - Technical feasibility",
            "  • length/precision alignment (5% weight) - Data structure fit",
            "- Use fuzzy matching for field descriptions to handle variations",
            "- Consider sample_value patterns for validation",
            "- Semantic understanding always overrides technical attributes",
            "",
            "Interface Context:",
        ]

        # Add interface context with emphasis
        if input_fields:
            first_field = input_fields[0]
            module = getattr(first_field, "module", "")
            if_name = getattr(first_field, "if_name", "")
            if_desc = getattr(first_field, "if_desc", "")

            prompt_parts.extend(
                [
                    "",
                    f"• Module: {module}",
                    f"• Interface: {if_name}",
                    f"• Description: {if_desc}",
                    "",
                    f"⚡ Step 1: Apply intelligent filtering - identify CDS Views semantically aligned with '{module}' module and '{if_name}' interface purpose",
                    "",
                ]
            )

        prompt_parts.append("Input Fields to Match:")

        # Add input fields with enhanced details
        for field in input_fields:
            row_idx = getattr(field, "row_index")
            field_name = getattr(field, "field_name", "")
            field_text = getattr(field, "field_text", "")
            is_key = getattr(field, 'key_flag')
            data_type = getattr(field, "data_type", "")
            length_total = getattr(field, "length_total", "")
            length_dec = getattr(field, "length_dec", "")
            sample_value = getattr(field, "sample_value", "")
            prompt_parts.append(
                f"• Row {row_idx}: field_name:{field_name}; field_desc:{field_text}; key_flag:{is_key}; data_type:{data_type}; length_total:{length_total}; length_dec:{length_dec}; sample_value:{sample_value}")

        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.extend(
            [
                f"Available CDS Context ({len(context)} fields):",
                "Step 2: Apply weighted semantic matching within filtered CDS Views - prioritize business meaning over technical attributes",
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
                f"table_id:{view_name}; field_name:{field_name}; key_flag: {is_key}; field_desc: {field_desc}; data_type:{data_type}; length_total:{length_total}; length_dec:{length_dec}"
            )
        prompt_parts.extend(compacted_context)
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("---")

        prompt_parts.extend(
            [
                "Output Requirements:",
                "Use review_field_matches function with EXACT row_index from input",
                "",
                "For each field provide:",
                "• table_id: Exact CDS view name from context (e.g., 'I_TIMESHEETRECORD')",
                "• field_id: Technical field name only (e.g., 'RECEIVERCOSTCENTER')",
                "• field_desc: Human-readable description from CDS context",
                "• data_type, length_total, length_dec: From matched CDS field",
                "• key_flag: 'X' if CDS field is marked as key, empty otherwise",
                "",
                "Output review notes in Japanese",
                "**Review:** [Fit Rate%] - [A one-sentence summary]",
                "**Analysis:** [CDS View selection reasoning - why this view fits the interface domain]",
                "**Matching:** [Semantic similarity: X% | Technical compatibility: Y% | Overall confidence: Z%]",
                "**Business Logic:** [Required transformations or direct mapping]",
                "**Technical Issues:** [Data type, length, or structural concerns, or 'None']",
                "**Implementation:** [Specific developer action required]",
                "**Business Validation:** [Question for business analyst if clarification needed, or 'None']",
                "",
                # "---Example---",
                # "**Review:** 75% - Good fit, but requires data conversion and business logic development.",
                # "**Analysis:** Selected I_TIMESHEETRECORD view - matches timesheet interface domain and production module context.",
                # "**Matching:** Semantic similarity: 85% | Technical compatibility: 70% | Overall confidence: 78%",
                # "**Business Logic:** Direct mapping with data type conversion required.",
                # "**Technical Issues:** Data type mismatch (Source: VARCHAR, Target: CHAR), Length truncation needed (50→40).",
                # "**Implementation:** Create ABAP transformation routine to convert VARCHAR to CHAR and truncate to 40 characters with padding.",
                # "**Business Validation:** Should truncated data be logged for audit purposes?",
                # "---End of Enhanced Example---",
                # "",
                "Remember: If no suitable match exists in the provided context, use empty strings for all fields.",
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
            "1.  **Analyze the Interface Context:** Carefully review the module, interface name, and the descriptions of the input fields to understand the business purpose of the interface.",
            "2.  **Evaluate Candidate Views:** For each candidate CDS view, assess its description to determine its relevance to the interface's purpose.",
            "3.  **Prioritize Semantic Relevance:** The selection should be based on the semantic meaning and business context, not just keyword matching.",
            "4.  **Return Only a List of Names:** Your final output must be a list of the names of the selected CDS views.",
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
                    f"  - **Module:** {module}",
                    f"  - **Interface Name:** {if_name}",
                    f"  - **Interface Description:** {if_desc}",
                    "",
                    "**Required Fields for the Interface:**",
                ]
            )

            for field in input_fields:
                field_name = getattr(field, "field_name", "N/A")
                field_text = getattr(field, "field_text", "N/A")
                prompt_parts.append(
                    f"  - **Field:** {field_name} | **Description:** {field_text}"
                )

        prompt_parts.extend(
            [
                "",
                "---",
                "",
                "**Candidate CDS Views:**",
                "Here is a list of candidate CDS views. Please select the most relevant ones.",
                "",
            ]
        )

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f" - **CDS View Name:** {view_name}; **CDS View Description**:{view_desc}")

        prompt_parts.extend(
            [
                "",
                "---",
                "",
                "**Your Task:**",
                "Based on the interface context and the list of candidate views, please call the `select_relevant_views` function with a list of the names of the most appropriate CDS views.",
                "Consider the overall business purpose of the interface and how well each candidate view's description aligns with it.",
            ]
        )

        return "\n".join(prompt_parts)
