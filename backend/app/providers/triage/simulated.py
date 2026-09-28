import hashlib
import random

from app.config import get_settings
from app.providers.triage.base import TriageResult
from app.providers.triage.rules import RuleBasedTriage


class SimulatedTriage:
    """
    Deterministic Simulated Triage Provider.
    Used by default in CI/CD and testing for zero-cost, 100% deterministic runs.
    Supports failure and malformed output injection for robustness verification.
    """
    name: str = "simulated"

    def __init__(
        self,
        failure_injection: bool | None = None,
        malformed_injection: bool | None = None,
    ):
        settings = get_settings()
        self.failure_injection = (
            failure_injection if failure_injection is not None else settings.FAILURE_INJECTION
        )
        self.malformed_injection = (
            malformed_injection if malformed_injection is not None else settings.MALFORMED_INJECTION
        )
        self._rules = RuleBasedTriage()

    async def triage(self, text: str, location: str) -> TriageResult:
        # 1. Fault injection checks
        if self.failure_injection:
            raise RuntimeError("Simulated triage failure injection triggered")
        if self.malformed_injection:
            raise ValueError("Simulated malformed output injection triggered")

        # 2. Derive deterministic seed from content hash
        content_hash = hashlib.sha256(f"{text}:{location}".encode()).hexdigest()
        seed_val = int(content_hash[:8], 16)
        rng = random.Random(seed_val)

        # 3. Base triage from rule heuristics
        base_result = await self._rules.triage(text, location)

        # 4. Deterministic confidence variation between 0.80 and 0.99
        confidence = round(0.80 + (rng.random() * 0.19), 2)

        return TriageResult(
            category=base_result.category,
            priority=base_result.priority,
            summary=base_result.summary,
            confidence=confidence,
        )
