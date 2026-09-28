# ADR 0004: PII Governance, Data Minimization, and External LLM Privacy Safeguards

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Member B (Security & Triage Lead), Member A (Database Lead)
- **Consulted:** SCD Course Rubric (§3.2, §5.3, Rubric C4, J2)
- **Informed:** Core CivicPulse Engineering Team

---

## 1. Context and Problem Statement

Citizen complaints lodged through municipal portals frequently contain sensitive Personally Identifiable Information (PII), such as:

- Pakistani National ID card numbers (CNIC: e.g., `42101-1234567-1`)
- Personal mobile numbers (e.g., `0300-1234567`)
- Full citizen names and residential house addresses
- Email addresses and billing identifiers

Dispatching un-redacted citizen complaint text to external cloud-hosted LLM providers (e.g., Groq Cloud / OpenAI) poses severe privacy, regulatory, and ethical risks.

---

## 2. Decision Outcome

We implement a **Strict Data Minimization & Privacy Boundary** architecture:

1. **Pre-Triage PII Sanitization (`backend/app/providers/triage/llm.py`):**
   Before any text payload is dispatched to an external API, regular expression scrubbers redact detected CNIC patterns, mobile numbers, and email addresses, replacing them with generic tokens (e.g., `[REDACTED_CNIC]`, `[REDACTED_PHONE]`).

2. **Coarse-Grained Geolocation:**
   Only high-level municipal neighborhood names (e.g., "Block 4, Gulshan") are sent to cloud triage. House numbers and specific residential coordinates are never transmitted externally.

3. **On-Premise / Edge Alternatives:**
   For high-security municipal deployments, administrators can configure `TRIAGE_PROVIDER=ollama` or `TRIAGE_PROVIDER=rules`, guaranteeing that 100% of data remains entirely within local, air-gapped infrastructure with zero third-party telemetry.

4. **Data Retention & Encryption:**
   PostgreSQL stores citizen complaints with restricted database role privileges. Passwords and API secrets are strictly managed via Kubernetes Secrets, with no plain-text credentials stored in version control or application logs.
