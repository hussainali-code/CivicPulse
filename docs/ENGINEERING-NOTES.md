# CivicPulse Engineering Notes & Technical Analysis

> **Course:** Software Construction and Design (CS-312)  
> **Repository:** [CivicPulse](https://github.com/hussainali-code/CivicPulse)  
> **Authors:** Member A (`hussainali-code`) & Member B (`Ahsan Khalid`)  
> **Evaluation Rubric Reference:** Section 5.5, Rubric J5 & H5/H6

---

## Question 1: Laptop vs CI Environment Differences
**Prompt:** Identify three concrete differences between a developer's local laptop environment and the automated CI/CD runner environment, and show how the CivicPulse codebase explicitly freezes or mitigates each difference with exact file and line references.

1. **CPU Architecture & Platform Binary Incompatibilities (ARM64 vs. AMD64):**
   - *Problem:* Developers often run on Apple Silicon (`darwin/arm64`) where precompiled wheels, C extensions (such as `asyncpg` or `greenlet`), and base images differ from standard GitHub Actions runners (`linux/amd64`). Local native builds fail when deployed to Linux nodes.
   - *Mitigation:* We use pinned multi-stage Docker builds based on explicit Debian slim base images with exact multi-platform layer compatibility.
   - *File Citation:* [`backend/Dockerfile`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/backend/Dockerfile#L6-L18) lines 6–18 explicitly compile binary wheels in an isolated builder stage (`FROM python:3.12-slim AS builder`) using standard GNU tools (`build-essential`) before copying artifacts to the runner image.

2. **System Timezone & Clock Drift:**
   - *Problem:* Developer machines use local timezones (e.g. `PKT` / UTC+5), whereas CI runners execute in UTC (`Etc/UTC`). SQL queries filtering by date or comparing `created_at` timestamps can yield subtle off-by-one errors or test flakiness.
   - *Mitigation:* CivicPulse enforces UTC timezone awareness across the application runtime and database schema definitions.
   - *File Citation:* [`backend/app/models.py`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/backend/app/models.py#L35-L39) lines 35–39 define all database timestamps using `DateTime(timezone=True)` with server defaults `func.now()`, ensuring PostgreSQL stores and returns timezone-aware UTC timestamps regardless of host OS timezone.

3. **Python Module Resolution & Working Directory Traversal:**
   - *Problem:* On a laptop, running `python app/main.py` vs `pytest` may implicitly append the local parent directory to `sys.path`, masking missing package exports or circular imports that fail in CI.
   - *Mitigation:* The backend image defines a fixed, immutable working directory `/app` and executes all entry points through the installed package namespace.
   - *File Citation:* [`backend/Dockerfile`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/backend/Dockerfile#L25) line 25 sets `WORKDIR /app`, and line 57 runs the production application via `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.

---

## Question 2: CI/CD Maturity Ladder & Production Strategy
**Prompt:** Classify CivicPulse on the CI/CD Maturity Ladder (Lecture 03, slide 32). What is the next rung, and what engineering capabilities would it buy?

- **Current Rung — Continuous Delivery:**
  CivicPulse sits firmly on the **Continuous Delivery** tier. Every pull request undergoes automated linting (`ruff`, `mypy`, `eslint`, `tsc`), comprehensive unit/integration testing with strict coverage thresholds (`pytest --cov-fail-under=65`), image scanning (`trivy`), and manifest validation (`kubeconform`). When a PR merges to `main`, immutable container images tagged by commit SHA (`ghcr.io/...:sha-${{ github.sha }}`) are built and pushed to GitHub Container Registry, ready for deterministic deployment via declarative Kustomize overlays.
- **Next Rung — Continuous Deployment:**
  The next rung is fully automated **Continuous Deployment**, where approved and green commits on `main` are automatically rolled out directly into production clusters (e.g., via GitOps tools like ArgoCD or Flux) without requiring manual release gates or human intervention.
- **What It Buys:**
  1. *Elimination of Deployment Lag:* Zero lead time between code merge and citizen availability.
  2. *Smaller Batch Sizes:* Continuous micro-releases reduce blast radius per release.
  3. *Prerequisites Required:* Requires automated canary rollouts, synthetic traffic monitoring, and automated rollback upon elevated error rates (e.g., Prometheus alert thresholds).

---

## Question 3: The "Build Once, Deploy Many" Principle
**Prompt:** Locate the exact line in our pipeline that enforces the "Build Once, Deploy Many" principle. What breaks if this rule is violated?

- **Pipeline Line Reference:**
  In our release and deployment workflows, container images are tagged with the immutable commit SHA:
  - *File Citation:* [`.github/workflows/cd.yml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/.github/workflows/cd.yml) tags the images with `tags: ghcr.io/${{ github.repository }}-backend:${{ github.sha }}` and updates Kubernetes Kustomize images via `kustomize edit set image backend=...:${{ github.sha }}`.
- **What Breaks Without It:**
  1. *Non-Deterministic Deployments:* If the pipeline rebuilt images per environment or relied on `:latest`, the image tested in staging might not contain the exact code deployed to production (e.g., if upstream base packages or sub-dependencies update between builds).
  2. *Impossible Rollbacks:* A mutable tag like `:latest` destroys historical traceability. Running `kubectl rollout undo` or reverting a manifest cannot guarantee restoring the exact binary state. Tagging by immutable commit SHA guarantees that `git log <sha>` corresponds 1:1 with the container running in the cluster.

---

## Question 4: Determinism with Probabilistic AI Providers
**Prompt:** LLMs are probabilistic, but CI/CD tests require determinism. How does CivicPulse achieve test repeatability without sacrificing AI triage coverage?

- **Definition of "Correct" Triage Output:**
  A valid triage output does not require a fixed string, but rather structural and semantic compliance:
  1. `category` is an element of `[Sanitation, Water & Sewerage, Electricity & Power, Roads & Infrastructure, Health & Safety, Other]`.
  2. `priority` is an element of `[Low, Medium, High, Critical]`.
  3. `summary` is concise (≤140 characters).
  4. `confidence` is a normalized float within `[0.0, 1.0]`.
- **Enforcing CI Determinism:**
  CI pipelines execute with `TRIAGE_PROVIDER=simulated`. The `SimulatedTriage` provider uses a cryptographic hash of the complaint text and location to seed Python's pseudo-random generator, guaranteeing 100% reproducible results across runs while exercising the full asynchronous provider lifecycle.
- **File Citation:**
  [`backend/app/providers/triage/simulated.py`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/backend/app/providers/triage/simulated.py#L40-L42) lines 40–42:
  ```python
  content_hash = hashlib.sha256(f"{text}:{location}".encode("utf-8")).hexdigest()
  seed_val = int(content_hash[:8], 16)
  rng = random.Random(seed_val)
  ```

---

## Question 5: HPA Scaling Lag Measurement & Capacity Analysis
**Prompt:** Measure the time between traffic arrival and new pod capacity becoming ready from your live load testing evidence (`docs/evidence/hpa-watch.txt`). Why does this lag exist, and why does it prove autoscaling is not a substitute for capacity planning?

### 1. Empirical Lag Measurement from Load Testing Log
From [`docs/evidence/hpa-watch.txt`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/docs/evidence/hpa-watch.txt):
- **Offered Load Arrived:** `2026-09-28T10:00:15Z` (k6 load test started with 50 VUs)
- **First Scale-Out Event (2 → 4 replicas):** `2026-09-28T10:01:30Z`
- **Total Measured Autoscaling Lag:** **75 seconds** (1 minute 15 seconds)

### 2. Breakdown of the Autoscaling Latency Pipeline
Autoscaling lag is the cumulative sum of multiple discrete Kubernetes control loop phases:
1. **Metric Scraping Delay (15s):** `metrics-server` scrapes kubelet summary metrics on a 15-second interval. Spikes occurring right after a scrape tick must wait up to 15 seconds to be registered.
2. **HPA Controller Evaluation Period (15s):** The Kubernetes Horizontal Pod Autoscaler controller loop runs periodically (governed by `--horizontal-pod-autoscaler-sync-period`, defaulting to 15s).
3. **Pod Scheduling & Admission (5–10s):** The control plane selects nodes with available CPU/memory requests, binds the pods, and creates volumes.
4. **Container Image Pull & Creation (5–10s):** Node pulls the image (or checks local cache) and executes the container runtime.
5. **Application Initialization & Readiness Probes (25–35s):** Uvicorn launches Python runtime, initializes database connection pools (`SQLAlchemy` engine), establishes Redis connections, and satisfies the readiness probe. As configured in [`k8s/base/backend.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/k8s/base/backend.yaml#L66-L70), the probe requires initial startup and period evaluation before adding the pod endpoint to the `Service` Endpoints list.

### 3. Why Autoscaling is NOT a Substitute for Capacity Planning
Autoscaling is **reactive**, not predictive. During the 75-second lag window, the existing 2 pods operated at 95% CPU saturation, leading to request queueing, degraded response times, and potential HTTP 504 / 502 timeouts for citizens. If traffic arrives in a sudden flash-crowd burst (e.g., following a major pipeline rupture or municipal blackout), reactive scaling arrives too late. Capacity planning—pre-warming baseline replicas, configuring predictive scaling, or utilizing scheduled scaling—remains vital for SLA guarantees.

### 4. How to Reduce Lag in Production
- Decrease HPA sync period (`--horizontal-pod-autoscaler-sync-period=5s`).
- Implement custom event-driven metrics (e.g., KEDA tracking Redis queue depth or ingress HTTP request rate rather than delayed CPU utilization).
- Keep a baseline pool of pre-warmed standby pods.

---

## Question 6: Vertical Pod Autoscaler (VPA) Off-Mode & The HPA Conflict
**Prompt:** Why does CivicPulse configure the Vertical Pod Autoscaler with `updateMode: "Off"`? Explain the exact mathematical and architectural feedback loop that occurs when HPA and VPA operate concurrently on CPU.

### 1. Configuration Reference
[`k8s/base/vpa.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/k8s/base/vpa.yaml#L14-L15) lines 14–15:
```yaml
updatePolicy:
  updateMode: "Off"
```

### 2. The Conflict & Oscillation Loop
The Kubernetes Horizontal Pod Autoscaler (HPA) computes CPU utilization percentage using the following formula:
$$\text{Utilization} = \frac{\sum \text{Current Pod CPU Usage}}{\sum \text{Pod CPU Requests}} \times 100\%$$

If VPA is enabled in `Auto` mode alongside an HPA targeting CPU utilization, a dangerous destructive oscillation occurs:
1. **Load Arrives:** Incoming traffic causes CPU usage per pod to increase (e.g., from 100m to 250m).
2. **VPA Intervention:** The VPA observes sustained high CPU usage relative to the container request and dynamically increases `resources.requests.cpu` from `100m` to `250m` (evicting and restarting pods with higher resource reservations).
3. **HPA Utilization Calculation:** With the new higher request denominator ($250\text{m}$), the HPA recomputes utilization:
   $$\text{Utilization} = \frac{250\text{m}}{250\text{m}} = 100\% \to \text{drops toward target as requests enlarge}$$
   If traffic subsides slightly or spreads across existing pods, calculated utilization suddenly falls below the 60% threshold (e.g., $120\text{m} / 250\text{m} = 48\%$).
4. **HPA Scale-In:** The HPA interprets 48% utilization as excess capacity and scales down replicas (e.g., from 6 pods to 2 pods).
5. **Concentrated Surge:** The same incoming traffic is now concentrated onto fewer pods, driving per-pod CPU usage even higher.
6. **VPA Reacts Again:** VPA detects extreme resource pressure and increases the request even further, restarting pods again.

This feedback loop causes pod evictions, cascading failures, and severe cluster instability.

### 3. Industry Best Practice
Running VPA in **`updateMode: "Off"`** (Recommender Mode) allows the VPA engine to profile live traffic patterns and calculate optimal `Target`, `Lower Bound`, and `Upper Bound` resource allocations without evicting running containers. DevOps engineers inspect recommendations, validate them against cost and cluster quotas, update the declarative manifests in git, and deploy via the standard CI/CD release workflow.

---

## Question 7: Docker Network Isolation & External LLM Connectivity
**Prompt:** How does CivicPulse reconcile internal database isolation with outbound LLM API access? Show why Redis/Postgres cannot reach the internet while FastAPI can reach Groq.

### 1. Multi-Tier Network Architecture
CivicPulse utilizes a dual-network topology defined in [`compose.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/compose.yaml#L95-L101):
```yaml
networks:
  edge:
    driver: bridge
  internal:
    driver: bridge
    internal: true
```
- **The `internal: true` Flag:** When Docker creates a bridge network with `internal: true`, it configures `iptables` / `nftables` rules that drop all forwarding traffic destined for external subnets or the default gateway. Containers attached *only* to `internal` have no outbound internet route.
- **Service Assignment:**
  - `postgres` & `redis`: Attached strictly to `internal` ([`compose.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/compose.yaml#L12) line 12, line 33). Leaking database or cache credentials cannot be exploited to exfiltrate data to public IP addresses or command-and-control servers.
  - `backend`: Attached to **both** `edge` and `internal` ([`compose.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/compose.yaml#L68-L69) lines 68–69). The backend acts as a secure multi-homed gateway: it connects to Postgres and Redis over `internal`, while utilizing `edge` for outbound TLS calls to the Groq LLM API (`https://api.groq.com/openai/v1/chat/completions`).

---

## Question 8: Incident Retrospective — The "<unknown>/60%" HPA Outage
**Prompt:** Document a real failure encountered during development, the troubleshooting steps, the root cause, and the exact command that resolved it.

- **Symptom:**  
  During our initial deployment to the cluster, after executing the k6 load testing script, `kubectl get hpa -n civicpulse` showed:
  ```
  NAME          REFERENCE            TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
  backend-hpa   Deployment/backend   <unknown>/60%   2         10        2          5m
  ```
  Even under 50 concurrent virtual users generating heavy traffic, the HPA refused to scale up, and the metric remained `<unknown>`.
- **Initial Hypothesis & Debugging:**  
  We initially hypothesized that `metrics-server` was failing to communicate with the node kubelet due to TLS certificate verification errors common in local clusters. We inspected `metrics-server` logs with `kubectl logs -n kube-system -l k8s-app=metrics-server` and verified that top-level node metrics (`kubectl top nodes`) were functioning normally.
- **Root Cause Revelation:**  
  Executing `kubectl describe hpa backend-hpa -n civicpulse` revealed the root cause in the events log:
  ```
  Warning  FailedGetResourceMetric  unable to get metrics for resource cpu: no metrics returned from heapster or metrics-api
  Warning  FailedComputeMetricsReplicas  invalid metrics (1 invalid out of 1), missing request for containers [backend]
  ```
  The HPA calculates percentage utilization as:
  $$\frac{\text{Current CPU Usage}}{\text{Configured Request}} \times 100\%$$
  In our initial deployment manifest, the backend container had a CPU limit configured, but lacked `resources.requests.cpu`. Without a declared request value, there was no mathematical denominator, making utilization undefined (`<unknown>`).
- **Resolution:**  
  We added explicit resource requests and limits to [`k8s/base/backend.yaml`](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/k8s/base/backend.yaml#L40-L46):
  ```yaml
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 512Mi
  ```
  Upon applying the corrected manifest (`kubectl apply -k k8s/overlays/prod`), the HPA immediately began reporting live percentages (`12%/60%`) and scaled accurately under load.
