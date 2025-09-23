import shutil
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from tqdm import tqdm

import openpyxl
import pandas as pd

from core.config import AppSettings
from utils.i18n import _
from utils.sap_logger import logger
from hana.hana_conn import HANADBClient
from models.data_models import InterfaceField
from services.aicore_base_service import AIServiceBase
from utils.exceptions import FileProcessingError
from utils.tools import parse_notes, clean_field_id, normalize_key_flag


# Suppress the specific DrawingML warning by matching the message text
warnings.filterwarnings(
    "ignore",
    message="DrawingML support is incomplete and limited to charts and images only. Shapes and drawings will be lost.",
    category=UserWarning,
)


class ExcelProcessor:
    """Process Excel files for SAP interface field mapping.

    This class handles the extraction of interface definitions from Excel files,
    queries relevant CDS views from HANA, and uses AI services to match fields.
    """

    def __init__(
        self, data_dir: Path, ai_service: AIServiceBase, settings: AppSettings
    ):
        """Initialize the Excel processor.

        Args:
            data_dir: Path to the data directory
            ai_service: AI service instance for field matching
            settings: The application settings object
        """
        self.data_dir = data_dir
        self.ai_service = ai_service
        self.settings = settings

        # 配置直接从settings对象获取
        self.excel_config = settings.excel
        self.column_mappings = settings.columns
        self.batch_size = self.excel_config.batch_size
        self.max_concurrent_batches = self.excel_config.max_concurrent_batches

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception, FileProcessingError)),
        reraise=True,
    )
    def process_file(self, file_path: Path) -> None:
        """Process an Excel file for field mapping.

        Args:
            file_path: Path to the Excel file to process

        Raises:
            FileProcessingError: If file processing fails
            FileNotFoundError: If the input file is not found
        """
        if not file_path.exists():
            error_msg = _("❌ Input file not found: {}").format(file_path)
            raise FileNotFoundError(error_msg)

        from core.consts import Directories

        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = file_path.stem
        file_suffix = file_path.suffix

        # 输出文件名
        output_filename = f"processed_{current_date}_{file_stem}{file_suffix}"
        output_path = self.data_dir / Directories.EXCEL_OUTPUT / output_filename

        if output_path.exists():
            output_path.unlink()

        try:
            workbook = openpyxl.load_workbook(file_path)
        except Exception as e:
            error_msg = _("Failed to load workbook: {}").format(e)
            raise FileProcessingError(error_msg) from e

        sheet_name = self.excel_config.sheet_name
        if sheet_name not in workbook.sheetnames:
            error_msg = _("Sheet '{}' not found in workbook").format(sheet_name)
            raise ValueError(error_msg)

        self._process_worksheet(workbook, sheet_name, file_path.name)

        try:
            workbook.save(output_path)
        except Exception as e:
            error_msg = _("Failed to save processed file: {}").format(e)
            raise FileProcessingError(error_msg) from e

        logger.info(
            _("Processed file saved: {} ✅").format(output_filename),
            logger.get_excel_log_filename(file_path.name),
        )

        # Archive the source file after successful processing
        if self._archive_processed_file(file_path):
            logger.info(
                _("Successful file moved to archive folder."),
                logger.get_excel_log_filename(file_path.name),
            )
        else:
            logger.warning(
                _(
                    "⚠️ Warning: Could not archive source file, but processing completed successfully."
                ),
                logger.get_excel_log_filename(file_path.name),
            )

    def _process_worksheet(
        self, workbook: openpyxl.Workbook, sheet_name: str, excel_filename: str
    ) -> None:
        """Process a worksheet within the workbook.

        Args:
            workbook: OpenPyXL workbook instance
            sheet_name: Name of the sheet to process
            excel_filename: Name of the Excel file for logging
        """
        worksheet = workbook[sheet_name]

        # 提取输入列的字段
        input_fields = self.extract_fields(worksheet)

        # 分批处理
        if len(input_fields) <= self.batch_size:
            self._process_single(worksheet, input_fields, excel_filename)
        else:
            self._process_in_batches(worksheet, input_fields, excel_filename)

    def _get_cds_context(
        self, input_fields: List[InterfaceField], excel_filename: str
    ) -> List[Dict[str, Any]]:
        """Get CDS context for field matching.

        Args:
            input_fields: List of input fields
            excel_filename: Name of the Excel file for logging

        Returns:
            List of field context dictionaries
        """
        if not input_fields:
            return []

        module = input_fields[0].module
        if_name = input_fields[0].if_name
        if_desc = input_fields[0].if_desc
        module_query = ",".join([module, if_name, if_desc])

        with HANADBClient() as hana_client:
            log_filename = logger.get_excel_log_filename(excel_filename)

            # Get CDS views
            cat_find_by_module = hana_client.run_vector_search(
                query=module_query, k=3, log_filename=log_filename
            )
            if cat_find_by_module.empty:
                logger.warning(
                    _("No categories for module."),
                    logger.get_excel_log_filename(excel_filename),
                )
                return []

            category_string = cat_find_by_module.iloc[0]["VIEWCATEGORY"]
            views_find_by_cat = hana_client.get_views(
                category=category_string, log_filename=log_filename
            )
            if views_find_by_cat.empty:
                logger.warning(
                    _("No views for category."),
                    logger.get_excel_log_filename(excel_filename),
                )
                return []

            logger.info(
                _("Found {} candidate CDS views").format(len(views_find_by_cat)),
                logger.get_excel_log_filename(excel_filename),
            )

            # Select relevant views using LLM
            llm_return_views = self._select_relevant_views(
                views_find_by_cat, input_fields, excel_filename
            )
            if not llm_return_views:
                logger.warning(
                    _("No views found by LLM."),
                    logger.get_excel_log_filename(excel_filename),
                )
                return []

            logger.info(
                _("LLM selected {} CDS views.").format(len(llm_return_views)),
                logger.get_excel_log_filename(excel_filename),
            )

            # Get fields from selected views
            llm_return_views_fields = hana_client.get_fields(
                cds_views=llm_return_views, log_filename=log_filename
            )

            #Get Custom views fields
            # custom_views_fields = hana_client.get_custom_fields(log_filename=log_filename)

            #Merge fields
            # llm_return_views_fields.extend(custom_views_fields)

            llm_return_views_df = views_find_by_cat[
                views_find_by_cat["VIEWNAME"].isin(llm_return_views)
            ]

            # 获取custom视图对应的DataFrame
            # custom_views_df = views_find_by_cat[
            #     views_find_by_cat["VIEWNAME"].isin(custom_views_fields)
            # ]
            #
            # llm_return_views_df = pd.concat([llm_return_views_df, custom_views_df],ignore_index=True)

            final_context_for_llm = self._prepare_llm_context(
                llm_return_views_fields, llm_return_views_df
            )

            return final_context_for_llm

    def _process_single(
        self, worksheet, input_fields: List[InterfaceField], excel_filename: str
    ) -> None:
        """Process a single batch of fields.

        Args:
            worksheet: OpenPyXL worksheet instance
            input_fields: List of input fields to process
            excel_filename: Name of the Excel file for logging
        """
        # Get CDS context
        final_context_for_llm = self._get_cds_context(input_fields, excel_filename)
        if not final_context_for_llm:
            error_msg = _("No CDS context available - unable to process this file.")
            logger.error(
                error_msg,
                logger.get_excel_log_filename(excel_filename),
            )
            raise FileProcessingError(error_msg)

        # Process fields
        try:
            batch_results = self._match_fields(
                input_fields, final_context_for_llm, excel_filename
            )
        except Exception as e:
            error_msg = f"❌ LLM function call failed: {e}"
            logger.error(
                error_msg,
                logger.get_excel_log_filename(excel_filename),
            )
            raise FileProcessingError(
                _("Failed to process file due to LLM error: {}").format(str(e))
            ) from e

        # Combine input fields with results
        final_results = list(zip(input_fields, batch_results))

        logger.info(
            "-" *80,
            logger.get_excel_log_filename(excel_filename),
        )

        # Write results
        logger.info(
            _("Writing results to file..."),
            logger.get_excel_log_filename(excel_filename),
        )
        self.write_results(worksheet, final_results)

    def _process_in_batches(
        self, worksheet, input_fields: List[InterfaceField], excel_filename: str
    ) -> None:
        """Process fields in batches for large files.

        Args:
            worksheet: OpenPyXL worksheet instance
            input_fields: List of input fields to process
            excel_filename: Name of the Excel file for logging
        """
        logger.info(
            _("Processing {} rows in batches of {}").format(
                len(input_fields), self.batch_size
            ),
            logger.get_excel_log_filename(excel_filename),
        )

        # Get common context for all batches
        final_context_for_llm = self._get_cds_context(input_fields, excel_filename)
        if not final_context_for_llm:
            error_msg = _(
                "Processing failed: No relevant CDS context found for this interface."
            )
            raise FileProcessingError(error_msg)

        # Process fields in batches (with parallel processing)
        all_results = []

        # Split input fields into batches
        batches = []
        for i in range(0, len(input_fields), self.batch_size):
            batch_fields = input_fields[i : i + self.batch_size]
            batches.append((i, batch_fields))

        # Process batches with progress bar
        logger.info(
            _("Processing {} batches...").format(len(batches)),
            logger.get_excel_log_filename(excel_filename),
        )
        with tqdm(
            total=len(batches),
            desc=_("Processing batches"),
            unit="batch",
            ncols=100,
            leave=False,
        ) as pbar:
            # Process batches in parallel
            with ThreadPoolExecutor(
                max_workers=self.max_concurrent_batches
            ) as executor:
                # Submit all batches for processing
                future_to_batch = {
                    executor.submit(
                        self._process_batch,
                        batch_fields,
                        final_context_for_llm,
                        excel_filename,
                        i,
                    ): (i, len(batch_fields))
                    for i, batch_fields in batches
                }

                # Collect results as they complete
                completed_batches = 0
                for future in as_completed(future_to_batch):
                    batch_index, batch_size = future_to_batch[future]
                    batch_start = batch_index + 1
                    batch_end = batch_index + batch_size

                    try:
                        batch_results = future.result()
                        # Combine input fields with results for this batch
                        batch_fields = input_fields[
                            batch_index : batch_index + batch_size
                        ]
                        batch_final_results = list(zip(batch_fields, batch_results))
                        all_results.extend(batch_final_results)

                        logger.info(
                            _("Row {}-{} processed successfully").format(
                                batch_start, batch_end
                            ),
                            logger.get_excel_log_filename(excel_filename),
                        )
                    except Exception as e:
                        error_msg = _("Failed to process row {}-{}: {}").format(
                            batch_start, batch_end, str(e)
                        )
                        logger.error(
                            error_msg,
                            logger.get_excel_log_filename(excel_filename),
                        )
                        # Continue with other batches even if one fails

                    # Update progress
                    completed_batches += 1
                    pbar.set_postfix_str(
                        _("Completed: {}/{}").format(completed_batches, len(batches))
                    )
                    pbar.update(1)
                    # Add newline to separate progress bar from logger output
                    print()  # Add newline after progress update

        # Sort results by row index to maintain order
        all_results.sort(key=lambda x: x[0].row_index)

        logger.info(
            "-" *80,
            logger.get_excel_log_filename(excel_filename),
        )

        # Write all results
        logger.info(
            _("Writing {} results to file...").format(len(all_results)),
            logger.get_excel_log_filename(excel_filename),
        )
        self.write_results(worksheet, all_results)

    def _process_batch(
        self,
        batch_fields: List[InterfaceField],
        context: List[Dict[str, Any]],
        excel_filename: str,
        batch_index: int,
    ) -> List[Dict[str, Any]]:
        """Process a single batch of fields.

        Args:
            batch_fields: List of fields in this batch
            context: Context information for field matching
            excel_filename: Name of the Excel file for logging
            batch_index: Index of this batch

        Returns:
            List of matching results for the batch
        """
        try:
            results = self._match_fields(batch_fields, context, excel_filename)

            return results
        except Exception as e:
            error_msg = _("Error in row {}: {}").format(batch_index, str(e))
            logger.error(
                error_msg,
                logger.get_excel_log_filename(excel_filename),
            )
            # Return empty results for failed batch
            return [{} for _ in batch_fields]

    def extract_fields(self, worksheet) -> List[InterfaceField]:
        """Extract interface fields from the worksheet.

        Args:
            worksheet: OpenPyXL worksheet instance

        Returns:
            List of InterfaceField objects
        """
        input_fields = []

        header_row = self.excel_config.header_row
        input_header_cols = self.column_mappings.input_header_cols

        # 抬头module、接口信息
        module = worksheet[f"{input_header_cols['module']}{header_row}"].value or ""
        if_name = worksheet[f"{input_header_cols['if_name']}{header_row}"].value or ""
        if_desc = worksheet[f"{input_header_cols['if_desc']}{header_row}"].value or ""

        start_row = self.excel_config.start_row
        input_row_cols = self.column_mappings.input_row_cols

        for row in range(start_row, (worksheet.max_row or 1000) + 1):
            field_name = worksheet[f"{input_row_cols['field_name']}{row}"].value

            if not field_name or str(field_name).strip() == "":
                continue

            interface_field = InterfaceField(
                module=module,
                if_name=if_name,
                if_desc=if_desc,
                field_name=str(field_name).strip(),
                key_flag=worksheet[f"{input_row_cols['key_flag']}{row}"].value or "",
                obligatory=worksheet[f"{input_row_cols['obligatory']}{row}"].value
                or "",
                data_type=worksheet[f"{input_row_cols['data_type']}{row}"].value or "",
                field_id=worksheet[f"{input_row_cols['field_id']}{row}"].value or "",
                length_total=worksheet[f"{input_row_cols['length_total']}{row}"].value
                or "",
                length_dec=worksheet[f"{input_row_cols['length_dec']}{row}"].value
                or "",
                field_text=worksheet[f"{input_row_cols['field_text']}{row}"].value
                or "",
                sample_value=worksheet[f"{input_row_cols['sample_value']}{row}"].value
                or "",
                row_index=row,
            )

            input_fields.append(interface_field)

        return input_fields

    def _select_relevant_views(
        self,
        candidate_views_df: pd.DataFrame,
        input_fields: List[InterfaceField],
        excel_filename: str,
    ) -> List[str]:
        """Select relevant CDS views using AI service.

        Args:
            candidate_views_df: DataFrame with candidate views
            input_fields: List of input fields
            excel_filename: Name of the Excel file for logging

        Returns:
            List of selected view names
        """
        views_prompt = self.ai_service.get_view_selection_prompt(
            candidate_views_df, input_fields
        )

        views_function_schema = self.ai_service.get_view_selection_schema()

        try:
            views_response = self.ai_service.call_with_function(
                views_prompt, views_function_schema
            )

            if views_response:
                return views_response.get("relevant_view_names", [])
            else:
                return []
        except Exception as e:
            logger.debug(
                f"select relevant views failed:{e}",
                logger.get_excel_log_filename(excel_filename),
            )
            return []

    def _prepare_llm_context(
        self,
        all_fields_dict: Dict[str, List[Dict[str, Any]]],
        relevant_views_df: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        """Prepare context for LLM field matching.

        Args:
            all_fields_dict: Dictionary of fields by view
            relevant_views_df: DataFrame with relevant views

        Returns:
            List of field context dictionaries
        """
        context_list = []
        view_desc_map = pd.Series(
            relevant_views_df.VIEWDESC.values, index=relevant_views_df.VIEWNAME
        ).to_dict()

        for view_name, fields in all_fields_dict.items():
            view_desc = view_desc_map.get(view_name, "")  # Safely get description
            for field_detail in fields:
                context_list.append(
                    {
                        "view_name": view_name,
                        "view_desc": view_desc,
                        "field_name": field_detail.get("field_name", ""),
                        "field_desc": field_detail.get("field_desc", ""),
                        "is_key": field_detail.get("is_key", False),
                        "data_type": field_detail.get("data_type", ""),
                        "length_total": str(field_detail.get("length_total", "")),
                        "length_dec": str(field_detail.get("length_dec", "")),
                    }
                )
        return context_list

    def write_results(
        self, worksheet, results: List[Tuple[InterfaceField, Dict[str, Any]]]
    ) -> None:
        """Write matching results to the worksheet.

        Args:
            worksheet: OpenPyXL worksheet instance
            results: List of tuples containing input fields and matching results
        """
        output_columns = self.column_mappings.output_columns

        processed_count = 0
        for interface_field, match_result in results:
            row = interface_field.row_index

            try:
                worksheet[f"{output_columns['field_name']}{row}"] = match_result.get(
                    "field_name", ""
                )  # Field description
                worksheet[f"{output_columns['field_id']}{row}"] = match_result.get(
                    "field_id", ""
                )  # Technical field name
                worksheet[f"{output_columns['key_flag']}{row}"] = match_result.get(
                    "key_flag", ""
                )
                worksheet[f"{output_columns['obligatory']}{row}"] = match_result.get(
                    "obligatory", ""
                )
                worksheet[f"{output_columns['table_id']}{row}"] = match_result.get(
                    "table_id", ""
                )
                worksheet[f"{output_columns['data_type']}{row}"] = match_result.get(
                    "data_type", ""
                )
                worksheet[f"{output_columns['length_total']}{row}"] = match_result.get(
                    "length_total", ""
                )
                worksheet[f"{output_columns['length_dec']}{row}"] = match_result.get(
                    "length_dec", ""
                )
                worksheet[f"{output_columns['match']}{row}"] = match_result.get(
                    "match", ""
                )
                worksheet[f"{output_columns['notes']}{row}"] = match_result.get(
                    "notes", ""
                )
                worksheet[f"{output_columns['sample_value']}{row}"] = match_result.get(
                    "sample_value", ""
                )

                processed_count += 1

            except Exception as e:
                continue

    # ========== Field Matching Logic ==========

    def _match_fields(
        self,
        input_fields: List,
        context: Optional[List[Dict[str, Any]]] = None,
        excel_filename: str = None,
    ) -> List[Dict[str, Any]]:
        """Field matching using AI services with HANA context.

        Args:
            input_fields: List of input fields to match
            context: Context information for matching
            excel_filename: Name of the Excel file for logging

        Returns:
            List of matching results
        """
        if not input_fields:
            return []

        if context is None:
            return []

        return self._match_fields_with_context(input_fields, context, excel_filename)

    def _match_fields_with_context(
        self,
        input_fields: List,
        context: List[Dict[str, Any]],
        excel_filename: str = None,
    ) -> List[Dict[str, Any]]:
        """Match fields with context using AI service.

        Args:
            input_fields: List of input fields to match
            context: Context information for matching
            excel_filename: Name of the Excel file for logging

        Returns:
            List of matching results
        """
        all_fields_context = self._extract_fields_from_context(context)

        resulsts_prompt = self.ai_service.get_rag_matching_prompt(
            input_fields, all_fields_context
        )

        results_function_schema = self.ai_service.get_field_matching_schema()

        results_response = self.ai_service.call_with_function(
            resulsts_prompt, results_function_schema
        )

        # Check if results_response is empty or None
        if not results_response:
            error_msg = _("LLM returned empty response for field matching")
            logger.error(
                error_msg,
                logger.get_excel_log_filename(excel_filename)
                if excel_filename
                else None,
            )
            raise FileProcessingError(error_msg)

        return self._parse_llm_response(results_response, input_fields, excel_filename)

    def _extract_fields_from_context(
        self, context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract all fields from the matched views as context.

        Args:
            context: Context information for matching

        Returns:
            List of field context dictionaries
        """
        all_fields_context = []

        for field_detail in context:
            all_fields_context.append(
                {
                    "view_name": field_detail.get("view_name", ""),
                    "view_desc": field_detail.get("view_desc", ""),
                    "field_name": str(field_detail.get("field_name", "")),
                    "field_desc": str(field_detail.get("field_desc", "")),
                    "is_key": bool(field_detail.get("is_key", False)),
                    "data_type": str(field_detail.get("data_type", "")),
                    "field_id": str(field_detail.get("field_id", "")),
                    "length_total": str(field_detail.get("length_total", "")),
                    "length_dec": str(field_detail.get("length_dec", "")),
                }
            )

        return all_fields_context

    def _parse_llm_response(
        self,
        function_response: Dict[str, Any],
        input_fields: List,
        excel_filename: str = None,
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured results.

        Args:
            function_response: Raw LLM response
            input_fields: List of input fields
            excel_filename: Name of the Excel file for logging

        Returns:
            List of parsed matching results
        """
        results = []
        matches = function_response.get("review", [])

        # Create mapping by row_index for exact matching
        match_map = {
            m.get("row_index"): m for m in matches if m.get("row_index") is not None
        }

        # Log matching info for debugging
        logger.debug(
            f"LLM returned {len(matches)} matches for {len(input_fields)} input fields",
            logger.get_excel_log_filename(excel_filename) if excel_filename else None,
        )

        for input_field in input_fields:
            # Handle both InterfaceField objects and dictionaries
            if hasattr(input_field, "row_index"):
                # InterfaceField object
                row_index = input_field.row_index
            else:
                # Dictionary
                row_index = input_field.get("row_index")

            match_result = match_map.get(row_index, {})

            # If no exact row match found, log warning
            if not match_result:
                logger.warning(
                    f"⚠️ No LLM match found for row {row_index}, using empty values",
                    logger.get_excel_log_filename(excel_filename)
                    if excel_filename
                    else None,
                )

            key_flag_raw = match_result.get("key_flag", "")
            key_flag = normalize_key_flag(key_flag_raw)

            # Clean field_id to remove view name prefix (technical field name)
            raw_field_id = match_result.get("field_id", "")
            clean_field_id_val = clean_field_id(raw_field_id)

            # Parse notes to extract percentage and description
            notes_text = match_result.get("notes", "")
            match_percentage, notes_description = parse_notes(notes_text)

            # field_name should be the field description
            field_name = match_result.get("field_desc", "")

            results.append(
                {
                    "table_id": match_result.get("table_id", ""),
                    "field_id": clean_field_id_val,  # Technical field name
                    "field_name": field_name,  # Field description
                    "key_flag": key_flag,
                    "obligatory": match_result.get("obligatory", ""),
                    "data_type": match_result.get("data_type", ""),
                    "length_total": match_result.get("length_total", ""),
                    "length_dec": match_result.get("length_dec", ""),
                    "field_desc": match_result.get("field_desc", ""),
                    "sample_value": match_result.get("sample_value", ""),
                    "match": match_result.get("match"),
                    "notes": match_result.get("notes", ""),
                }
            )

        return results

    def _archive_processed_file(self, source_file_path: Path) -> bool:
        """Move successfully processed file to excel_archive folder.

        Args:
            source_file_path: Path to the source file to archive

        Returns:
            bool: True if archiving was successful, False otherwise
        """
        try:
            from core.consts import Directories

            # Create archive directory if it doesn't exist
            archive_dir = self.data_dir / Directories.EXCEL_ARCHIVE
            archive_dir.mkdir(exist_ok=True)

            # Generate archived filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_filename = f"{timestamp}_{source_file_path.name}"
            archive_path = archive_dir / archive_filename

            # Move the file to archive
            shutil.move(str(source_file_path), str(archive_path))

            # logger.info(
            #     f"File archived: {source_file_path.name} → {archive_filename}",
            #     logger.get_excel_log_filename(source_file_path.name),
            # )
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to archive file {source_file_path.name}: {e}",
                logger.get_excel_log_filename(source_file_path.name),
            )
            return False
