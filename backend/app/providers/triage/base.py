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


class DefaultSimulatedTriage:
    name: str = "simulated"

    async def triage(self, text: str, location: str) -> TriageResult:
        lower = text.lower()
        if any(w in lower for w in ["water", "pipe", "leak", "main"]):
            cat = Category.WATER
            prio = Priority.HIGH if any(w in lower for w in ["burst", "flood", "flooding"]) else Priority.NORMAL
        elif any(w in lower for w in ["electric", "power", "wire", "voltage", "blackout"]):
            cat = Category.ELECTRICITY
            prio = Priority.HIGH if any(w in lower for w in ["spark", "fire", "shock"]) else Priority.NORMAL
        elif any(w in lower for w in ["road", "pothole", "asphalt", "crater"]):
            cat = Category.ROADS
            prio = Priority.NORMAL
        elif any(w in lower for w in ["light", "lamp", "dark", "pole"]):
            cat = Category.STREETLIGHTS
            prio = Priority.LOW
        elif any(w in lower for w in ["trash", "garbage", "waste", "drain", "sewer", "gutters"]):
            cat = Category.SANITATION
            prio = Priority.NORMAL
        else:
            cat = Category.OTHER
            prio = Priority.NORMAL

        summary = (text[:137] + "...") if len(text) > 140 else text
        return TriageResult(
            category=cat,
            priority=prio,
            summary=summary,
            confidence=0.85,
        )


def get_triage_provider() -> TriageProvider:
    return DefaultSimulatedTriage()
