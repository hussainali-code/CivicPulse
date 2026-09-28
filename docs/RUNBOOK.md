# CivicPulse — Operational & Incident Response Runbook

This runbook provides actionable procedures for deploying, monitoring, rolling back, and troubleshooting CivicPulse in development, staging, and production environments.

---

## 1. Deployment Procedures

### 1.1 Docker Compose Deployment (Local / Single Node)

```bash
# Clone and prepare environment
cp .env.example .env

# Start stack with automatic rebuild
docker compose up -d --build

# Verify all services are healthy
docker compose ps
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/ready
```

### 1.2 Kubernetes Production Deployment (Kustomize)

```bash
# Deploy production manifests
kubectl apply -k k8s/overlays/prod

# Await rolling update completion
kubectl rollout status deployment/backend -n civicpulse --timeout=180s
kubectl rollout status deployment/frontend -n civicpulse --timeout=180s

# Verify StatefulSet and HPA
kubectl get statefulset -n civicpulse
kubectl get hpa -n civicpulse
```

---

## 2. Rollback Procedures

### 2.1 Emergency Imperative Rollback (Fastest, MTTR < 30s)

If a faulty deployment causes errors or crashed pods in production:

```bash
# Immediately revert backend and frontend to previous replica revision
kubectl rollout undo deployment/backend -n civicpulse
kubectl rollout undo deployment/frontend -n civicpulse

# Inspect rollout status
kubectl rollout status deployment/backend -n civicpulse
```

### 2.2 Declarative GitOps Rollback (Audited)

Identify the previous stable commit SHA from Git history:

```bash
git log --oneline -5 origin/main
```

Update the Kustomize overlay to target the previous stable SHA:

```bash
cd k8s/overlays/prod
kustomize edit set image \
  civicpulse-backend=ghcr.io/hussainali-code/civicpulse-backend:<PREVIOUS_STABLE_SHA> \
  civicpulse-frontend=ghcr.io/hussainali-code/civicpulse-frontend:<PREVIOUS_STABLE_SHA>
```

Commit and apply:

```bash
kustomize build . | kubectl apply -f -
```

---

## 3. Log Inspection & Monitoring

### 3.1 Streaming Real-Time Structured JSON Logs

```bash
# Backend logs
kubectl logs -l app=backend -n civicpulse -f --tail=100

# Inspect specific pod logs
kubectl logs pod/backend-<pod-hash> -n civicpulse -c backend
```

### 3.2 Key Log Fields for Troubleshooting

All application logs are formatted as structured JSON:

- `request_id`: Unique UUID to trace requests across microservices.
- `client_ip`: Originating client IP address.
- `endpoint`: API path and HTTP method.
- `duration_ms`: Execution latency in milliseconds.
- `triage_provider`: The active AI triage engine used for the request.

---

## 4. Incident Response & Troubleshooting Playbooks

### Playbook 1: External Cloud LLM API Outage (HTTP 429 / 503 / Timeout)

- **Symptom:** Logs show Groq LLM provider failed. Engaging RulesTriage fallback.
- **System Behavior:** Automatic fallback triggers seamlessly; requests return `201 Created` with `[Fallback: Rules]` tagged summaries.
- **Action:**
  1. Inspect Groq API dashboard / status page.
  2. Verify if rate limits were exceeded or API token expired.
  3. If cloud API is prolonged down, switch default provider to local rules via ConfigMap:
     ```bash
     kubectl patch configmap civicpulse-config -n civicpulse --type merge -p '{"data":{"TRIAGE_PROVIDER":"rules"}}'
     kubectl rollout restart deployment/backend -n civicpulse
     ```

### Playbook 2: Redis Cache Unavailable or Unresponsive

- **Symptom:** `/ready` probe returns HTTP 503 with `"redis": false`.
- **Action:**
  1. Verify Redis pod status: `kubectl get pods -l app=redis -n civicpulse`.
  2. Inspect Redis logs: `kubectl logs -l app=redis -n civicpulse`.
  3. Restart Redis deployment: `kubectl rollout restart deployment/redis -n civicpulse`.
  - *Note:* Backend automatically falls back to direct database reads for `/api/stats` if Redis is temporarily unreachable.

### Playbook 3: Database Connection Pool Starvation

- **Symptom:** Latency spikes on `/api/complaints`, 500 errors in logs citing asyncpg pool timeout.
- **Action:**
  1. Check PostgreSQL pod load: `kubectl top pod postgres-0 -n civicpulse`.
  2. Scale up backend replica capacity or adjust pool settings (`DB_POOL_SIZE` in ConfigMap).
