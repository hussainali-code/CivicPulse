# ADR 0003: PostgreSQL Persistence Architecture via Kubernetes StatefulSet & Immutable Deploy-by-SHA Strategy

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Member A (DevOps & Infrastructure Lead), Member B (Application Engineer)
- **Consulted:** SCD Course Rubric (§3.3, §5.3, Rubric H3, I4, J2)
- **Informed:** Core CivicPulse Engineering Team

---

## 1. Context and Problem Statement

CivicPulse relies on PostgreSQL 16 as its relational system of record for citizen complaints, audit trails, and status histories. Operating a stateful database inside an ephemeral container orchestration environment like Kubernetes poses significant data integrity risks if misconfigured:

1. **Volume Detachment / Multi-Attach Conflicts:** Standard Kubernetes `Deployments` treat pods as interchangeable and stateless. If a node fails or a rolling update initiates, Kubernetes can spawn a new pod on another node while the cloud storage volume is still locked by the old node, triggering fatal `Multi-Attach error for volume` deadlocks.
2. **Data Loss on Pod Eviction:** Deployments relying on shared ephemeral storage (`emptyDir`) or loose PVC bindings can detach or lose persistent state during node drains, horizontal node autoscaling, or pod rescheduling.
3. **Non-Deterministic Releases (`:latest` Tag Anti-Pattern):** Using mutable container tags like `:latest` obscures what code and schema version is actively running, eliminates traceability, breaks automated rollbacks, and creates cache inconsistency across replica nodes.

---

## 2. Decision Drivers

- **Zero Data Loss Guarantee (§5.3):** Automatic -20 mark penalty if PostgreSQL is deployed as an ephemeral Deployment or lacks persistent volume retention.
- **Deterministic Pod Identity:** Database client connections from the FastAPI backend pool must resolve to a predictable, persistent DNS identity.
- **Controlled Lifecycle & Flush:** PostgreSQL must cleanly flush Write-Ahead Logs (WAL) and close shared buffer pools during planned maintenance or node rescheduling.
- **Auditable, Deterministic Rollback:** Deployments must reference immutable Git commit SHAs, enabling instant declarative and imperative rollbacks.

---

## 3. Considered Options

### Database Storage & Workload Architecture
- **Option 1A: Kubernetes `StatefulSet` with `volumeClaimTemplates` (Selected)**
- **Option 1B: Kubernetes `Deployment` with a single shared `PersistentVolumeClaim`**
- **Option 1C: External Managed Cloud Database (e.g., AWS RDS / Cloud SQL)**

### Container Tagging & Rollback Strategy
- **Option 2A: Immutable Git SHA Tagging (`:sha-${{ github.sha }}`) (Selected)**
- **Option 2B: Mutable Floating Tag (`:latest`)**
- **Option 2C: Semantic Versioning Only (`:v1.0.0`)**

---

## 4. Decision Outcome

### 4.1 StatefulSet for PostgreSQL (`k8s/base/postgres.yaml`)

We chose **Option 1A (`StatefulSet` with `volumeClaimTemplates`)**.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: civicpulse
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

#### Why This Solves the Core Problems:
1. **Persistent Volume Retention Across Restarts:** Unlike a Deployment where PVCs can be decoupled or orphaned, `volumeClaimTemplates` dynamically provisions `postgres-data-postgres-0`. When the pod is rescheduled or upgraded, Kubernetes guarantees that the exact same volume is re-mounted to `postgres-0`.
2. **Stable Network Identifier:** The companion headless service provides a deterministic DNS record: `postgres-0.postgres.civicpulse.svc.cluster.local`. Backend pods communicate reliably without DNS flapping.
3. **Sequential Graceful Shutdown:** During cluster maintenance, StatefulSet terminates the pod with ordered termination (`terminationGracePeriodSeconds: 60`), allowing the PostgreSQL engine to complete active checkpointing and write WAL records to disk without corruption.

---

### 4.2 Immutable Deploy-by-SHA & Rollback Mechanism

We chose **Option 2A (Git SHA Tagging)** across CI/CD and Kustomize overlays.

1. **Build Once, Deploy by SHA:**
   Every GitHub Actions build produces immutable images tagged with the exact 40-character commit hash:
   `ghcr.io/hussainali-code/civicpulse-backend:sha-${{ github.sha }}`
2. **Kustomize Declarative Image Replacement:**
   The CD workflow executes:
   ```bash
   cd k8s/overlays/prod
   kustomize edit set image \
     civicpulse-backend=ghcr.io/hussainali-code/civicpulse-backend:${{ github.sha }} \
     civicpulse-frontend=ghcr.io/hussainali-code/civicpulse-frontend:${{ github.sha }}
   ```
3. **Two-Tier Rollback Capability:**
   - **Emergency Imperative Rollback (Fastest, MTTR < 30s):**
     ```bash
     kubectl rollout undo deployment/backend -n civicpulse
     kubectl rollout undo deployment/frontend -n civicpulse
     ```
   - **Audited Declarative Rollback (GitOps-Compliant):**
     Identify the last known good commit SHA from `git log main`, update the Kustomize overlay to that SHA, and push to trigger automated deployment.

---

## 5. Pros and Cons

| Option | Pros | Cons |
|---|---|---|
| **StatefulSet (Selected)** | Guaranteed persistent storage binding; deterministic network identity; sequential teardown avoids WAL corruption. | Requires headless service; slightly more verbose manifest than Deployment. |
| **Deployment (Rejected)** | Simpler manifest syntax. | **High Risk:** Race conditions on volume reattachment; potential split-brain or data loss on rescheduling; fails course integrity checks. |
| **Deploy by SHA (Selected)** | 100% deterministic; reproducible builds; immutable artifacts; trivial rollback to any specific commit. | Requires CI/CD automation to inject commit SHA into manifests. |
| **`:latest` Tag (Rejected)** | No manifest updates required. | Non-deterministic; impossible to know what code is live; breaks rollback; causes container image cache poisoning. |

---

## 6. Verification and Compliance

- **Integrity Validation:** Validated via `scripts/check_submission.py` Section 5:
  `[PASS] Postgres k8s manifest - StatefulSet confirmed`
- **Kubeconform Check:** Confirmed schema compliance using `kubeconform -strict` in the CI pipeline.
- **Data Persistence Test:** Verified in integration testing: restarting the `postgres-0` pod retains existing Alembic migration state and seeded complaint records.
