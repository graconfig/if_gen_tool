"""
优化后的中文AI提示词模板
Optimized Chinese AI prompt templates for SAP field matching
"""

import os
from typing import Dict, List, Any

import pandas as pd


class ChinesePromptTemplates:
    """中文提示词模板集合"""

    @staticmethod
    def get_field_matching_prompt(
            input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]], TerminologyMapping_df: pd.DataFrame,
    ) -> str:
        """生成优化的字段匹配提示词"""
        match_number = os.getenv("Match_Number", "1")

        if os.getenv("VERIFY_FLAG") == "true":
            prompt_parts = [
                "您是负责智能字段映射的SAP专家。",
                "",
                "**任务：** 为以下输入字段找到最佳CDS字段匹配。提供了经过预过滤的高度相关CDS字段列表作为上下文。"
                "您的任务是根据SAP中的表或CDS或提供的上下文执行详细的字段级匹配。",
                "",
                "关键规则：",
                "• 优先在提供的上下文中匹配，如果无法从提供的上下文中匹配，可以从SAP中已有的表或CDS进行匹配",
                "• 找不到合适匹配时设置为空字符串",
                "• 考虑字段之间的业务关系，确保匹配字段在业务逻辑上保持一致",
                f"• 为每个输入字段匹配相关性最高的TOP {match_number}个SAP字段",
                "",
                "加权匹配标准（合计100%）：",
                "1.field_text语义相似性（60%，主要标准）",
                "2.业务上下文对齐（20%）",
                "3.data_type兼容性（15%）",
                "4.长度/精度对齐（5%）",
                "注：语义含义 > 技术属性；描述使用模糊匹配。",
                "",
                "待匹配的输入字段（row_index:field_name;field_desc;key_flag;data_type;field_id;length_total）：",
            ]
        else:
            prompt_parts = [
                "您是负责智能字段映射的SAP专家。",
                "",
                "**任务：** 为以下输入字段找到最佳CDS字段匹配。提供了经过预过滤的高度相关CDS字段列表作为上下文。您的任务是执行详细的字段级匹配。",
                "",
                "关键规则：",
                "• 只使用提供上下文中的确切字段名/视图名",
                "• 找不到合适匹配时设置为空字符串",
                "• 考虑字段之间的业务关系，确保匹配字段在业务逻辑上保持一致",
                f"• 为每个输入字段匹配相关性最高的TOP {match_number}个SAP字段",
                "",
                "加权匹配标准（合计100%）：",
                "1.field_text语义相似性（60%，主要标准）",
                "2.业务上下文对齐（20%）",
                "3.data_type兼容性（15%）",
                "4.长度/精度对齐（5%）",
                "注：语义含义 > 技术属性；描述使用模糊匹配。",
                "",
                "待匹配的输入字段（row_index:field_name;field_desc;key_flag;data_type;table_id;field_id;length_total）：",
            ]

        # Add input fields with enhanced details
        for field in input_fields:
            if field[1] is None:
                row_idx = getattr(field[0], "row_index")
                field_name = getattr(field[0], "field_name", "")
                field_text = getattr(field[0], "field_text", "")
                is_key = getattr(field[0], 'key_flag')
                data_type = getattr(field[0], "data_type", "")
                table_id  = getattr(field[0], "table_id", "")
                field_id  = getattr(field[0], "field_id", "")
                length_total = getattr(field[0], "length_total", "")
                remark = getattr(field[0], "remark", "")
                prompt_parts.append(
                    f"{row_idx};{field_name};{field_text};{is_key};{data_type};{table_id};{field_id};{length_total};{remark}")

        prompt_parts.append("")
        prompt_parts.append("以下字段已手动匹配，只需分析匹配结果（row_index:field_name;field_desc;key_flag;data_type;table_id;field_id;length_total;sap_table;sap_field）：")

        for field in input_fields:
            if field[1] is not None:
                row_idx = getattr(field[0], "row_index")
                field_name = getattr(field[0], "field_name", "")
                field_text = getattr(field[0], "field_text", "")
                is_key = getattr(field[0], 'key_flag')
                data_type = getattr(field[0], "data_type", "")
                table_id  = getattr(field[0], "table_id", "")
                field_id  = getattr(field[0], "field_id", "")
                length_total = getattr(field[0], "length_total", "")
                remark = getattr(field[0], "remark", "")
                sap_table = field[1].get("table_id", "")
                sap_field = field[1].get("field_id", "")
                prompt_parts.append(
                    f"{row_idx};{field_name};{field_text};{is_key};{data_type};{table_id};{field_id};{length_total};{remark};{sap_table};{sap_field}")

        prompt_parts.append("")
        prompt_parts.extend(
            [
                f"可用CDS上下文（{len(context)}个字段）：",
                "*CDSViewFormat: table_id;field_id;key_flag;field_desc;data_type;length_total;length_dec*",
                "",
            ]
        )

        # Group context by view for better organization
        compacted_context = []
        for ctx in context:
            view_name = ctx.get('view_name', '')
            field_name = ctx.get('field_name', '')
            is_key = '○' if ctx.get('is_key', False) else ''
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
                "输出要求（使用review_field_matches函数，row_index使用输入的确切行号）：",
                "为每个字段提供（确切的row_index）：",
                "• table_id: 确切的CDS视图名（如：'I_TIMESHEETRECORD'）",
                "• field_id: 仅技术字段名（如：'RECEIVERCOSTCENTER'）",
                "• field_desc: 可读描述",
                "• data_type, length_total, length_dec: 来自匹配的CDS字段",
                "• key_flag: 如果CDS字段标记为主键则为'X'，否则为空",
                "• sample_value: 样例值，如果未提供则生成一个可能的值",
                "",
                "评审备注用日语填写",
                "[一句话总结]",
                "[CDS视图选择理由]",
                "[语义相似性: X% | 技术兼容性: Y% | 整体置信度: Z%]",
                "[所需转换或直接映射]",
                "[数据类型、长度或结构问题，或'None']",
                "[开发人员需要的具体操作]",
                "[需要业务分析师澄清的问题，或'None']",
            ]
        )

        prompt_parts.extend(
            [
                "",
                "**术语映射规则：**",
                "以下是可供参考的术语映射列表。"
                "格式：sourceTerm,sourceTermAlias,sourceContext,targetTerm,targetTermAlias,sapModule,sapTransaction,sapObjectType,sapTechnicalName,category,domainArea,priority,confidence",
            ]
        )

        for _, row in TerminologyMapping_df.iterrows():
            sourceTerm = (row["SOURCETERM"], "") if row["SOURCETERM"] is not None else ""
            sourceTermAlias = (row["SOURCETERMALIAS"], "") if row["SOURCETERMALIAS"] is not None else ""
            sourceContext = row["SOURCECONTEXT"] if row["SOURCECONTEXT"] is not None else ""
            targetTerm = (row["TARGETTERM"], "") if row["TARGETTERM"] is not None else ""
            targetTermAlias = (row["TARGETTERMALIAS"], "") if row["TARGETTERMALIAS"] is not None else ""
            sapModule = (row["SAPMODULE"], "") if row["SAPMODULE"] is not None else ""
            sapTransaction = (row["SAPTRANSACTION"], "") if row["SAPTRANSACTION"] is not None else ""
            sapObjectType = (row["SAPOBJECTTYPE"], "") if row["SAPOBJECTTYPE"] is not None else ""
            sapTechnicalName = (row["SAPTECHNICALNAME"], "") if row["SAPTECHNICALNAME"] is not None else ""
            category = (row["CATEGORY"], "") if row["CATEGORY"] is not None else ""
            domainArea = (row["DOMAINAREA"], "") if row["DOMAINAREA"] is not None else ""
            priority = (row["PRIORITY"], "") if row["PRIORITY"] is not None else ""
            confidence = (row["CONFIDENCE"], "") if row["CONFIDENCE"] is not None else ""

            prompt_parts.append(
                f"{sourceTerm},{sourceTermAlias},{sourceContext},{targetTerm},{targetTermAlias},{sapModule},{sapTransaction},{sapObjectType},{sapTechnicalName},{category},{domainArea},{priority},{confidence}"
            )

        return "\n".join(prompt_parts)

    @staticmethod
    def get_view_selection_prompt(
            candidate_views_df: pd.DataFrame, TerminologyMapping_df: pd.DataFrame, input_fields: List[Dict[str, Any]]
    ) -> str:
        """
        生成提示词以指导LLM选择最相关的CDS视图。
        """
        prompt_parts = [
            "您是SAP数据建模专家。您的任务是从提供的列表中选择最适合接口的CDS视图，基于所需字段。",
            "",
            "**主要目标：** 识别并选择最可能包含接口所需数据的CDS视图。",
            "",
            "**关键指示：**",
            "1.**分析接口上下文：** 仔细查看模块、接口名称和输入字段的描述，以理解接口的业务目的。",
            "2.**评估候选视图：** 对于每个候选CDS视图，评估其描述以确定与接口目的的相关性。",
            "3.**优先考虑语义相关性：** 选择应基于语义含义和业务上下文，而不仅仅是关键词匹配。",
            "4.**仅返回名称列表：** 您的最终输出必须是选中的CDS视图名称列表。",
            "",
            "---",
            "",
            "**接口上下文：**",
        ]

        if input_fields:
            first_field = input_fields[0][0]
            module = getattr(first_field, "module", "N/A")
            if_name = getattr(first_field, "if_name", "N/A")
            if_desc = getattr(first_field, "if_desc", "N/A")

            prompt_parts.extend(
                [
                    f"-**模块：** {module}",
                    f"-**接口名称：** {if_name}",
                    f"-**接口描述：** {if_desc}",
                    "",
                    "接口所需字段：",
                    "格式：field_id,field_name,field_description",
                ]
            )

            for field in input_fields:
                field_id = getattr(field[0], "field_id", "N/A")
                field_name = getattr(field[0], "field_name", "N/A")
                field_text = getattr(field[0], "field_text", "N/A")
                prompt_parts.append(
                    f"{field_id},{field_name},{field_text}"
                )

        prompt_parts.extend(
            [
                "",
                "**候选CDS视图：**",
                "以下是候选CDS视图列表。请选择最相关的。"
                "格式：CDSViewName,CDSViewDescription",
            ]
        )

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f"{view_name},{view_desc}")

        prompt_parts.extend(
            [
                "",
                "**您的任务：**",
                "基于接口上下文和候选视图列表，请使用`select_relevant_views`函数调用，传入最合适的CDS视图名称列表。",
                "考虑接口的整体业务目的以及每个候选视图的描述与其的匹配程度。",
            ]
        )

        prompt_parts.extend(
            [
                "",
                "**术语映射规则：**",
                "以下是可供参考的术语映射列表。"
                "格式：sourceTerm,sourceTermAlias,sourceContext,targetTerm,targetTermAlias,sapModule,sapTransaction,sapObjectType,sapTechnicalName,category,domainArea,priority,confidence",
            ]
        )

        for _, row in TerminologyMapping_df.iterrows():
            sourceTerm = (row["SOURCETERM"], "") if row["SOURCETERM"] is not None else ""
            sourceTermAlias = (row["SOURCETERMALIAS"], "") if row["SOURCETERMALIAS"] is not None else ""
            sourceContext = row["SOURCECONTEXT"] if row["SOURCECONTEXT"] is not None else ""
            targetTerm = (row["TARGETTERM"], "") if row["TARGETTERM"] is not None else ""
            targetTermAlias = (row["TARGETTERMALIAS"], "") if row["TARGETTERMALIAS"] is not None else ""
            sapModule = (row["SAPMODULE"], "") if row["SAPMODULE"] is not None else ""
            sapTransaction = (row["SAPTRANSACTION"], "") if row["SAPTRANSACTION"] is not None else ""
            sapObjectType = (row["SAPOBJECTTYPE"], "") if row["SAPOBJECTTYPE"] is not None else ""
            sapTechnicalName = (row["SAPTECHNICALNAME"], "") if row["SAPTECHNICALNAME"] is not None else ""
            category = (row["CATEGORY"], "") if row["CATEGORY"] is not None else ""
            domainArea = (row["DOMAINAREA"], "") if row["DOMAINAREA"] is not None else ""
            priority = (row["PRIORITY"], "") if row["PRIORITY"] is not None else ""
            confidence = (row["CONFIDENCE"], "") if row["CONFIDENCE"] is not None else ""

            prompt_parts.append(
                f"{sourceTerm},{sourceTermAlias},{sourceContext},{targetTerm},{targetTermAlias},{sapModule},{sapTransaction},{sapObjectType},{sapTechnicalName},{category},{domainArea},{priority},{confidence}"
            )

        prompt_parts.extend(
            [
                "",
                "**您的任务：**",
                "基于接口上下文和候选视图列表，请使用`select_relevant_views`函数调用，传入最合适的CDS视图名称列表。",
                "考虑接口的整体业务目的以及每个候选视图的描述与其的匹配程度。",
            ]
        )

        return "\n".join(prompt_parts)
