"""
SAP IF Design Generation Tool.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from core.config import ConfigurationManager
from core.i18n import initialize_i18n, _
from excel.excel_processor import ExcelProcessor
from utils.ai_connectivity_test import auto_select_ai_service
from utils.token_statistics import initialize_token_tracker, set_current_provider, save_and_print_usage


def setup_directories() -> Path:
    """Setup and validate application directories."""
    from core.consts import Directories

    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"

    # Create required directories if they don't exist
    required_dirs = [
        data_dir / Directories.EXCEL_INPUT,
        data_dir / Directories.EXCEL_OUTPUT,
        data_dir / Directories.EXCEL_ARCHIVE
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Validate data directory exists
    if not data_dir.exists():
        raise FileNotFoundError(_("Data directory not found: {}").format(data_dir))

    return data_dir


def get_excel_files(data_dir: Path) -> list:
    """Get all Excel files from input directory."""
    from core.consts import Directories, FileExtensions
    input_dir = data_dir / Directories.EXCEL_INPUT

    if not input_dir.exists():
        return []

    excel_files = []
    for ext in [FileExtensions.XLSX, ".xls"]:
        excel_files.extend(input_dir.glob(f"*{ext}"))

    return excel_files


def format_execution_time(seconds):
    """将秒数转换为小时、分钟、秒的格式"""
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    return _("{}h {}m {:.2f}s").format(hours, minutes, seconds)


def main():
    """Main application entry point."""
    print("-" * 50)
    project_start_time = datetime.now()
    print(_("[Project Start Time]: {}").format(project_start_time.strftime('%Y-%m-%d %H:%M:%S')))
    print("-" * 50)

    parser = argparse.ArgumentParser(description=_("SAP IF Design Generation Tool"))
    parser.add_argument(
        "--file",
        type=str,
        help=_("Process specific Excel file (relative to input directory)")
    )

    parser.add_argument(
        "--langu",
        type=str,
        choices=["en", "zh", "ja"],
        help=_("Set interface language (en, zh, ja)")
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["claude", "gemini", "openai"],
        help=_("Choose AI provider (claude, gemini, openai) - all via AI Core")
    )

    args = parser.parse_args()

    # Initialize internationalization first
    config_manager = ConfigurationManager()
    language_config = config_manager.get_language_config()

    # Determine language to use
    target_language = args.langu or language_config.get('language', 'en')
    initialize_i18n(target_language)

    try:
        # Setup directories
        data_dir = setup_directories()

        # Initialize token tracker
        base_dir = Path(__file__).parent
        token_tracker = initialize_token_tracker(base_dir)

        # Auto-select AI service
        print(_("[Step 1] 🔍 Auto-detecting available AI services..."))

        # Use the specified provider
        ai_service, service_name = auto_select_ai_service(config_manager, args.provider, target_language)

        # Set current provider for token tracking
        set_current_provider(service_name)

        print("-" * 50)
        print(_("[Step 2] 📄 Excel Processing..."))
        # Initialize Excel processor with AI service
        excel_processor = ExcelProcessor(data_dir, ai_service, config_manager)

        if args.file:
            # Process specific file
            from core.consts import Directories
            file_path = data_dir / Directories.EXCEL_INPUT / args.file
            if file_path.exists():
                try:
                    file_start_time = datetime.now()
                    print(_("Processing file: {} start time: {}").format(args.file,
                                                                         file_start_time.strftime('%Y-%m-%d %H:%M:%S')))

                    excel_processor.process_file(file_path)

                    file_end_time = datetime.now()
                    print(_("Completed: {} ✅").format(args.file))
                    print("-" * 50)

                    # 计算当前文件的单独处理时间
                    file_seconds = (file_end_time - file_start_time).total_seconds()
                    # 计算从项目开始到当前文件完成的累计时间
                    project_elapsed_seconds = (file_end_time - project_start_time).total_seconds()

                    # 输出时间信息
                    print(_("Processing {} completed at: {}").format(file_path.name,
                                                                     file_end_time.strftime('%Y-%m-%d %H:%M:%S')))
                    print(_("File processing time: {}").format(format_execution_time(file_seconds)))
                    print(_("Total project time: {}").format(format_execution_time(project_elapsed_seconds)))

                except Exception as e:
                    print(_("❌ Failed to process {}: {}").format(args.file, e))
                    sys.exit(1)
            else:
                print(_("File not found: {}").format(args.file))
                sys.exit(1)
        else:
            # Auto-process all Excel files in input directory
            excel_files = get_excel_files(data_dir)

            if not excel_files:
                print(_("❌ No Excel files found in data/excel_input/ directory"))
                print(_("❌ Please add Excel files to process or use --file to specify a file"))
                return

            print(_("Found {} Excel file(s) to process:").format(len(excel_files)))
            for file_path in excel_files:
                print(f"   - {file_path.name}")

                # Process each file
            for file_path in excel_files:
                try:
                    file_start_time = datetime.now()
                    print(_("\nProcessing: {} start time: {}").format(file_path.name,
                                                                    file_start_time.strftime('%Y-%m-%d %H:%M:%S')))

                    excel_processor.process_file(file_path)

                    file_end_time = datetime.now()
                    print(_("Completed: {} ✅ Available end time: {}").format(file_path.name, file_end_time.strftime(
                        '%Y-%m-%d %H:%M:%S')))
                    print("-" * 50)

                    # 计算当前文件的单独处理时间
                    file_seconds = (file_end_time - file_start_time).total_seconds()
                    # 计算从项目开始到当前文件完成的累计时间
                    project_elapsed_seconds = (file_end_time - project_start_time).total_seconds()

                    # 输出时间信息
                    print(_("{}  execution time: {}").format(file_path.name, format_execution_time(file_seconds)))

                    processed_files = excel_files if not args.file else [data_dir / "excel_archive" / args.file]
                    additional_info = {
                        "ai_provider": service_name,
                        "processed_files": file_path.name,
                        "total_files": 1
                    }

                    token_file = save_and_print_usage(additional_info)

                except Exception as e:
                    print(_("❌ Failed 456 to process {}: {}").format(file_path.name, e))
                continue

            print(_("\n🎉 All files processed!"))
        # processed_files = excel_files if not args.file else [data_dir / "excel_archive" / args.file]
        # additional_info = {
        #     "ai_provider": service_name,
        #     "processed_files": [f.name for f in processed_files if f.exists()],
        #     "total_files": len(processed_files)
        # }
        #
        # token_file = save_and_print_usage(additional_info)
        print("-" * 50)

        # 所有文件处理完成后，输出项目总耗时
        project_end_time = datetime.now()
        total_project_seconds = (project_end_time - project_start_time).total_seconds()
        print("\n" + "=" * 50)
        print(_("[Project End Time]: {} =====").format(project_end_time.strftime('%Y-%m-%d %H:%M:%S')))
        print(_("===== Total Time: {} =====").format(format_execution_time(total_project_seconds)))
    except Exception as e:
        print(_("❌ Application error: {}").format(e))

        try:
            additional_info = {
                "ai_provider": service_name if 'service_name' in locals() else "unknown",
                "error": str(e),
                "status": "failed"
            }
            save_and_print_usage(additional_info)
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
