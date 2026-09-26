# CivicPulse — AI-Assisted Municipal Complaint Intake & Triage Platform

CivicPulse is an automated municipal complaint intake and AI triage platform built for high-throughput citizen request management, intelligent categorization, priority assignment, and SLA routing.

Built for **CS4032 – Software Construction and Design (Assignment 01)**.

---

## Team Members & Responsibilities

| Member | Role & Focus Areas |
|---|---|
| **Member A** | Lead Architecture, Git Setup, Data Layer (Postgres + Alembic), Docker Compose, K8s Base Manifests, GitHub Actions (CI/CD) |
| **Member B** | API Routes & Triage Factory, Redis Caching, React Frontend (Intake & Triage Dashboard), Nginx Reverse Proxy, K8s Overlays |

---

## Tech Stack

- **Backend:** FastAPI (Async Python 3.12+), SQLAlchemy 2.0 (asyncpg), Alembic, Pydantic v2
- **Frontend:** React 18, Vite, Vanilla CSS design system, Lucide icons
- **Data & Cache:** PostgreSQL 16 (StatefulSet / container), Redis 7 (Alpine)
- **AI Triage:** Pluggable Strategy Pattern (Groq LLM, Local Ollama, Deterministic Rules, Deterministic Simulated)
- **Containerization & Orchestration:** Docker, Docker Compose, Kubernetes (Kustomize overlays: `dev`, `prod`)
- **CI/CD:** GitHub Actions (Automated testing, linting, container builds, security scans)

---

## Project Structure

```
civicpulse/
├── backend/
│   ├── alembic/              # Database migration configurations and scripts
│   │   └── versions/
│   ├── app/
│   │   ├── providers/triage/ # Pluggable AI triage engine (Strategy Pattern)
│   │   ├── repositories/     # Data access layer
│   │   ├── routes/           # FastAPI API endpoints
│   │   └── services/         # Business logic layer
│   └── tests/                # Unit and integration test suites
├── frontend/
│   ├── src/
│   │   ├── api/              # API client and service calls
│   │   ├── components/       # Reusable UI component library
│   │   └── pages/            # Citizen Intake & Staff Triage Dashboard
│   └── tests/                # Frontend component and integration tests
├── k8s/
│   ├── base/                 # Base Kubernetes manifests (Deployments, StatefulSets, Services)
│   └── overlays/
│       ├── dev/              # Development overlay (NodePort / lightweight resources)
│       └── prod/             # Production overlay (Ingress, HPA, PDB, resource limits)
├── load/                     # k6 performance and load testing scripts
├── docs/
│   ├── evidence/             # Screenshots and logs for submission evidence
│   ├── AI-USAGE.md           # AI tooling disclosures and prompts log
│   ├── ENGINEERING-NOTES.md  # Architectural and design decisions
│   ├── RUNBOOK.md            # Operational and deployment runbook
│   └── TRIAGE.md             # Triage engine design and benchmark comparison
├── adr/                      # Architecture Decision Records (0001 - 0004)
├── scripts/                  # Automated submission validation and health-check scripts
├── .github/workflows/        # GitHub Actions CI, CD, and Release workflows
├── compose.yaml              # Local development compose configuration
├── compose.prod.yaml         # Production-ready compose configuration
├── .env.example              # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Quickstart (Local Development)

### 1. Prerequisites
- Docker Engine 24+ & Docker Compose v2+
- Python 3.12+ (for local backend development)
- Node.js 20+ & npm (for local frontend development)

### 2. Configuration
```bash
cp .env.example .env
# Adjust environment variables in .env if needed
```

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```
- **Frontend:** http://localhost:80
- **API Documentation (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
