import json
import os
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv
from hana_ml import ConnectionContext
from hdbcli.dbapi import Error as HanaDbError

from core.i18n import _, get_current_language
import re

load_dotenv()


class HANADBClient:
    def __init__(self):
        self.scenario_table = "AI_ORCHESTRATION_RAG_BUSINESSSCENARIOS"
        self.cds_view_table = "AI_ORCHESTRATION_RAG_CDSVIEWS"
        self.view_fields_table = "AI_ORCHESTRATION_RAG_VIEWFIELDS"

        self.db_addr = os.getenv("HANA_ADDRESS")
        self.db_user = os.getenv("HANA_USER")
        self.db_pwd = os.getenv("HANA_PASSWORD")
        self._db_schema = os.getenv("HANA_SCHEMA")

        self.hana_client: ConnectionContext = None

    def connect(self) -> None:
        if self.hana_client:
            return

        try:
            self.hana_client = ConnectionContext(
                address=self.db_addr,
                port="443",  # 443 is usual
                user=self.db_user,
                password=self.db_pwd,
                encrypt=True,
            )
        except HanaDbError as e:
            print(_("HANA Cloud connection failed: {}").format(e))
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.hana_client:
            self.hana_client.close()
            print(_("Database connection closed."))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _format_in_clause(self, items: List[str]) -> str:
        if not items:
            return "('')"
        formatted_items = [f"'{str(item).replace("'", "''")}'" for item in items]
        return f"({', '.join(formatted_items)})"

    def run_vector_search(
            self,
            query: str,
            metric="COSINE_SIMILARITY",
            k=3,
    ) -> pd.DataFrame:
        if not self.hana_client:
            raise ConnectionError(_("HANA Cloud not connected."))

        sort = "ASC" if metric == "L2DISTANCE" else "DESC"

        sql = """SELECT TOP {k}"ID","SCENARIO","DESCRIPTION","VIEWCATEGORY"
        FROM "{schema}"."{table}"
        ORDER BY {metric}(VECTOR_EMBEDDING('{query}', 'QUERY', 'SAP_NEB.20240715'),"EMBEDDINGS") {sort}""".format(
            k=k,
            metric=metric,
            query=query,
            sort=sort,
            table=self.scenario_table,
            schema=self._db_schema,
        )
        try:
            hdf = self.hana_client.sql(sql)
            df_context = hdf.head(k).collect()
            return df_context
        except HanaDbError as e:
            print(_("SQL execution failed: {}").format(e))
            return pd.DataFrame()

    def get_views(self, category: str) -> pd.DataFrame:
        if not self.hana_client:
            raise ConnectionError(_("Database not connected."))

        categories = [cat for cat in category.split("/") if cat]
        if not categories:
            return pd.DataFrame()

        category_sql = self._format_in_clause(categories)

        sql = """
             SELECT "VIEWNAME", "VIEWDESC"
            FROM "{schema}"."{table}"
            WHERE "VIEWCATEGORY" IN {categories} 
            AND "ISACTIVE" = 'true'
        """.format(
            schema=self._db_schema, table=self.cds_view_table, categories=category_sql
        )
        try:
            return self.hana_client.sql(sql).collect()
        except HanaDbError as e:
            print(_("SQL error occurred while getting views: {}").format(e))
            return pd.DataFrame()

    def get_filter_fields(
            self,
            cds_views: List[str],
            query: str,
            language: str = None,
            top_k: int = 50,
            threshold: float = 0.2,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not self.hana_client:
            raise ConnectionError(_("Database not connected."))

        if language is None:
            language = get_current_language()
        db_language = language

        cds_views_sql = self._format_in_clause(cds_views)
        sql = """
            SELECT "TABLENAME","TABLEDESC","CONTENT"
            FROM "{schema}"."{table}"
            WHERE "TABLENAME" IN {cds_views}
            AND "LANGU" = '{language}'
        """.format(
            schema=self._db_schema,
            table=self.view_fields_table,
            cds_views=cds_views_sql,
            language=db_language,
        )

        try:
            fields_df = self.hana_client.sql(sql).collect()
            filtered_fields_by_view = {view: [] for view in cds_views}
            original_count = 0
            filtered_count = 0

            # Clean query text once for reuse
            fields_embed_query = query.replace("'", "''").replace('"', '""')

            if not fields_df.empty:
                print(_("Applying fields filtering..."))
                for idx, row in fields_df.iterrows():
                    view_name = row["TABLENAME"]
                    content_str = row["CONTENT"]

                    if not content_str or not isinstance(content_str, str):
                        continue

                    try:
                        parsed_fields = json.loads(content_str)
                        view_fields_with_scores = []

                        # --- OPTIMIZED LOGIC: Parse, filter, and score in a single loop ---
                        for field_data in parsed_fields:
                            original_count += 1
                            if not isinstance(field_data, list) or len(field_data) < 7:
                                continue

                            field_name = str(field_data[0])
                            field_desc = str(field_data[2])

                            # Combine field name and description for embedding
                            field_text = f"{field_name} {field_desc}".strip()
                            if not field_text:
                                continue

                            field_text = field_text.replace("'", "''").replace('"', '""')

                            # Calculate similarity for the current field
                            similarity_sql = f"""
                            SELECT COSINE_SIMILARITY(
                                VECTOR_EMBEDDING('{query}', 'QUERY', 'SAP_NEB.20240715'),
                                VECTOR_EMBEDDING('{field_text}', 'DOCUMENT', 'SAP_NEB.20240715')
                            ) as SIMILARITY
                            FROM DUMMY
                            """.format(query=fields_embed_query,field_text=field_text)

                            similarity_score = 0.0
                            try:
                                result = self.hana_client.sql(similarity_sql).collect()
                                if not result.empty:
                                    similarity_score = float(result.iloc[0]["SIMILARITY"])
                            except Exception:
                                # Assign low similarity on error
                                similarity_score = 0.0

                            # Only keep fields that meet the threshold
                            if similarity_score >= threshold:
                                field_dict = {
                                    "field_name": field_data[0],
                                    "is_key": field_data[1],
                                    "field_desc": field_data[2],
                                    "data_element": field_data[3],
                                    "data_type": field_data[4],
                                    "length_total": field_data[5],
                                    "length_dec": field_data[6],
                                    "similarity_score": similarity_score,  # Store score for sorting
                                }
                                view_fields_with_scores.append(field_dict)

                        # After checking all fields, sort by similarity and take top_k
                        view_fields_with_scores.sort(key=lambda x: x["similarity_score"], reverse=True)
                        top_fields = view_fields_with_scores[:top_k]
                        filtered_fields_by_view[view_name] = top_fields
                        filtered_count += len(top_fields)

                    except json.JSONDecodeError:
                        print(
                            _(
                                "⚠️ Warning: Could not parse CONTENT JSON for view {}"
                            ).format(view_name)
                        )
                        continue

            reduction_percentage = (
                ((original_count - filtered_count) / original_count * 100)
                if original_count > 0
                else 0
            )
            print(
                _(
                    "After filtering: {} fields selected from {} total fields ({:.1f}% reduction)"
                ).format(filtered_count, original_count, reduction_percentage)
            )

            return filtered_fields_by_view

        except HanaDbError as e:
            print(f"SQL error in get_fields: {e}")
            return {view: [] for view in cds_views}

    def get_fields(self, cds_views: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        if not self.hana_client:
            raise ConnectionError("数据库未连接。")

        cds_views_sql = self._format_in_clause(cds_views)

        sql = """
            SELECT "TABLENAME","TABLEDESC","CONTENT"
            FROM "{schema}"."{table}"
            WHERE "TABLENAME" IN {cds_views}
            AND "LANGU" = 'ja'
        """.format(
            schema=self._db_schema,
            table=self.view_fields_table,
            cds_views=cds_views_sql,
        )
        try:
            fields_df = self.hana_client.sql(sql).collect()
            # 初始化结果字典
            results = {view: [] for view in cds_views}
            if not fields_df.empty:
                for _, row in fields_df.iterrows():
                    view_name = row["TABLENAME"]
                    content_str = row["CONTENT"]

                    if not content_str or not isinstance(content_str, str):
                        continue

                    try:
                        # 2. 解析字段
                        content_str_re = self.parse_fields(content_str)
                        parsed_fields = json.loads(content_str_re)

                        # 3. 将解析后的列表转换为结构化的字典列表
                        for field_data in parsed_fields:
                            if not isinstance(field_data, list) or len(field_data) < 7:
                                continue  # Skip malformed entries

                            field_dict = {
                                "field_name": field_data[0],
                                "is_key": field_data[1],
                                "field_desc": field_data[2],
                                "data_element": field_data[3],  # Can be added if needed
                                "data_type": field_data[4],
                                "length_total": field_data[5],
                                "length_dec": field_data[6],
                            }
                            results[view_name].append(field_dict)
                    except json.JSONDecodeError as e:
                        print(
                            f"⚠️ Warning: Could not parse CONTENT JSON for view {view_name} error: {e}"
                        )
                        continue
                    except Exception as e:
                        print(f"Error parse fields:{e}")
            return results
        except HanaDbError as e:
            print(f"{e}")
            return []

    @staticmethod
    def parse_fields(content_str: str) -> str:
        result_chars = []
        in_string = False
        i = 0
        s_len = len(content_str)

        while i < s_len:
            char = content_str[i]

            if char == '"':
                if not in_string:
                    # 字符串开头
                    in_string = True
                    result_chars.append(char)
                else:
                    # 字符串内部遇到了一个引号。
                    # 查找下一个非空白字符
                    next_char_index = i + 1
                    while next_char_index < s_len and content_str[next_char_index].isspace():
                        next_char_index += 1

                    # 如果字符串后面就是逗号、方括号或字符串结尾，
                    # 那么这个引号是合法的结束符。
                    if next_char_index == s_len or content_str[next_char_index] in [',', ']', '}']:
                        in_string = False
                        result_chars.append(char)
                    else:
                        # 否则，这绝对是一个需要转义的内部引号。
                        result_chars.append('\\"')
            else:
                # 对于所有其他字符，直接添加
                result_chars.append(char)

            i += 1

        repaired_string = "".join(result_chars)

        return repaired_string

if __name__ == "__main__":
    query_text = "purchase"
    try:
        with HANADBClient() as db:
            print(
                _("--- Step 1: Executing vector search for query '{}' ---").format(
                    query_text
                )
            )
            vector_search_results = db.run_vector_search(query=query_text, k=1)

            print(_("\nVector search results:"))
            print(vector_search_results)
            print("-" * 50)

            if not vector_search_results.empty:
                category_string = vector_search_results.iloc[0]["VIEWCATEGORY"]
                print(
                    _(
                        "\n--- Step 2: Getting all related CDS views using category string '{}' ---"
                    ).format(category_string)
                )

                views_in_category = db.get_views(category=category_string)

                if not views_in_category.empty:
                    print(_("\nFound {} CDS views:").format(len(views_in_category)))
                    print("-" * 50)

            else:
                print(_("\nVector search returned no results."))
    except Exception as e:
        print(_("\nProgram execution failed: {}").format(e))