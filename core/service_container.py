"""
Dependency Injection Container for the application.
Manages the creation and lifecycle of services.
"""

from typing import Dict, Type
from core.config import settings  # Import the global settings object
from services.aicore_base_service import AIServiceBase
from services.aicore_claude_service import AICoreClaudeService
from services.aicore_gemini_service import AICoreGeminiService
from services.aicore_openai_service import AICoreOpenAIService


class ServiceContainer:
    """Dependency Injection Container for managing service instances."""

    def __init__(self):
        self._ai_services: Dict[str, AIServiceBase] = {}

    def create_ai_service(self, provider: str, language: str = "en") -> AIServiceBase:
        """Create an AI service instance for the specified provider.

        Args:
            provider: The AI provider to create (claude, gemini, openai)
            language: The language to use for the service

        Returns:
            An instance of the requested AI service
        """
        provider_config = settings.model.get_provider_config(provider)

        if not provider_config:
            raise ValueError(f"Configuration for provider '{provider}' not found")

        # Service factory mapping
        service_map: Dict[str, Type[AIServiceBase]] = {
            "claude": AICoreClaudeService,
            "gemini": AICoreGeminiService,
            "openai": AICoreOpenAIService,
        }

        service_class = service_map.get(provider)
        if not service_class:
            raise ValueError(f"Unsupported AI provider: {provider}")

        return service_class(
            llm_model=provider_config.llm_model,
            embedding_model=provider_config.embedding_model,
            language=language,
            llm_deployment_id=provider_config.llm_deployment_id,
            embedding_deployment_id=provider_config.embedding_deployment_id,
        )

    def get_ai_service(self, provider: str, language: str = "en") -> AIServiceBase:
        """Get or create an AI service instance for the specified provider.

        This method caches service instances to avoid recreating them.

        Args:
            provider: The AI provider to get (claude, gemini, openai)
            language: The language to use for the service

        Returns:
            An instance of the requested AI service
        """
        key = f"{provider}_{language}"
        if key not in self._ai_services:
            self._ai_services[key] = self.create_ai_service(provider, language)
        return self._ai_services[key]


# Global container instance
container = ServiceContainer()