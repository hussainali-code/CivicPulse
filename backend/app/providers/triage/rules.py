import re

from app.models import Category, Priority
from app.providers.triage.base import TriageResult

CATEGORY_KEYWORDS: list[tuple[Category, list[str]]] = [
    (
        Category.WATER,
        [
            "pipe", "pipeline", "pani", "water", "leak", "leaking", "burst",
            "flood", "flooding", "seepage", "supply", "tap", "filtration"
        ],
    ),
    (
        Category.ELECTRICITY,
        [
            "bijli", "electric", "power", "wire", "current", "spark", "sparking",
            "transformer", "blackout", "voltage", "feeder", "load shedding", "shock"
        ],
    ),
    (
        Category.SANITATION,
        [
            "kachra", "garbage", "trash", "sewer", "sewerage", "gutter", "drainage",
            "filth", "dump", "smell", "odor", "waste", "carcass", "overflow"
        ],
    ),
    (
        Category.ROADS,
        [
            "sadak", "road", "pothole", "potholes", "sinkhole", "gaddha", "asphalt",
            "flyover", "broken road", "crater", "manhole", "footpath", "sidewalk"
        ],
    ),
    (
        Category.STREETLIGHTS,
        [
            "batti", "streetlight", "street light", "lamp", "pole", "dark",
            "darkness", "light", "bulb", "fixture", "floodlight"
        ],
    ),
]

HIGH_PRIORITY_KEYWORDS = [
    "burst", "spark", "sparking", "fire", "danger", "dangerous", "fatal",
    "hazard", "sinkhole", "hospital", "flood", "flooding", "emergency",
    "urgent", "carcass", "uncovered manhole"
]

LOW_PRIORITY_KEYWORDS = [
    "tap", "flicker", "flickering", "minor", "paint", "repainting",
    "speed breaker", "garden", "wedding", "request"
]


class RuleBasedTriage:
    """
    Deterministic Rule-Based AI Triage Provider.
    Matches complaints against curated keyword dictionaries. Never raises exceptions.
    """
    name: str = "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        lower_text = text.lower()
        combined_text = f"{lower_text} {location.lower()}"

        # 1. Determine Category
        matched_category = Category.OTHER
        max_matches = 0

        for category, keywords in CATEGORY_KEYWORDS:
            matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))
            if matches > max_matches:
                max_matches = matches
                matched_category = category

        # Fallback keyword matching without strict word boundaries if no exact word matched
        if matched_category == Category.OTHER:
            for category, keywords in CATEGORY_KEYWORDS:
                if any(kw in combined_text for kw in keywords):
                    matched_category = category
                    break

        # 2. Determine Priority
        if any(kw in combined_text for kw in HIGH_PRIORITY_KEYWORDS):
            priority = Priority.HIGH
        elif any(kw in combined_text for kw in LOW_PRIORITY_KEYWORDS):
            priority = Priority.LOW
        else:
            priority = Priority.NORMAL

        # 3. Generate Summary
        summary = text.strip().replace("\n", " ")
        if len(summary) > 137:
            summary = summary[:137] + "..."

        confidence = 0.90 if matched_category != Category.OTHER else 0.50

        return TriageResult(
            category=matched_category,
            priority=priority,
            summary=summary,
            confidence=confidence,
        )
