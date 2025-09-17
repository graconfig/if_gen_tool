"""
Constants
"""


# AI Provider
class AIProvider:
    # Three distinct providers, all using AI Core backend
    OPENAI = "openai"  # OpenAI models via AI Core
    CLAUDE = "claude"  # Claude models via AI Core
    GEMINI = "gemini"  # Gemini models via AI Core

    # List of all supported providers
    ALL_PROVIDERS = [OPENAI, CLAUDE, GEMINI]
    DEFAULT = CLAUDE


# Directory
class Directories:
    EXCEL_INPUT = "excel_input"
    EXCEL_OUTPUT = "excel_output"
    EXCEL_ARCHIVE = "excel_archive"


# Language Support
class Languages:
    EN = "en"
    ZH = "zh"
    JA = "ja"

    SUPPORTED = [EN, ZH, JA]
    DEFAULT = JA  # Changed default to Japanese


# File Extensions
class FileExtensions:
    TXT = ".txt"
    CSV = ".csv"
    XLSX = ".xlsx"
