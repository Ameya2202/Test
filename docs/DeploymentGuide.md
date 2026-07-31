# Deployment Guide

Deployment options supported by the OpsSwarm repository.

---

## Local Deployment

### Development

```bash
pnpm install --frozen-lockfile
pnpm --filter @opsswarm/shared build
pnpm dev
```

- API: `http://127.0.0.1:3001`
- UI: `http://localhost:5173`

### Local production-like (without Docker)

```bash
pnpm build
DATABASE_URL=./data/opsswarm.db PORT=3001 HOST=0.0.0.0 \
  pnpm --filter @opsswarm/server start

# separate process
pnpm --filter @opsswarm/web preview --host 0.0.0.0 --port 4173
```

Preview proxies `/api` using `VITE_API_PROXY` / default `http://127.0.0.1:3001`.

> Serving the web `dist/` from Fastify is **not implemented** (`@fastify/static` is unused).

---

## Docker Deployment

### Images

`Dockerfile` multi-stage targets:

| Target | Contents |
|---|---|
| `api` | Node 24 + built workspace; runs `@opsswarm/server start` |
| `web` | nginx 1.27 Alpine + `packages/web/dist` + `deploy/nginx.conf` |

### Compose

```bash
docker compose up --build
```

Services:

| Service | Host port | Notes |
|---|---|---|
| `api` | `3001` | `DATABASE_URL=/data/opsswarm.db`, volume `opsswarm-data` |
| `web` | `8080` → `80` | nginx proxies `/api/` to `http://api:3001/api/` |

Verify:

```bash
curl http://127.0.0.1:3001/api/health
curl -I http://127.0.0.1:8080/
```

SSE note: nginx config disables proxy buffering and sets a long read timeout for streaming suitability.

---

## Production Deployment

The repository provides a **baseline** container packaging, not a full production platform.

### What is included

- Multi-stage Docker builds
- Compose wiring for API + static UI
- Durable SQLite volume for a single API instance
- Deterministic scripted model client (safe default for demos/benchmarks)

### What you must add for real production

These are **not implemented** in-repo:

- TLS termination / certificate management beyond whatever your ingress provides
- Authentication and authorization
- Managed backups for SQLite (or migration to Postgres)
- Horizontal scaling / multi-instance locking
- Real LLM provider credentials and rate-limit controls
- Observability (metrics, tracing, centralized logs)
- CI/CD deploy pipelines / Kubernetes manifests
- Health-gated rolling updates

### Practical single-node production sketch

1. Build and run the `api` and `web` images behind your reverse proxy
2. Mount a persistent volume for `/data`
3. Restrict network access (API is currently open + permissive CORS)
4. Replace `ScriptedModelClient` with a hardened `ModelClient` only if required—and keep fixtures for tests
5. Monitor disk growth of SQLite and event history (no retention job ships today)

---

## Environment Checklist

| Item | Value |
|---|---|
| Node in images | `24.18.1-bookworm` |
| pnpm in images | `10.33.3` |
| API health | `GET /api/health` |
| UI entry (Compose) | `/` on port 8080 |
| DB path (Compose) | `/data/opsswarm.db` |

---

## Related Documents

- [ConfigurationGuide.md](./ConfigurationGuide.md)
- [RunGuide.md](./RunGuide.md)
- [Troubleshooting.md](./Troubleshooting.md)
- [FutureEnhancements.md](./FutureEnhancements.md)
