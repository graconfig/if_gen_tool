import yaml
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any
import copy

from utils.i18n import get_current_language

class SchemaManager:
    """Manages loading and assembling function calling schemas from a central YAML file."""

    def __init__(self, schemas_file: Path):
        self.schemas_file = schemas_file

    @lru_cache(maxsize=1)
    def _load_schemas(self) -> Dict[str, Any]:
        """Load and parse the main schemas YAML file."""
        try:
            with open(self.schemas_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise IOError(f"Failed to load schemas file: {self.schemas_file}") from e

    def get(self, schema_name: str, language: str = None, provider: str = 'openai') -> Dict[str, Any]:
        """Get a fully assembled schema for a given name, language, and provider."""
        if language is None:
            language = get_current_language()

        all_schemas = self._load_schemas()
        schema_config = all_schemas.get(schema_name)

        if not schema_config:
            raise ValueError(f"Schema '{schema_name}' not found in {self.schemas_file}")

        # Deep copy the base structure to avoid modifying the cached version
        final_schema = copy.deepcopy(schema_config.get('base_structure', {}))
        lang_descriptions = schema_config.get('descriptions', {}).get(language, {})

        # Recursively merge descriptions into the final schema
        self._merge_descriptions(final_schema, lang_descriptions)

        # Adapt the final structure to the provider-specific format
        return self._adapt_to_provider(final_schema, provider)

    def _merge_descriptions(self, base: Dict[str, Any], descriptions: Dict[str, Any]):
        """Recursively merges description dictionaries into a base structure."""
        for key, value in descriptions.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._merge_descriptions(base[key], value)
            else:
                base[key] = value

    def _adapt_to_provider(self, schema: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Adapts a generic schema structure to a provider-specific format."""
        if provider == 'openai':
            return {"type": "function", "function": schema}
        elif provider == 'gemini':
            return {"function_declarations": [schema]}
        elif provider == 'claude':
            # Claude's format is more complex and might need more specific handling
            # This is a simplified adaptation
            return {
                "tools": [{
                    "toolSpec": {
                        "name": schema.get('name'),
                        "description": schema.get('description'),
                        "inputSchema": {"json": schema.get('parameters', {})}
                    }
                }]
            }
        else:
            raise ValueError(f"Unsupported provider for schema adaptation: {provider}")

# Initialize the manager with the default path
_schema_manager_instance = None

def get_schema_manager() -> SchemaManager:
    global _schema_manager_instance
    if _schema_manager_instance is None:
        schemas_path = Path(__file__).parent / "schemas" / "schemas.yaml"
        _schema_manager_instance = SchemaManager(schemas_path)
    return _schema_manager_instance