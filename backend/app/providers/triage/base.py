from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from app.models import Category, Priority


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(..., max_length=140)
    confidence: float = Field(..., ge=0.0, le=1.0)


@runtime_checkable
class TriageProvider(Protocol):
    name: str

    async def triage(self, text: str, location: str) -> TriageResult:
        ...


from app.providers.triage.factory import get_triage_provider  # noqa: E402

__all__ = ["TriageProvider", "TriageResult", "get_triage_provider"]
