# ADR 0001: Pluggable AI Triage Provider Interface via Structural Subtyping (`typing.Protocol`)

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Member A (Architect & Infrastructure), Member B (Application & Integrations)
- **Consulted:** SCD Course Rubric (§3.2, Rubric C1–C4)
- **Informed:** Core CivicPulse Engineering Team

---

## 1. Context and Problem Statement

CivicPulse is designed to process municipal complaints across diverse operational environments—ranging from offline edge nodes and air-gapped municipal data centers to scalable cloud deployments. Different environments dictate different triage engines:
1. **Local Development / CI Tests:** Deterministic mock results with zero external network dependencies or API costs.
2. **Offline Municipal Infrastructure:** Lightweight heuristic rule-based engines or local Ollama instances running quantized open-source models (e.g., Llama 3 / Mistral).
3. **High-Throughput Production:** Cloud-hosted fast LLMs (e.g., Groq Llama 3.3 70B Versatile) for high-accuracy multilingual parsing and nuanced sentiment analysis.

We needed an architectural pattern in Python 3.12 that allows seamless hot-swapping and fallback between these engines without altering core business services or introducing rigid inheritance hierarchies.

---

## 2. Decision Drivers

- **Open-Closed Principle (OCP):** Adding a new triage provider (e.g., Anthropic Claude, OpenAI GPT-4o, or local HuggingFace ONNX runtime) must require adding a new class file without modifying existing services (`ComplaintService`).
- **Static & Runtime Type Safety:** Providers must be strictly verifiable by Mypy during CI, while permitting runtime assertion at startup (`isinstance`).
- **Decoupled Architecture:** Business logic in `app/services/complaint_service.py` must depend purely on an abstraction, not on third-party SDKs (such as `openai` or `httpx`).
- **Fault-Tolerant Fallback:** If a cloud provider encounters rate limits (HTTP 429), timeouts (504), or network partitions, the system must transparently fall back to deterministic local providers.

---

## 3. Considered Options

1. **Option 1: Python `typing.Protocol` with `@runtime_checkable` (Structural Subtyping)**
2. **Option 2: Python `abc.ABC` with `@abstractmethod` (Nominal Subtyping)**
3. **Option 3: Procedural Branching (`if/elif/else` within Route Handlers)**

---

## 4. Decision Outcome

**Chosen Option:** **Option 1 (`typing.Protocol` with `@runtime_checkable`)** combined with the **Strategy Pattern** and a factory registry (`backend/app/providers/triage/factory.py`).

### Interface Definition (`backend/app/providers/triage/base.py`)

```python
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
```

### How New Providers Are Added
1. Create a new module under `backend/app/providers/triage/` (e.g., `gemini.py`).
2. Implement the single asynchronous method `async def triage(self, text: str, location: str) -> TriageResult`.
3. Register the provider key in `PROVIDER_REGISTRY` within `backend/app/providers/triage/factory.py`.
4. No base class inheritance is required; Mypy verifies interface adherence statically, and the factory verifies `isinstance(instance, TriageProvider)` at initialization.

---

## 5. Pros and Cons of the Options

### Option 1: `typing.Protocol` (Selected)
* **Positive:** **Zero Nominal Coupling.** Providers do not inherit from a shared base class; they simply satisfy the contract (duck typing with static verification).
* **Positive:** **Testability.** Unit tests can create trivial lightweight mock objects or fakes without mocking ABC internals.
* **Positive:** **Safe Composition.** Avoids fragile base class problem and multiple inheritance conflicts.
* **Positive:** Fully compatible with Pydantic v2 data transfer objects (`TriageResult`).
* **Negative:** Runtime type checking with `isinstance` on protocols only verifies method presence, not parameter types (mitigated by strict Mypy CI checks).

### Option 2: `abc.ABC` (Nominal Subtyping)
* **Positive:** Familiar to developers with Java/C++ backgrounds.
* **Negative:** Rigid class hierarchy. Forces third-party wrapper classes to explicitly inherit from our internal ABC.
* **Negative:** Harder to compose when combining with other mixins or framework classes.

### Option 3: Procedural Branching
* **Negative:** Violates Open-Closed Principle (OCP) and Single Responsibility Principle (SRP).
* **Negative:** Leads to massive conditional blocks, duplicate error handling, and unmaintainable test matrices.

---

## 6. Validation and Evidence

1. **Static Analysis:** Verified via `mypy backend/app/` with 0 type errors.
2. **Provider Implementations:**
   - `SimulatedTriage` (`backend/app/providers/triage/simulated.py`)
   - `RulesTriage` (`backend/app/providers/triage/rules.py`)
   - `LLMTriage` (Groq API, `backend/app/providers/triage/llm.py`)
   - `OllamaTriage` (Local OpenAI-compatible API, `backend/app/providers/triage/ollama.py`)
3. **Automated Fallback:** Verified in `backend/tests/test_triage_member_b.py`, confirming automatic fallback from LLM to RulesTriage when API exceptions or timeouts occur.
