import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from openai import APIStatusError, APITimeoutError

from app.models import Category, Priority
from app.providers.triage.factory import get_triage_provider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage


class InMemoryRedis:
    def __init__(self):
        self.store = {}
        self.get_calls = 0
        self.set_calls = 0

    async def get(self, key: str):
        self.get_calls += 1
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self.set_calls += 1
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)


def create_mock_completion(payload: dict):
    response_mock = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = json.dumps(payload)
    response_mock.choices = [choice_mock]
    return response_mock


@pytest.mark.asyncio
async def test_llm_triage_success():
    """LLMTriage returns valid structured output using Groq API."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=create_mock_completion({
            "category": "water",
            "priority": "high",
            "summary": "Main water pipeline burst flooding sector",
            "confidence": 0.95,
        })
    )
    mock_redis = InMemoryRedis()
    triage = LLMTriage(client=mock_client, redis_client=mock_redis)

    result = await triage.triage(
        "Burst water pipeline flooding houses in Street 12",
        "Sector F-7",
    )

    assert result.category == Category.WATER
    assert result.priority == Priority.HIGH
    assert result.summary == "Main water pipeline burst flooding sector"
    assert result.confidence == 0.95
    assert triage.name == "llm:groq"
    assert triage.last_triaged_by == "llm:groq"
    assert mock_redis.set_calls == 1


@pytest.mark.asyncio
async def test_llm_redis_content_hash_caching():
    """Redis content-hash cache returns cached result on duplicate complaint without calling LLM."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=create_mock_completion({
            "category": "electricity",
            "priority": "high",
            "summary": "Transformer sparking dangerously",
            "confidence": 0.92,
        })
    )
    mock_redis = InMemoryRedis()
    triage = LLMTriage(client=mock_client, redis_client=mock_redis)

    text = "Sparks coming from the neighborhood electric transformer"
    loc = "Commercial Block"

    # First call - MISS
    res1 = await triage.triage(text, loc)
    assert mock_client.chat.completions.create.call_count == 1
    assert mock_redis.get_calls == 1
    assert mock_redis.set_calls == 1

    # Second call - HIT
    res2 = await triage.triage(text, loc)
    # LLM should NOT be called again
    assert mock_client.chat.completions.create.call_count == 1
    assert mock_redis.get_calls == 2
    assert res1.category == res2.category
    assert res1.summary == res2.summary


@pytest.mark.asyncio
async def test_llm_timeout_triggers_retry_and_fallback():
    """LLMTriage retries once on timeout, then falls back to RuleBasedTriage with 'rules:fallback'."""
    mock_client = MagicMock()
    request_mock = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    timeout_err = APITimeoutError(request=request_mock)

    mock_client.chat.completions.create = AsyncMock(side_effect=timeout_err)
    mock_redis = InMemoryRedis()
    triage = LLMTriage(client=mock_client, redis_client=mock_redis)

    # Use patch on asyncio.sleep to fast-forward jitter
    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await triage.triage(
            "Main water pipeline burst flooding houses",
            "Sector F-7",
        )

    # Should attempt initial call + 1 retry
    assert mock_client.chat.completions.create.call_count == 2
    # Should fall back to rule-based classification
    assert result.category == Category.WATER
    assert triage.name == "rules:fallback"
    assert triage.last_triaged_by == "rules:fallback"


@pytest.mark.asyncio
async def test_llm_rate_limit_429_triggers_retry_and_fallback():
    """LLM 429 response retries once with jitter and falls back cleanly."""
    mock_client = MagicMock()
    response_429 = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com"))
    err_429 = APIStatusError("Rate limited", response=response_429, body={"error": "Rate limit exceeded"})

    mock_client.chat.completions.create = AsyncMock(side_effect=err_429)
    mock_redis = InMemoryRedis()
    triage = LLMTriage(client=mock_client, redis_client=mock_redis)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await triage.triage(
            "Broken streetlight on main boulevard",
            "Main Boulevard",
        )

    assert mock_client.chat.completions.create.call_count == 2
    assert result.category == Category.STREETLIGHTS
    assert triage.name == "rules:fallback"


@pytest.mark.asyncio
async def test_llm_malformed_json_falls_back():
    """Malformed non-JSON output from model triggers immediate fallback."""
    mock_client = MagicMock()
    response_mock = MagicMock()
    choice_mock = MagicMock()
    choice_mock.message.content = "Here is your response: Category is water, priority is normal."
    response_mock.choices = [choice_mock]
    mock_client.chat.completions.create = AsyncMock(return_value=response_mock)

    mock_redis = InMemoryRedis()
    triage = LLMTriage(client=mock_client, redis_client=mock_redis)

    result = await triage.triage(
        "Open sewer overflowing near school",
        "Street 4",
    )

    assert result.category == Category.SANITATION
    assert triage.name == "rules:fallback"


@pytest.mark.asyncio
async def test_ollama_triage_success():
    """OllamaTriage successfully parses model response."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=create_mock_completion({
            "category": "roads",
            "priority": "normal",
            "summary": "Dangerous pothole on street",
            "confidence": 0.88,
        })
    )
    mock_redis = InMemoryRedis()
    triage = OllamaTriage(client=mock_client, redis_client=mock_redis)

    result = await triage.triage(
        "Big pothole damaged car tire",
        "Avenue 3",
    )

    assert result.category == Category.ROADS
    assert result.priority == Priority.NORMAL
    assert triage.name == "llm:ollama"


@pytest.mark.asyncio
async def test_ollama_error_fallback():
    """OllamaTriage falls back to RuleBased on connection error."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=ConnectionError("Cannot reach Ollama"))
    mock_redis = InMemoryRedis()
    triage = OllamaTriage(client=mock_client, redis_client=mock_redis)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await triage.triage(
            "Garbage pile rotting on the sidewalk",
            "Sector I-8",
        )

    assert result.category == Category.SANITATION
    assert triage.name == "rules:fallback"


def test_factory_resolves_all_providers():
    """Factory correctly resolves all provider names."""
    groq_p = get_triage_provider("groq")
    assert isinstance(groq_p, LLMTriage)

    llm_p = get_triage_provider("llm")
    assert isinstance(llm_p, LLMTriage)

    ollama_p = get_triage_provider("ollama")
    assert isinstance(ollama_p, OllamaTriage)
