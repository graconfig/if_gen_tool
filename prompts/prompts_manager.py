import os
from pathlib import Path
from functools import lru_cache

import yaml
from jinja2 import Environment, FileSystemLoader

from utils.i18n import get_current_language

class PromptTemplateManager:
    """Manages prompt templates loaded from YAML files for different languages."""

    def __init__(self, templates_dir: Path):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    @lru_cache(maxsize=3) # Cache loaded YAML files for en, zh, ja
    def _load_templates(self, language: str) -> dict:
        """Load and parse the YAML file for a given language."""
        template_file = f"{language}.yaml"
        try:
            with open(self.env.loader.get_source(self.env, template_file)[1], 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            # Fallback to English if the language file has issues
            if language != 'en':
                return self._load_templates('en')
            raise e

    def get(self, prompt_name: str, language: str = None, **kwargs) -> str:
        """Get and render a prompt template."""
        if language is None:
            language = get_current_language()
        
        templates = self._load_templates(language)
        prompt_config = templates.get(prompt_name)

        if not prompt_config:
            raise ValueError(f"Prompt '{prompt_name}' not found in language '{language}'.")

        template_str = prompt_config.get('template', '')
        template = self.env.from_string(template_str)
        
        return template.render(**kwargs)

# Initialize the manager with the default path
_prompt_manager_instance = None

def get_prompt_manager() -> PromptTemplateManager:
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        templates_path = Path(__file__).parent / "templates"
        _prompt_manager_instance = PromptTemplateManager(templates_path)
    return _prompt_manager_instance