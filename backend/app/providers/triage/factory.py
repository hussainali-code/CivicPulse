import logging
from typing import Optional, cast

from app.config import get_settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

logger = logging.getLogger("civicpulse")


def get_triage_provider(provider_name: Optional[str] = None) -> TriageProvider:
    """
    Factory function returning the configured TriageProvider implementation.
    Configured via TRIAGE_PROVIDER environment variable.
    """
    settings = get_settings()
    name = (provider_name or settings.TRIAGE_PROVIDER).strip().lower()

    if name == "rules":
        return RuleBasedTriage()
    elif name == "simulated":
        return SimulatedTriage()
    elif name in ["groq", "llm", "openai"]:
        try:
            from app.providers.triage.llm import LLMTriage
            return cast(TriageProvider, LLMTriage())
        except (ImportError, AttributeError):
            logger.warning("LLMTriage requested but not yet implemented/available. Falling back to RuleBasedTriage.")
            return RuleBasedTriage()
    elif name == "ollama":
        try:
            from app.providers.triage.ollama import OllamaTriage
            return cast(TriageProvider, OllamaTriage())
        except (ImportError, AttributeError):
            logger.warning("OllamaTriage requested but not yet implemented/available. Falling back to RuleBasedTriage.")
            return RuleBasedTriage()
    else:
        logger.warning(f"Unknown TRIAGE_PROVIDER '{name}', defaulting to SimulatedTriage.")
        return SimulatedTriage()
