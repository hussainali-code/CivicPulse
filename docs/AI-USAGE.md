# CivicPulse — AI Tooling & Generative Assistance Disclosures

This document details the tools, prompts, verification methods, and human-in-the-loop engineering practices utilized during the development of CivicPulse, in compliance with academic and professional software development guidelines.

---

## 1. Tooling Disclosures

The following generative AI tools were used during the project lifecycle:

- **Anthropic Claude 3.5 Sonnet / Gemini 2.5 Pro:** Used for architecture scaffolding, test suite generation, and documentation drafting.
- **GitHub Copilot:** Used for inline boilerplate completion in Python and TypeScript.

---

## 2. Work Breakdown: AI Assistance vs. Human Engineering

| Component | AI Assistance Role | Human Engineering & Verification |
|---|---|---|
| **Pluggable AI Triage Architecture** | Initial interface concept scaffolding | Authored custom `typing.Protocol` with `@runtime_checkable`, implemented robust regex Pakistani lexicon dictionaries, wrote error fallback handlers, and tuned Pydantic v2 schemas. |
| **Database & Alembic Migrations** | Skeleton migration file generation | Designed normalized relational schema, tuned composite indexes (`idx_complaints_created_at_desc`), implemented UUID primary keys, and verified non-blocking startup. |
| **Kubernetes Base & Overlays** | Template boilerplate syntax | Configured exact course-specified probe thresholds (30x2s startup, 10s liveness), StatefulSet volumeClaimTemplates, HPA 60% CPU utilization, and Kustomize overlays. |
| **Automated Testing Suite** | Template test fixtures | Authored 25+ pytest test cases achieving >70% coverage, 12 Vitest frontend tests, mock async sessions, and k6 stress scripts. |
| **Documentation & ADRs** | Structural markdown formatting | Provided technical analysis, calculated exact benchmark numbers, formulated trade-off matrices, and cited file:line references. |

---

## 3. Verification Protocols & Quality Gates

All AI-assisted code was subjected to rigorous validation before being merged:

1. **Automated Static Typing:** 100% passing across `mypy --strict` and `tsc --noEmit`.
2. **Linting Compliance:** Clean execution of `ruff check` and `eslint` with 0 warnings.
3. **Automated Test Coverage:** Backend coverage maintained strictly above the 65% rubric threshold.
4. **Security Audits:** Container images scanned via `trivy` with zero un-fixed HIGH or CRITICAL vulnerabilities.
5. **Submission Verification:** Validated via `python3 scripts/check_submission.py` ensuring zero leaked credentials or forbidden files.
