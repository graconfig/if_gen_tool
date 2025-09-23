"""
AI Service Connectivity Test Tool
"""

from typing import Tuple

from core.config import settings
from core.consts import AIProvider
from core.service_container import container
from utils.exceptions import AIServiceError, ConfigurationError
from utils.i18n import _
from utils.sap_logger import logger
from services.aicore_base_service import AIServiceBase


def create_ai_service_by_provider(
    provider: str, language: str = "en"
) -> AIServiceBase:
    """Create AI service based on provider type.

    Args:
        provider: Provider type ('openai', 'claude', 'gemini')
        language: Language code for the service

    Returns:
        AI service instance configured for the specified provider
    """
    # The container now uses the global settings object, so no need to set it
    return container.get_ai_service(provider, language)


def test_ai_service_connectivity(
    ai_service: AIServiceBase, provider_name: str, log_filename: str = None
) -> bool:
    """Test AI service connectivity"""
    try:
        # Basic connectivity test for all AI Core services
        _ = ai_service.llm_model
        _ = ai_service.embedding_model
        return True
    except Exception as e:
        logger.error(
            _("AI Service initialization failed: {}...").format(str(e)[:100]),
            log_filename,
        )
        return False


def auto_select_ai_service(
    provider_override: str = None,
    language: str = "en",
    log_filename: str = None,
) -> Tuple[AIServiceBase, str]:
    """Automatically select available AI service"""
    # If provider is specified, use it directly
    if provider_override:
        logger.info(
            _("Using specified AI provider: {}").format(provider_override),
            log_filename,
        )
        if provider_override in AIProvider.ALL_PROVIDERS:
            try:
                ai_service = container.get_ai_service(provider_override, language)
                # Set the log filename for response time recording
                if hasattr(ai_service, "_current_log_filename"):
                    ai_service._current_log_filename = log_filename
                provider_config = settings.model.get_provider_config(provider_override)
                return ai_service, provider_config.provider_name
            except Exception as e:
                error_msg = _("Failed to initialize AI provider {}: {}").format(
                    provider_override, str(e)
                )
                logger.error(error_msg, log_filename)
                raise AIServiceError(error_msg) from e
        else:
            error_msg = f"Invalid provider: {provider_override}. Supported providers: {AIProvider.ALL_PROVIDERS}"
            raise ConfigurationError(error_msg)

    # Get default provider from environment configuration
    default_provider = settings.model.default_provider

    # Determine providers_to_test order
    if default_provider and default_provider in AIProvider.ALL_PROVIDERS:
        # First try the configured default provider, then fallback to the priority order
        logger.info(
            _("Using configured default AI provider: {}").format(default_provider),
            log_filename,
        )
        providers_to_test = [default_provider]
        # Add remaining providers in fallback order (claude -> gemini -> openai)
        fallback_providers = [AIProvider.CLAUDE, AIProvider.GEMINI, AIProvider.OPENAI]
        for provider in fallback_providers:
            if provider != default_provider:
                providers_to_test.append(provider)
    else:
        # No default configured, use priority order: Claude -> Gemini -> OpenAI
        logger.info(
            _("No default AI provider configured, testing in priority order"),
            log_filename,
        )
        providers_to_test = [AIProvider.CLAUDE, AIProvider.GEMINI, AIProvider.OPENAI]

    for provider in providers_to_test:
        try:
            provider_config = settings.model.get_provider_config(provider)
            service_name = provider_config.provider_name
            logger.info(
                _("Testing {}...").format(service_name),
                log_filename,
            )
            ai_service = container.get_ai_service(provider, language)
            # Set the log filename for response time recording
            if hasattr(ai_service, "_current_log_filename"):
                ai_service._current_log_filename = log_filename

            if test_ai_service_connectivity(ai_service, provider, log_filename):
                logger.info(
                    _("Selected AI Provider: {}").format(service_name),
                    log_filename,
                )
                return ai_service, service_name
            else:
                logger.error(
                    _("❌ Not available"),
                    log_filename,
                )
        except Exception as e:
            logger.error(
                _("❌ Failed: {}!").format(str(e)[:50] + "..."),
                log_filename,
            )

    # If no available service, throw error
    error_msg = _(
        "❌ No AI services are available. Please check your configuration and API keys."
    )
    logger.error(error_msg, log_filename)
    raise AIServiceError(error_msg)


def test_all_providers(log_filename: str = None) -> dict:
    """Test all AI providers via AI Core"""
    providers = AIProvider.ALL_PROVIDERS
    results = {}

    logger.info(_("🚀 Testing all AI providers via AI Core..."), log_filename)
    logger.info("-" * 80, log_filename)

    for provider in providers:
        try:
            provider_config = settings.model.get_provider_config(provider)
            service_name = provider_config.provider_name
            logger.info(_("\n🧪 Testing {}:").format(service_name), log_filename)
            ai_service = container.get_ai_service(provider)

            if test_ai_service_connectivity(ai_service, provider, log_filename):
                results[provider] = {
                    "status": "available",
                    "llm_model": ai_service.llm_model,
                    "embedding_model": ai_service.embedding_model,
                    "provider_name": service_name,
                }
                logger.info(_("   ✅ Available"), log_filename)
                logger.info(_("   LLM: {}").format(ai_service.llm_model), log_filename)
                logger.info(
                    _("   Embedding: {}").format(ai_service.embedding_model),
                    log_filename,
                )
            else:
                results[provider] = {"status": "unavailable"}
                logger.warning(_("   ❌ Not available"), log_filename)

        except Exception as e:
            results[provider] = {"status": "error", "error": str(e)}
            logger.error(_("   ❌ Error: {}!").format(str(e)[:50] + "..."), log_filename)

    # Print summary
    available = [k for k, r in results.items() if r["status"] == "available"]
    logger.info(_("\n📊 Summary:"), log_filename)
    logger.info(
        _("   Available: {}/{}").format(len(available), len(providers)), log_filename
    )
    if available:
        provider_names = [results[p].get("provider_name", p) for p in available]
        logger.info(
            _("   ✅ Ready: {}").format(", ".join(provider_names)), log_filename
        )
        logger.info(
            _("   🎯 Recommended: {}").format(
                results[available[0]].get("provider_name", available[0])
            ),
            log_filename,
        )
    else:
        logger.warning(_("   ❌ No services available"), log_filename)

    return results


def test_specific_provider(
    provider: str, log_filename: str = None
) -> bool:
    """Test specific AI provider via AI Core"""
    try:
        provider_config = settings.model.get_provider_config(provider)
        service_name = provider_config.provider_name
    except (KeyError, AttributeError):
        error_msg = f"Unknown provider: {provider}. Supported providers: {AIProvider.ALL_PROVIDERS}"
        raise ConfigurationError(error_msg)

    logger.info(_("🧪 Testing {} connectivity...").format(service_name), log_filename)
    logger.info("=" * 40, log_filename)

    try:
        ai_service = container.get_ai_service(provider)

        if test_ai_service_connectivity(ai_service, provider, log_filename):
            logger.info(_("✅ {} is ready to use!").format(service_name), log_filename)
            logger.info(
                _("   LLM Model: {}").format(ai_service.llm_model), log_filename
            )
            logger.info(
                _("   Embedding Model: {}").format(ai_service.embedding_model),
                log_filename,
            )
            return True
        else:
            logger.warning(
                _("❌ {} is not available").format(service_name), log_filename
            )
            return False

    except Exception as e:
        logger.error(
            _("❌ {} test failed: {}!").format(service_name, str(e)), log_filename
        )
        return False


def main():
    """Command line entry point"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=_("AI Service Connectivity Test"))
    parser.add_argument(
        "--provider",
        type=str,
        choices=["claude", "gemini", "openai"],
        help=_("Test specific AI provider via AI Core"),
    )
    parser.add_argument(
        "--all-providers",
        action="store_true",
        help=_("Test all available AI providers"),
    )

    args = parser.parse_args()

    try:
        if args.all_providers:
            # Test all providers
            results = test_all_providers()
            available = [k for k, r in results.items() if r["status"] == "available"]
            if not available:
                sys.exit(1)
        elif args.provider:
            # Test specific provider
            if not test_specific_provider(args.provider):
                sys.exit(1)
        else:
            # Default auto-selection test
            logger.info(_("🚀 Auto-detecting available AI services..."))
            logger.info("-" * 80)
            try:
                _, service_name = auto_select_ai_service()
                logger.info(_("\n🎉 Ready to use {}!").format(service_name))
            except RuntimeError as e:
                logger.error(f"\n{e}")
                sys.exit(1)

        logger.info(_("\n✅ Connectivity test completed!"))

    except Exception as e:
        logger.error(_("❌ Test error: {}!").format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()