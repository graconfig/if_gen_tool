"""
最適化された日本語AIプロンプトテンプレート
Optimized Japanese AI prompt templates for SAP field matching
"""

import os
from typing import Dict, List, Any

import pandas as pd


class JapanesePromptTemplates:
    """日本語プロンプトテンプレート集合"""

    @staticmethod
    def get_field_matching_prompt(
            input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]], TerminologyMapping_df: pd.DataFrame,
    ) -> str:
        """最適化されたフィールドマッチングプロンプトを生成"""
        match_number = os.getenv("Match_Number", "1")

        if os.getenv("VERIFY_FLAG") == "true":
            prompt_parts = [
                "あなたはインテリジェントフィールドマッピングを担当するSAPエキスパートです。",
                "",
                "**タスク：** 以下の入力フィールドに最適なCDSフィールドマッチを見つけてください。事前にフィルタリングされた高度に関連性の高いCDSフィールドのリストがコンテキストとして提供されています。"
                "あなたのタスクは、SAPのテーブルまたはCDSに基づいて詳細なフィールドレベルのマッチングを行うことです。",
                "",
                "重要なルール：",
                "• 提供されたコンテキストを優先的にマッチング。提供されたコンテキストからマッチできない場合は、SAP既存のテーブルまたはCDSからマッチ可能",
                "• 適切なマッチが見つからない場合は空文字列を設定",
                "• フィールド間のビジネス関係を考慮し、マッチしたフィールドがビジネスロジック上一貫していることを確認",
                f"• 各入力フィールドに対して最も相関の高いSAPフィールドのTOP {match_number}をマッチ",
                "",
                "重み付きマッチング基準（合計100%）：",
                "1.field_textセマンティック類似性（60%、主要基準）",
                "2.ビジネスコンテキスト整合（20%）",
                "3.data_type互換性（15%）",
                "4.長さ/精度整合（5%）",
                "注：セマンティックな意味 > 技術属性；説明についてはファジーマッチを使用。",
                "",
                "マッチング対象の入力フィールド（row_index:field_name;field_desc;key_flag;data_type;field_id;length_total）：",
            ]
        else:
            prompt_parts = [
                "あなたはインテリジェントフィールドマッピングを担当するSAPエキスパートです。",
                "",
                "**タスク：** 以下の入力フィールドに最適なCDSフィールドマッチを見つけてください。事前にフィルタリングされた高度に関連性の高いCDSフィールドのリストがコンテキストとして提供されています。あなたのタスクは詳細なフィールドレベルのマッチングを行うことです。",
                "",
                "重要なルール：",
                "• 提供されたコンテキストの正確なフィールド名/ビュー名のみ使用",
                "• 適切なマッチが見つからない場合は空文字列を設定",
                "• フィールド間のビジネス関係を考慮し、マッチしたフィールドがビジネスロジック上一貫していることを確認",
                f"• 各入力フィールドに対して最も相関の高いSAPフィールドのTOP {match_number}をマッチ",
                "",
                "重み付きマッチング基準（合計100%）：",
                "1.field_textセマンティック類似性（60%、主要基準）",
                "2.ビジネスコンテキスト整合（20%）",
                "3.data_type互換性（15%）",
                "4.長さ/精度整合（5%）",
                "注：セマンティックな意味 > 技術属性；説明についてはファジーマッチを使用。",
                "",
                "マッチング対象の入力フィールド（row_index:field_name;field_desc;key_flag;data_type;table_id;field_id;length_total）：",
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
        prompt_parts.append("以下のフィールドは手動でマッチング済みです。マッチング結果の分析のみが必要です（row_index:field_name;field_desc;key_flag;data_type;table_id;field_id;length_total;sap_table;sap_field）：")

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
                f"利用可能なCDSコンテキスト（{len(context)}フィールド）：",
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
                "出力要件（入力の正確なrow_indexを使用してreview_field_matches関数を使用）：",
                "各フィールドに対して提供（正確なrow_index）：",
                "• table_id: 正確なCDSビュー名（例：'I_TIMESHEETRECORD'）",
                "• field_id: 技術フィールド名のみ（例：'RECEIVERCOSTCENTER'）",
                "• field_desc: 人間が読める説明",
                "• data_type, length_total, length_dec: マッチしたCDSフィールドから",
                "• key_flag: CDSフィールドがキーとしてマークされている場合は'X'、そうでなければ空",
                "• sample_value: サンプル値。提供されていない場合は可能な値を生成",
                "",
                "レビューノートは日本語で",
                "[一文要約]",
                "[CDSビュー選択の理由]",
                "[セマンティック類似性: X% | 技術互換性: Y% | 全体信頼度: Z%]",
                "[必要な変換または直接マッピング]",
                "[データ型、長さ、構造的懸念、または'None']",
                "[開発者に必要な具体的アクション]",
                "[明確化が必要な場合のビジネスアナリストへの質問、または'None']",
            ]
        )

        prompt_parts.extend(
            [
                "",
                "**用語マッピングルール：**",
                "参考にできる用語マッピングリストを以下に示します。"
                "フォーマット：sourceTerm,sourceTermAlias,sourceContext,targetTerm,targetTermAlias,sapModule,sapTransaction,sapObjectType,sapTechnicalName,category,domainArea,priority,confidence",
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
        最も関連性の高いCDSビューを選択するようLLMに指示するプロンプトを生成します。
        """
        prompt_parts = [
            "あなたはSAPデータモデリングのエキスパートです。提供されたリストから、必要なフィールドに基づいてインターフェースに適したCDSビューを選択してください。",
            "",
            "**主要目標：** インターフェースに必要なデータを含む可能性が最も高いCDSビューを特定し選択する。",
            "",
            "**重要な指示：**",
            "1.**インターフェースコンテキストの分析：** モジュール、インターフェース名、入力フィールドの説明を慎重に確認し、インターフェースのビジネス目的を理解してください。",
            "2.**候補ビューの評価：** 各候補CDSビューについて、その説明を評価してインターフェースの目的との関連性を判断してください。",
            "3.**セマンティック関連性の優先：** 選択は単純なキーワードマッチングではなく、セマンティックな意味とビジネスコンテキストに基づくべきです。",
            "4.**名前のリストのみを返す：** 最終的な出力は、選択されたCDSビューの名前のリストでなければなりません。",
            "",
            "---",
            "",
            "**インターフェースコンテキスト：**",
        ]

        if input_fields:
            first_field = input_fields[0][0]
            module = getattr(first_field, "module", "N/A")
            if_name = getattr(first_field, "if_name", "N/A")
            if_desc = getattr(first_field, "if_desc", "N/A")

            prompt_parts.extend(
                [
                    f"-**モジュール：** {module}",
                    f"-**インターフェース名：** {if_name}",
                    f"-**インターフェース説明：** {if_desc}",
                    "",
                    "インターフェースに必要なフィールド：",
                    "フォーマット：field_id,field_name,field_description",
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
                "**候補CDSビュー：**",
                "以下は候補CDSビューのリストです。最も関連性の高いものを選択してください。"
                "フォーマット：CDSビュー名,CDSビュー説明",
            ]
        )

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f"{view_name},{view_desc}")

        prompt_parts.extend(
            [
                "",
                "**あなたのタスク：**",
                "インターフェースコンテキストと候補ビューのリストに基づいて、最も適切なCDSビューの名前のリストを`select_relevant_views`関数で呼び出してください。",
                "インターフェースの全体的なビジネス目的と、各候補ビューの説明がそれにどの程度適合するかを考慮してください。",
            ]
        )

        prompt_parts.extend(
            [
                "",
                "**用語マッピングルール：**",
                "参考にできる用語マッピングリストを以下に示します。"
                "フォーマット：sourceTerm,sourceTermAlias,sourceContext,targetTerm,targetTermAlias,sapModule,sapTransaction,sapObjectType,sapTechnicalName,category,domainArea,priority,confidence",
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
                "**あなたのタスク：**",
                "インターフェースコンテキストと候補ビューのリストに基づいて、最も適切なCDSビューの名前のリストを`select_relevant_views`関数で呼び出してください。",
                "インターフェースの全体的なビジネス目的と、各候補ビューの説明がそれにどの程度適合するかを考慮してください。",
            ]
        )

        return "\n".join(prompt_parts)
