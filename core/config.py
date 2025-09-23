"""
Configuration management using Pydantic.
"""

from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from core.consts import AIProvider, Languages
from utils.tools import detect_system_language


class ExcelConfig(BaseSettings):
    """Excel processing settings."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    sheet_name: str = "IF項目定義"
    header_row: int = 6
    start_row: int = 13
    batch_size: int = Field(30, alias="BATCH_SIZE")
    max_concurrent_batches: int = Field(5, alias="MAX_WORKERS")


class ColumnMappings(BaseSettings):
    """Static column mappings for Excel input/output."""

    model_config = SettingsConfigDict(env_prefix="")

    input_header_cols: Dict[str, str] = {"module": "C", "if_name": "H", "if_desc": "I"}
    input_row_cols: Dict[str, str] = {
        "field_name": "C",
        "key_flag": "D",
        "obligatory": "E",
        "data_type": "I",
        "field_id": "H",
        "length_total": "J",
        "length_dec": "K",
        "field_text": "L",
        "sample_value": "N",
    }
    output_columns: Dict[str, str] = {
        "field_name": "S",
        "key_flag": "T",
        "obligatory": "U",
        "table_id": "V",
        "field_id": "W",
        "data_type": "X",
        "length_total": "Y",
        "length_dec": "Z",
        "notes": "AA",
        "sample_value": "AB",
        "match": "AC",
    }


class AIProviderDetails(BaseSettings):
    """Base configuration details for a single AI provider."""

    model_config = SettingsConfigDict(env_prefix="")

    # No env_prefix here, subclasses will define it
    provider_name: str
    llm_model: str
    embedding_model: str | None = (
        None  # Make optional, can be set by global_embedding_model
    )
    llm_deployment_id: str | None = None
    embedding_deployment_id: str | None = None


class OpenAIProviderDetails(AIProviderDetails):
    model_config = SettingsConfigDict(env_prefix="OPENAI_")
    provider_name: str = "SAP AICore OpenAI"
    llm_model: str = "gpt-4o"
    # embedding_model and deployment_id will be loaded from OPENAI_EMBEDDING_MODEL/OPENAI_EMBEDDING_DEPLOYMENT_ID
    # or fall back to None if not set, then ModelConfig's validator can set global_embedding_model


class ClaudeProviderDetails(AIProviderDetails):
    model_config = SettingsConfigDict(env_prefix="CLAUDE_")
    provider_name: str = "SAP AICore Claude"
    llm_model: str = "anthropic--claude-4-sonnet"


class GeminiProviderDetails(AIProviderDetails):
    model_config = SettingsConfigDict(env_prefix="GEMINI_")
    provider_name: str = "SAP AICore Gemini"
    llm_model: str = "gemini-2.5-pro"


class ModelConfig(BaseSettings):
    """AI model settings for all supported providers."""

    model_config = SettingsConfigDict(env_prefix="")

    default_provider: str = Field(AIProvider.DEFAULT, alias="AI_PROVIDER")

    # Global embedding model, used if provider-specific one is not set
    global_embedding_model: str = Field(
        "text-embedding-ada-002", alias="TEXT_EMBEDDING_MODEL"
    )

    openai: OpenAIProviderDetails = Field(default_factory=OpenAIProviderDetails)
    claude: ClaudeProviderDetails = Field(default_factory=ClaudeProviderDetails)
    gemini: GeminiProviderDetails = Field(default_factory=GeminiProviderDetails)

    @model_validator(mode="after")
    def set_embedding_models(self) -> "ModelConfig":
        """Set embedding_model to global_embedding_model if not explicitly set for a provider."""
        if self.openai.embedding_model is None:
            self.openai.embedding_model = self.global_embedding_model
        if self.claude.embedding_model is None:
            self.claude.embedding_model = self.global_embedding_model
        if self.gemini.embedding_model is None:
            self.gemini.embedding_model = self.global_embedding_model
        return self

    def get_provider_config(self, provider: str) -> AIProviderDetails | None:
        """Get config for a specific provider by name."""
        return getattr(self, provider, None)


class LanguageConfig(BaseSettings):
    """Language and internationalization settings."""

    model_config = SettingsConfigDict(env_prefix="")

    language: str = Field(default="en")
    supported_languages: List[str] = Field(default_factory=lambda: Languages.SUPPORTED)

    @model_validator(mode="after")
    def set_default_language(self) -> "LanguageConfig":
        """Sets the default language based on environment or system settings."""
        # Handle empty string or None case
        if not self.language or not str(self.language).strip():
            self.language = "en"
        else:
            # Ensure it's a string (in case it was parsed as something else)
            self.language = str(self.language).strip()

        # Priority 1: Use language if it's valid and provided via env var
        if self.language and self.language in self.supported_languages:
            return self

        # Priority 2: Detect OS language
        self.language = detect_system_language()
        return self


class AppSettings(BaseSettings):
    """Root configuration object for the entire application."""

    model_config = SettingsConfigDict(env_prefix="")

    # This field will capture the LANGUAGE env var as a plain string
    language_str: str | None = Field(None, alias="LANGUAGE")

    excel: ExcelConfig = Field(default_factory=ExcelConfig)
    columns: ColumnMappings = Field(default_factory=ColumnMappings)
    model: ModelConfig = Field(default_factory=ModelConfig)
    language_config: LanguageConfig = Field(default_factory=LanguageConfig)

    @model_validator(mode="after")
    def assemble_language_config(self) -> "AppSettings":
        """
        Initializes the language configuration.

        If the `LANGUAGE` environment variable is set, it will be used to create
        the `LanguageConfig`. Otherwise, the default factory for `language_config`
        will be used, which then falls back to system language detection or 'en'.
        """
        if self.language_str is not None:
            self.language_config = LanguageConfig(language=self.language_str)
        return self


# Single instance of settings to be used throughout the application
settings = AppSettings()
