# Configuration Guide

Configuration sources that exist in the OpsSwarm repository today.

---

## Environment Variables

| Variable | Default | Consumed by | Purpose |
|---|---|---|---|
| `DATABASE_URL` | `./data/opsswarm.db` | server `client.ts`, `app.ts`, `index.ts`, drizzle config | SQLite path or `:memory:` |
| `PORT` | `3001` | server `index.ts` | HTTP listen port |
| `HOST` | `0.0.0.0` | server `index.ts` | HTTP bind address |
| `BACKOFF_BASE_MS` | `25` | server `app.ts` → orchestrator | Retry backoff base |
| `NODE_ENV` | _(unset)_ | server `app.ts` | `test` disables Fastify logger + auto-resume |
| `VITE_API_PROXY` | `http://127.0.0.1:3001` | `packages/web/vite.config.ts` | Dev/preview proxy target for `/api` |
| `E2E_PORT` | `4173` | Playwright config | UI preview port for e2e |
| `E2E_API_PORT` | `3001` | Playwright config | API port for e2e |
| `CI` | _(unset)_ | Playwright config | Stricter e2e settings |

Docker Compose / Dockerfile additionally set:

- `NODE_ENV=production` (API image)
- `DATABASE_URL=/data/opsswarm.db`
- `PORT=3001`, `HOST=0.0.0.0`

### Not present

- No committed `.env` / `.env.example`
- No secrets manager integration
- No `LOG_LEVEL` variable (Fastify default logger only)
- No feature-flag framework

---

## Configuration Files

| File | Role |
|---|---|
| `package.json` | Workspace scripts, engines, pnpm build allow-list |
| `pnpm-workspace.yaml` | `packages/*` |
| `.nvmrc` | `24.18.1` |
| `tsconfig.base.json` | Shared strict TS options |
| `eslint.config.js` | Flat ESLint config |
| `prettier.config.js` | Formatting |
| `packages/server/drizzle.config.ts` | Drizzle Kit schema path / sqlite dialect |
| `packages/*/vitest.config.ts` | Unit test runner |
| `packages/web/vite.config.ts` | Dev server, preview, `/api` proxy |
| `packages/web/playwright.config.ts` | e2e webServers and browser project |
| `Dockerfile` | Multi-stage api/web images |
| `docker-compose.yml` | Local container orchestration |
| `deploy/nginx.conf` | SPA + `/api` reverse proxy |

### Per-run options (API body, not env)

Posted under `options` on `POST /api/runs`:

- `concurrencyLimit` (1–10, default 3)
- `stepTimeoutMs` (≥100, default 10000)
- `maxRetries` (0–5, default 2)
- `scenarioId` (optional string)

---

## Ports

| Service | Port | Notes |
|---|---|---|
| Fastify API | `3001` | Default |
| Vite dev UI | `5173` | Proxies `/api` |
| Vite preview / e2e UI | `4173` | Used by Playwright |
| Compose nginx UI | `8080` → container `80` | Proxies `/api` to `api:3001` |
| Compose API | `3001` | Published to host |

---

## Database Path

| Context | Path |
|---|---|
| Local default | `./data/opsswarm.db` (relative to process cwd) |
| Docker API | `/data/opsswarm.db` (Compose volume `opsswarm-data`) |
| Playwright e2e | `./data/e2e.db` |
| Unit tests | often `:memory:` or temp file |

Directory is created automatically when using a filesystem path.

---

## Logging

- Fastify request logging when `NODE_ENV !== 'test'`
- Pipeline audit trail via `events` table + SSE
- No file log sinks, log rotation, or external APM configuration in-repo

---

## Model / Scenario Configuration

Scripts live in code: `packages/shared/src/fixtures.ts` (`buildScenarioScripts`, `SCENARIO_INCIDENTS`).

There is **no** runtime config file for swapping LLM providers. The default app always constructs `ScriptedModelClient`.

---

## Related Documents

- [InstallationGuide.md](./InstallationGuide.md)
- [DeploymentGuide.md](./DeploymentGuide.md)
- [Troubleshooting.md](./Troubleshooting.md)
