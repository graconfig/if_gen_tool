"""
优化后的中文AI提示词模板
Optimized Chinese AI prompt templates for SAP field matching
"""

from typing import Dict, List, Any

import pandas as pd


class ChinesePromptTemplates:
    """中文提示词模板集合"""

    @staticmethod
    def get_field_matching_prompt(input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]) -> str:
        """生成优化的两阶段字段匹配提示词"""
        prompt_parts = [
            "您是SAP实施专家，负责智能字段映射，采用两阶段匹配策略。",
            "",
            "任务：使用两阶段方法为输入字段找到最佳CDS匹配",
            "",
            "关键约束：",
            "• 只使用提供上下文中的确切字段名/视图名",
            "• 找不到合适匹配时设置为空字符串",
            "• 绝不创建或修改字段名",
            "• 如果上下文中无匹配，保持字段为空",
            "",
            "增强型两阶段匹配策略：",
            "**阶段1：智能CDS视图预筛选**",
            "- 分析模块+接口对齐的业务域相关性",
            "- 通过与接口描述的语义相似性为视图评分",
            "- 优先选择匹配业务上下文的视图（生产、财务等）",
            "- 考虑视图命名模式和功能领域",
            "",
            "**阶段2：智能字段级匹配**",
            "- 在筛选的CDS视图内，应用加权匹配标准：",
            "  • field_text语义相似性（60%权重）- 主要标准",
            "  • 业务上下文对齐（20%权重）- 域相关性",
            "  • data_type兼容性（15%权重）- 技术可行性",
            "  • 长度/精度对齐（5%权重）- 数据结构适配",
            "- 使用模糊匹配处理字段描述变体",
            "- 考虑sample_value模式进行验证",
            "- 语义理解始终优先于技术属性",
            "",
            "接口上下文："
        ]

        # 添加接口上下文，增强显示
        if input_fields:
            first_field = input_fields[0]
            module = getattr(first_field, 'module', '')
            if_name = getattr(first_field, 'if_name', '')
            if_desc = getattr(first_field, 'if_desc', '')

            prompt_parts.extend([
                "",
                f"• 模块: {module}",
                f"• 接口: {if_name}",
                f"• 描述: {if_desc}",
                "",
                f"步骤1：应用智能筛选 - 识别与'{module}'模块和'{if_name}'接口目的语义对齐的CDS视图",
                ""
            ])

        prompt_parts.append("待匹配的输入字段：")

        # 添加输入字段，增强详细信息
        for field in input_fields:
            row_idx = getattr(field, 'row_index')
            field_name = getattr(field, 'field_name', '')
            field_text = getattr(field, 'field_text', '')
            is_key = getattr(field, 'key_flag')
            data_type = getattr(field, 'data_type', '')
            length_total = getattr(field, 'length_total', '')
            length_dec = getattr(field, 'length_dec', '')
            sample_value = getattr(field, 'sample_value', '')

            prompt_parts.append(
                f"• 行 {row_idx}: 字段名称:{field_name}; 字段描述:{field_text};  key_flag:{is_key}; 数据类型:{data_type}; 长度:{length_total}; 小数位:{length_dec}; 样例值:{sample_value}"
            )
            prompt_parts.append("")
            prompt_parts.append("---")

        prompt_parts.extend([
            f"可用CDS上下文（{len(context)}个字段）：",
            "⚡ 步骤2：在筛选的CDS视图内应用加权语义匹配 - 业务含义优先于技术属性",
            ""
        ])

        # 按视图分组上下文以便更好组织
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
                f"视图名:{view_name}; 字段名:{field_name}; 是否主键：{is_key}; 字段描述：{field_desc}; 数据类型：{data_type}; 长度：{length_total}; 小数位：{length_dec}"
            )
        prompt_parts.extend(compacted_context)
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("---")

        prompt_parts.extend([
            "输出要求：",
            "使用review_field_matches函数，row_index使用输入的确切行号",
            "",
            "为每个字段提供：",
            "• table_id: 上下文中的确切CDS视图名（如：'I_TIMESHEETRECORD'）",
            "• field_id: 仅技术字段名（如：'RECEIVERCOSTCENTER'）",
            "• field_desc: CDS上下文中的可读描述",
            "• data_type, length_total, length_dec: 来自匹配的CDS字段",
            "• key_flag: 如果CDS字段标记为主键则为'X'，否则为空",
            "",
            "notes格式（必需）：",
            "**Review:** [适配率%] - [一句话总结]",
            "**Analysis:** [CDS视图选择理由 - 此视图适配接口域的原因]",
            "**Matching:** [语义相似性: X% | 技术兼容性: Y% | 整体置信度: Z%]",
            "**Business Logic:** [所需转换或直接映射]",
            "**Technical Issues:** [数据类型、长度或结构问题，或'None']",
            "**Implementation:** [开发人员需要的具体操作]",
            "**Business Validation:** [需要业务分析师澄清的问题，或'None']",
            "",
            "---示例---",
            "**Review:** 75% - 良好适配，但需要数据转换和业务逻辑开发。",
            "**Analysis:** 选择I_TIMESHEETRECORD视图 - 匹配时间表接口域和生产模块上下文。",
            "**Matching:** 语义相似性: 85% | 技术兼容性: 70% | 整体置信度: 78%",
            "**Business Logic:** 需要数据类型转换的直接映射。",
            "**Technical Issues:** 数据类型不匹配（源：VARCHAR，目标：CHAR），需要长度截断（50→40）。",
            "**Implementation:** 创建ABAP转换例程，将VARCHAR转换为CHAR并截断到40字符并填充。",
            "**Business Validation:** 截断的数据是否应记录用于审计目的？",
            "---增强示例结束---",
            "",
            "记住：如果提供的上下文中不存在合适匹配，所有字段使用空字符串。"
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def get_view_selection_prompt(candidate_views_df: pd.DataFrame, input_fields: List[Dict[str, Any]]) -> str:
        """
        生成提示词以指导LLM选择最相关的CDS视图。
        """
        prompt_parts = [
            "您是SAP数据建模专家。您的任务是从提供的列表中选择最适合接口的CDS视图，基于所需字段。",
            "",
            "**主要目标：** 识别并选择最可能包含接口所需数据的CDS视图。",
            "",
            "**关键指示：**",
            "1.  **分析接口上下文：** 仔细查看模块、接口名称和输入字段的描述，以理解接口的业务目的。",
            "2.  **评估候选视图：** 对于每个候选CDS视图，评估其描述以确定与接口目的的相关性。",
            "3.  **优先考虑语义相关性：** 选择应基于语义含义和业务上下文，而不仅仅是关键词匹配。",
            "4.  **仅返回名称列表：** 您的最终输出必须是选中的CDS视图名称列表。",
            "",
            "---",
            "",
            "**接口上下文：**"
        ]

        if input_fields:
            first_field = input_fields[0]
            module = getattr(first_field, "module", "N/A")
            if_name = getattr(first_field, "if_name", "N/A")
            if_desc = getattr(first_field, "if_desc", "N/A")

            prompt_parts.extend([
                f"  - **模块：** {module}",
                f"  - **接口名称：** {if_name}",
                f"  - **接口描述：** {if_desc}",
                "",
                "**接口所需字段：**"
            ])

            for field in input_fields:
                field_name = getattr(field, "field_name", "N/A")
                field_text = getattr(field, "field_text", "N/A")
                prompt_parts.append(
                    f"  - **字段：** {field_name}; **描述：** {field_text}"
                )

        prompt_parts.extend([
            "",
            "---",
            "",
            "**候选CDS视图：**",
            "以下是候选CDS视图列表。请选择最相关的。",
            ""
        ])

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f"- **视图名称：** {view_name}; **描述：** {view_desc}")

        prompt_parts.extend([
            "",
            "---",
            "",
            "**您的任务：**",
            "基于接口上下文和候选视图列表，请使用`select_relevant_views`函数调用，传入最合适的CDS视图名称列表。",
            "考虑接口的整体业务目的以及每个候选视图的描述与其的匹配程度。"
        ])

        return "\n".join(prompt_parts)
