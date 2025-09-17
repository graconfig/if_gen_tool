"""
最適化された日本語AIプロンプトテンプレート
Optimized Japanese AI prompt templates for SAP field matching
"""

from typing import Dict, List, Any

import pandas as pd


class JapanesePromptTemplates:
    """日本語プロンプトテンプレート集合"""

    @staticmethod
    def get_field_matching_prompt(input_fields: List[Dict[str, Any]], context: List[Dict[str, Any]]) -> str:
        """最適化された2段階フィールドマッチングプロンプトを生成"""
        prompt_parts = [
            "あなたはSAP実装エキスパートで、2段階マッチング戦略を使用したインテリジェントフィールドマッピングを担当しています。",
            "",
            "タスク：2段階アプローチを使用して入力フィールドの最適なCDSマッチを見つける",
            "",
            "重要な制約：",
            "• 提供されたコンテキスト内の正確なフィールド名/ビュー名のみ使用",
            "• 適切なマッチが見つからない場合は空文字列を設定",
            "• フィールド名の作成や変更は絶対禁止",
            "• コンテキストにマッチが存在しない場合、フィールドを空のままにする",
            "",
            "強化された2段階マッチング戦略：",
            "**段階1：スマートCDSビュー事前フィルタリング**",
            "- モジュール+インターフェース整合をビジネスドメイン関連性で分析",
            "- インターフェース説明とのセマンティック類似性でビューをスコア化",
            "- ビジネスコンテキスト（生産、財務など）に一致するビューを優先",
            "- ビュー命名パターンと機能領域を考慮",
            "",
            "**段階2：インテリジェントフィールドレベルマッチング**",
            "- フィルタされたCDSビュー内で、重み付けマッチング基準を適用：",
            "  • field_textセマンティック類似性（60%重み）- 主要基準",
            "  • ビジネスコンテキスト整合（20%重み）- ドメイン関連性",
            "  • data_type互換性（15%重み）- 技術的実現可能性",
            "  • 長さ/精度整合（5%重み）- データ構造適合",
            "- フィールド説明のバリエーション処理にファジーマッチングを使用",
            "- 検証のためsample_valueパターンを考慮",
            "- セマンティック理解が常に技術属性を上回る",
            "",
            "インターフェースコンテキスト："
        ]

        # インターフェースコンテキストを強調して追加
        if input_fields:
            first_field = input_fields[0]

            module = getattr(first_field, 'module', '')
            if_name = getattr(first_field, 'if_name', '')
            if_desc = getattr(first_field, 'if_desc', '')

            prompt_parts.extend([
                "",
                f"• モジュール: {module}",
                f"• インターフェース: {if_name}",
                f"• 説明: {if_desc}",
                "",
                f"ステップ1：インテリジェントフィルタリング適用 - '{module}'モジュールと'{if_name}'インターフェース目的にセマンティックに整合するCDSビューを特定",
                ""
            ])

        prompt_parts.append("マッチング対象の入力フィールド：")

        # 詳細情報を強化して入力フィールドを追加
        for field in input_fields:
            row_idx = getattr(field, 'row_index')
            field_name = getattr(field, 'field_name')
            field_text = getattr(field, 'field_text')
            is_key    = getattr(field, 'key_flag')
            data_type = getattr(field, 'data_type', '')
            length_total = getattr(field, 'length_total', '')
            length_dec = getattr(field, 'length_dec', '')
            sample_value = getattr(field, 'sample_value', '')
            prompt_parts.append(
                # f"• 行/Row {row_idx}: 項目名/field_name:{field_name}; 必須/任意/key_flag:{is_key}; 項目説明/field_desc:{field_text}; データ型/data_type:{data_type}; 桁数(全体)/length_total:{length_total}; 桁数(小数点以下)/length_dec:{length_dec}; サンプル値(表示形式込み)/sample_value:{sample_value}"
                f"• Row {row_idx}: field_name:{field_name}; field_desc:{field_text}; key_flag:{is_key}; data_type:{data_type}; length_total:{length_total}; length_dec:{length_dec}; sample_value:{sample_value}")
        prompt_parts.append("")
        prompt_parts.append("---")

        prompt_parts.extend([
            f"利用可能なCDSコンテキスト（{len(context)}フィールド）：",
            "⚡ ステップ2：フィルタされたCDSビュー内で重み付けセマンティックマッチング適用 - 技術属性よりビジネス意味を優先",
            ""
        ])

        # より良い組織化のためにビューごとにコンテキストをグループ化
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
                # f"テーブルID/table_id:{view_name}; 項目名/field_name:{field_name}; 必須/任意/key_flag:{is_key}; 項目説明/field_desc:{field_desc}; データ型/data_type:{data_type}; 桁数(全体)/length_total:{length_total}; 桁数(小数点以下)/length_dec:{length_dec}"
                f"table_id:{view_name}; field_name:{field_name}; key_flag: {is_key}; field_desc: {field_desc}; data_type:{data_type}; length_total:{length_total}; length_dec:{length_dec}")
        prompt_parts.extend(compacted_context)
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("---")

        prompt_parts.extend([
            "出力要件：",
            "review_field_matches関数を使用、入力からの正確なrow_indexを使用",
            "",
            "各フィールドに対して提供：",
            "• table_id: コンテキストからの正確なCDSビュー名（例：'I_TIMESHEETRECORD'）",
            "• field_id: 技術フィールド名のみ（例：'RECEIVERCOSTCENTER'）",
            "• field_desc: CDSコンテキストからの人間が読める説明",
            "• data_type, length_total/桁数(全体), length_dec/桁数(小数点以下): マッチしたCDSフィールドから",
            "• key_flag: CDSフィールドがキーとしてマークされている場合は'X'、そうでなければ空",
            # "• table_id/テーブルID: コンテキストからの正確なCDSビュー名（例：'I_TIMESHEETRECORD'）",
            # "• field_id/項目ID: 技術フィールド名のみ（例：'RECEIVERCOSTCENTER'）",
            # "• field_desc/項目名: CDSコンテキストからの人間が読める説明",
            # "• data_type/データ型, length_total/桁数(全体), length_dec/桁数(小数点以下): マッチしたCDSフィールドから",
            # "• key_flag/必須/任意: CDSフィールドがキーとしてマークされている場合は'X'、そうでなければ空",
            "",
            "notesフォーマット（必須）：",
            "**Review:** [適合率%] - [一文要約]",
            "**Analysis:** [CDSビュー選択理由 - このビューがインターフェースドメインに適合する理由]",
            "**Matching:** [セマンティック類似性: X% | 技術互換性: Y% | 全体信頼度: Z%]",
            "**Business Logic:** [必要な変換または直接マッピング]",
            "**Technical Issues:** [データ型、長さ、構造的懸念、または'None']",
            "**Implementation:** [開発者に必要な具体的アクション]",
            "**Business Validation:** [明確化が必要な場合のビジネスアナリストへの質問、または'None']",
            "",
            "---例---",
            "**Review:** 75% - 良好な適合、ただしデータ変換とビジネスロジック開発が必要。",
            "**Analysis:** I_TIMESHEETRECORDビューを選択 - タイムシートインターフェースドメインと生産モジュールコンテキストに一致。",
            "**Matching:** セマンティック類似性: 85% | 技術互換性: 70% | 全体信頼度: 78%",
            "**Business Logic:** データ型変換が必要な直接マッピング。",
            "**Technical Issues:** データ型不一致（ソース：VARCHAR、ターゲット：CHAR）、長さ切り詰めが必要（50→40）。",
            "**Implementation:** VARCHARをCHARに変換し、40文字に切り詰めてパディングするABAP変換ルーチンを作成。",
            "**Business Validation:** 切り詰められたデータは監査目的でログに記録すべきか？",
            "---強化例終了---",
            "",
            "記住：提供されたコンテキストに適切なマッチが存在しない場合、すべてのフィールドに空文字列を使用してください。"
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def get_view_selection_prompt(candidate_views_df: pd.DataFrame, input_fields: List[Dict[str, Any]]) -> str:
        """
        最も関連性の高いCDSビューを選択するようLLMに指示するプロンプトを生成します。
        """
        prompt_parts = [
            "あなたはSAPデータモデリングのエキスパートです。提供されたリストから、必要なフィールドに基づいてインターフェースに適したCDSビューを選択してください。",
            "",
            "**主要目標：** インターフェースに必要なデータを含む可能性が最も高いCDSビューを特定し選択する。",
            "",
            "**重要な指示：**",
            "1.  **インターフェースコンテキストの分析：** モジュール、インターフェース名、入力フィールドの説明を慎重に確認し、インターフェースのビジネス目的を理解してください。",
            "2.  **候補ビューの評価：** 各候補CDSビューについて、その説明を評価してインターフェースの目的との関連性を判断してください。",
            "3.  **セマンティック関連性の優先：** 選択は単純なキーワードマッチングではなく、セマンティックな意味とビジネスコンテキストに基づくべきです。",
            "4.  **名前のリストのみを返す：** 最終的な出力は、選択されたCDSビューの名前のリストでなければなりません。",
            "",
            "---",
            "",
            "**インターフェースコンテキスト：**"
        ]

        if input_fields:
            first_field = input_fields[0]
            module = getattr(first_field, "module", "N/A")
            if_name = getattr(first_field, "if_name", "N/A")
            if_desc = getattr(first_field, "if_desc", "N/A")

            prompt_parts.extend([
                f"  - **モジュール：** {module}",
                f"  - **インターフェース名：** {if_name}",
                f"  - **インターフェース説明：** {if_desc}",
                "",
                "**インターフェースに必要なフィールド：**"
            ])

            for field in input_fields:
                field_name = getattr(field, "field_name", "N/A")
                field_text = getattr(field, "field_text", "N/A")
                prompt_parts.append(
                    f"  - **フィールド：** {field_name} | **説明：** {field_text}"
                )

        prompt_parts.extend([
            "",
            "---",
            "",
            "**候補CDSビュー：**",
            "以下は候補CDSビューのリストです。最も関連性の高いものを選択してください。",
            "フォーマット：CDS ビュー名,CDS ビュー説明"
            ""
        ])

        for _, row in candidate_views_df.iterrows():
            view_name = row["VIEWNAME"]
            view_desc = row["VIEWDESC"]
            prompt_parts.append(f"{view_name},{view_desc}")

        prompt_parts.extend([
            "",
            "---",
            "",
            "**あなたのタスク：**",
            "インターフェースコンテキストと候補ビューのリストに基づいて、最も適切なCDSビューの名前のリストを`select_relevant_views`関数で呼び出してください。",
            "インターフェースの全体的なビジネス目的と、各候補ビューの説明がそれにどの程度適合するかを考慮してください。"
        ])

        return "\n".join(prompt_parts)
