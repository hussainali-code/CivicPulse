# ADR 0002: Frontend Runtime API Configuration via Nginx Reverse Proxy (Build-Once-Deploy-Many)

- **Status:** Accepted
- **Date:** 2026-09-24
- **Deciders:** Member B (Frontend & Proxy Lead), Member A (Infrastructure Lead)
- **Consulted:** SCD Course Rubric (§3.2, §3.3, Rubric D4, J2)
- **Informed:** Core CivicPulse Engineering Team

---

## 1. Context and Problem Statement

Single Page Applications (SPAs) built with Vite compile client-side JavaScript, TypeScript, and JSX into static asset bundles at build time. In naive implementations, developers bake the backend API base URL into environment variables during build (e.g., `VITE_API_BASE_URL=http://localhost:8000`).

This practice introduces severe architectural drawbacks:

1. **Violation of "Build Once, Deploy Many" (12-Factor App §3):** A container image built for local development cannot be promoted to staging or production without rebuilding the entire JavaScript bundle.
2. **CORS Complications:** Cross-origin browser requests require managing complex Cross-Origin Resource Sharing (CORS) headers and preflight `OPTIONS` requests across varied domain names.
3. **Configuration Drift:** Runtime configuration changes require invalidating container registry caches and re-running build pipelines.

---

## 2. Decision Outcome

We enforce **Dynamic Runtime Routing via an Nginx Reverse Proxy** inside the production frontend container (`frontend/nginx.conf`).

### Nginx Reverse Proxy Architecture

1. All client-side API requests from React use relative paths (`/api/...`) rather than absolute URLs.
2. Nginx serves static HTML/JS/CSS on port 80 and reverse-proxies all `/api/*` traffic upstream to the backend service:

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Benefits

- **Single Container Image for All Environments:** The exact same Docker image (`ghcr.io/.../civicpulse-frontend:sha-...`) runs unmodified in Docker Compose, staging KinD clusters, and production Kubernetes.
- **Zero CORS Friction:** In the browser's view, all API calls originate from the same host and port (`localhost:80` or `civicpulse.local`), eliminating cross-origin preflight latency and CORS misconfiguration vulnerabilities.
- **Dynamic Service Discovery:** In Kubernetes, ingress routing or internal service DNS seamlessly redirects `/api` requests without client bundle re-compilation.
