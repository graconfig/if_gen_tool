import json
import os
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv
from hana_ml import ConnectionContext
from hdbcli.dbapi import Error as HanaDbError

from utils.i18n import _, get_current_language
from utils.sap_logger import logger
from collections import defaultdict


load_dotenv()


class HANADBClient:
    def __init__(self):
        self.scenario_table = "PWC_HAND_AI2REPORT_DEV_BUSINESSSCENARIOS"
        self.cds_view_table = "PWC_HAND_AI2REPORT_DEV_CDSVIEWS"
        self.view_fields_table = "PWC_HAND_AI2REPORT_DEV_VIEWFIELDS"
        self.cust_fields_table = "PWC_HAND_AI2REPORT_DEV_CUSTFIELDS"

        self.db_addr = os.getenv("HANA_ADDRESS")
        self.db_user = os.getenv("HANA_USER")
        self.db_pwd = os.getenv("HANA_PASSWORD")
        self._db_schema = os.getenv("HANA_SCHEMA")
        self._db_schema_cust = os.getenv("HANA_SCHEMA_CUST")

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
            logger.error(_("HANA Cloud connection failed: {}").format(e))
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.hana_client:
            self.hana_client.close()
            logger.info(_("Database connection closed."))

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
        log_filename: str = None,
    ) -> pd.DataFrame:
        if not self.hana_client:
            error_msg = _("HANA Cloud not connected.")
            logger.error(error_msg, log_filename)
            raise ConnectionError(error_msg)

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
            logger.error(_("SQL execution failed: {}").format(e), log_filename)
            return pd.DataFrame()

    def get_views(self, category: str, log_filename: str = None) -> pd.DataFrame:
        if not self.hana_client:
            error_msg = _("Database not connected.")
            logger.error(error_msg, log_filename)
            raise ConnectionError(error_msg)

        categories = [cat for cat in category.split("/") if cat]
        if not categories:
            logger.warning(_("No valid categories provided"), log_filename)
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
            result = self.hana_client.sql(sql).collect()
            return result
        except HanaDbError as e:
            logger.error(
                _("SQL error occurred while getting views: {}").format(e), log_filename
            )
            return pd.DataFrame()

    def get_fields(
        self, cds_views: List[str], log_filename: str = None
    ) -> Dict[str, List[Dict[str, Any]]]:
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
                        # 直接找到[[的位置
                        start_idx = content_str_re.find('[[')
                        end_idx = content_str_re.rfind(']]')

                        if start_idx != -1 and end_idx != -1:
                             # 提取完整的内容（包含[[和]]）
                            full_content = content_str_re[start_idx:end_idx+2]
                            
                        parsed_fields = json.loads(full_content)
                        
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
                        logger.warning(
                            _(
                                "⚠️ Warning: Could not parse CONTENT JSON for view {} error: {}"
                            ).format(view_name, e),
                            log_filename,
                        )
                        continue
                    except Exception as e:
                        logger.error(_("Error parse fields:{}").format(e), log_filename)
            return results
        except HanaDbError as e:
            logger.error(_("Error: {}").format(e), log_filename)
            return {}

    def get_custom_fields(
        self, 
        field_query: str,
        metric="COSINE_SIMILARITY",
        log_filename: str = None
    ) -> Dict[str, Any]:
        """
        对单个字段进行客户化字段表的向量检索（基于 SOURCEDESC 字段）
        
        Args:
            field_query: 字段查询文本（字段名+描述+示例值）
            metric: 相似度算法
            log_filename: 日志文件名
            
        Returns:
            匹配结果字典，如果未匹配返回空字典
        """
        sort = "ASC" if metric == "L2DISTANCE" else "DESC"

        # 清理查询文本
        clean_query = field_query.replace("'", "''").replace('"', '""')

        sql = """
            SELECT TOP 1
                "TARGETTABLE",
                "TARGETFIELD",
                "TARGETDESC",
                "TARGETTYPE",
                "TARGETLENGTH",
                "TARGETDECIMALS",
                "KEYFLAG",
                "OBLIGATORY",
                "ALLOWEDVALUES",
                "NOTES",
                SIMILARITY_SCORE
            FROM (
                SELECT
                    "TARGETTABLE",
                    "TARGETFIELD",
                    "TARGETDESC",
                    "TARGETTYPE",
                    "TARGETLENGTH",
                    "TARGETDECIMALS",
                    "KEYFLAG",
                    "OBLIGATORY",
                    "ALLOWEDVALUES",
                    "NOTES",
                    {metric}(VECTOR_EMBEDDING('{query}', 'QUERY', 'SAP_NEB.20240715'),"EMBEDDINGS") AS SIMILARITY_SCORE
                FROM "{schema}"."{table}"
                WHERE "ISACTIVE"=0
            ) AS SubqueryAlias
            WHERE SIMILARITY_SCORE {comparison_operator} {threshold}
            ORDER BY SIMILARITY_SCORE {sort}
        """.format(
            metric=metric,
            query=clean_query,
            sort=sort,
            schema=self._db_schema_cust,
            table=self.cust_fields_table,
            comparison_operator='>' if sort.strip().upper() == 'DESC' else '<',
            threshold=0.7  # 示例阈值，您需要根据实际情况调整
        )

        try:
            result_df = self.hana_client.sql(sql).collect()
            
            if result_df.empty:
                return {}
            
            row = result_df.iloc[0]
            return {
                "table_name":   row["TARGETTABLE"],
                "field_id":     row["TARGETFIELD"],
                "field_name":   row["TARGETDESC"],
                "data_type":    row["TARGETTYPE"],
                "length_total": row["TARGETLENGTH"],
                "length_dec":   row["TARGETDECIMALS"],
                "is_key":       row["KEYFLAG"],
                "obligatory":   row["OBLIGATORY"],
                "sample_value": row["ALLOWEDVALUES"],
                "notes":        row["NOTES"]
            }
            
        except HanaDbError as e:
            logger.error(
                _("Custom field vector search failed: {}").format(e), 
                log_filename
            )
            return {}

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
                    while (
                        next_char_index < s_len
                        and content_str[next_char_index].isspace()
                    ):
                        next_char_index += 1

                    # 如果字符串后面就是逗号、方括号或字符串结尾，
                    # 那么这个引号是合法的结束符。
                    if next_char_index == s_len or content_str[next_char_index] in [
                        ",",
                        "]",
                        "}",
                    ]:
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
        db = HANADBClient()
        db.connect()
        
        logger.info(
            _("--- Step 1: Executing vector search for query '{}' ---").format(
                query_text
            )
        )
        vector_search_results = db.run_vector_search(query=query_text, k=1)

        logger.info(_("\nVector search results:"))
        logger.info(str(vector_search_results))
        logger.info("-" * 80)

        if not vector_search_results.empty:
            category_string = vector_search_results.iloc[0]["VIEWCATEGORY"]
            logger.info(
                _(
                    "\n--- Step 2: Getting all related CDS views using category string '{}' ---"
                ).format(category_string)
            )

            views_in_category = db.get_views(category=category_string)

            if not views_in_category.empty:
                logger.info(
                    _("\nFound {} CDS views:").format(len(views_in_category))
                )
                logger.info("-" * 80)

        else:
            logger.info(_("\nVector search returned no results."))
    except Exception as e:
        logger.error(_("\nProgram execution failed: {}").format(e))
