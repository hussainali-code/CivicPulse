# ADR 0003 (Addendum): Immutable Deploy-by-SHA and Rollback Strategy

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Member A (DevOps & Infrastructure Lead), Member B (Application Engineer)
- **Reference:** See comprehensive implementation in [ADR 0003: PostgreSQL StatefulSet & Deploy-by-SHA](file:///Users/macbookprom2/Desktop/SCD%20Assignment/civicpulse/adr/0003-postgres-statefulset.md)

---

## 1. Context and Problem Statement

Deploying cloud-native applications with mutable tags like `:latest` creates critical operational liabilities:
1. **Loss of Determinism:** A pod restart in a Kubernetes cluster can pull a newly pushed image containing breaking changes, leading to unexpected runtime divergence between replica pods in the same Deployment.
2. **Untracked Production State:** In the event of an outage, engineers cannot easily determine which specific Git commit is running across backend and frontend containers.
3. **Impaired Rollbacks:** Running `kubectl rollout undo` on an image tagged `:latest` can re-pull the same corrupted container image rather than reverting to the previous known good binary.

---

## 2. Decision Outcome

We enforce **Immutable Deploy-by-SHA** across all environments:
1. Every container image produced by the GitHub Actions build pipeline is tagged with the exact 40-character commit hash:
   - `ghcr.io/hussainali-code/civicpulse-backend:sha-${{ github.sha }}`
   - `ghcr.io/hussainali-code/civicpulse-frontend:sha-${{ github.sha }}`
2. Continuous Deployment modifies `k8s/overlays/prod/kustomization.yaml` using `kustomize edit set image`, creating an explicit GitOps trace.
3. Rollbacks are executed deterministically either by:
   - **Emergency imperative rollback:** `kubectl rollout undo deployment/backend -n civicpulse`
   - **Declarative GitOps rollback:** `kustomize edit set image civicpulse-backend=ghcr.io/...:<previous-sha>` and `kubectl apply -k .`

---

## 3. Benefits

- **Zero Ambiguity:** Every running container is tied 1:1 to a specific Git commit SHA.
- **Hermetic Caching:** Node container runtimes avoid redundant cache re-validations.
- **Auditable Security:** Syft Software Bill of Materials (SBOM) and Trivy vulnerability scan reports map directly to immutable image digests.
