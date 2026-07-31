# Run Guide

How to start, build, and exercise OpsSwarm using the implemented scripts and API.

---

## How to Start the Backend

From the repository root (Node 24 + pnpm active):

```bash
pnpm --filter @opsswarm/server dev
```

This runs `tsx watch src/index.ts`.

Defaults:

- Host: `0.0.0.0` (`HOST`)
- Port: `3001` (`PORT`)
- Database: `./data/opsswarm.db` (`DATABASE_URL`)
- Auto-resume unfinished runs: **enabled** (unless `NODE_ENV=test`)

Health check:

```bash
curl http://127.0.0.1:3001/api/health
# {"ok":true}
```

---

## How to Start the Frontend

```bash
pnpm --filter @opsswarm/web dev
```

Vite serves the UI at **http://localhost:5173/** and proxies `/api` to `http://127.0.0.1:3001` (override with `VITE_API_PROXY`).

Start both packages together:

```bash
pnpm dev
```

---

## How to Build the Project

```bash
pnpm build
```

Order:

1. `@opsswarm/shared` → `tsc` to `dist/`
2. `@opsswarm/server` → `tsc` to `dist/`
3. `@opsswarm/web` → typecheck + `vite build` to `packages/web/dist/`

---

## How to Run a Production Build

### API

```bash
pnpm --filter @opsswarm/shared build
pnpm --filter @opsswarm/server build
DATABASE_URL=./data/opsswarm.db PORT=3001 pnpm --filter @opsswarm/server start
```

### Web (preview)

```bash
pnpm --filter @opsswarm/web build
pnpm --filter @opsswarm/web preview
# default preview port 4173; /api proxy configured in vite.config.ts
```

### Docker Compose (recommended packaged path)

```bash
docker compose up --build
```

- UI: http://localhost:8080
- API: http://localhost:3001

Details: [DeploymentGuide.md](./DeploymentGuide.md)

---

## How to Execute the Investigation Pipeline

### Via UI

1. Open http://localhost:5173/
2. Choose a scenario (for example `happy`)
3. Optionally set an idempotency key and concurrency limit
4. Click **Start run**
5. Watch pipeline nodes, event timeline, agent outputs, and the final report
6. Use **Cancel** during slow scenarios (for example `cancellation`)

### Via API

```bash
# Load fixture incident
INCIDENT=$(curl -s http://127.0.0.1:3001/api/scenarios/happy)

# Create run
curl -s -X POST http://127.0.0.1:3001/api/runs \
  -H 'Content-Type: application/json' \
  -d "$(node -e 'const s=JSON.parse(require("fs").readFileSync(0,"utf8")); process.stdout.write(JSON.stringify({incident:s.incident, options:{scenarioId:"happy"}}))' <<<"$INCIDENT")"
```

Poll:

```bash
curl -s http://127.0.0.1:3001/api/runs/<runId>
```

Stream events:

```bash
curl -N http://127.0.0.1:3001/api/runs/<runId>/stream
```

Cancel:

```bash
curl -s -X POST http://127.0.0.1:3001/api/runs/<runId>/cancel
```

Available scenario IDs:

`happy`, `partial_failure`, `retry`, `invalid_output`, `timeout`, `contradiction`, `cancellation`, `restart`, `duplicate`, `invalid_citation`

---

## How to Verify Successful Startup

| Check | Expected |
|---|---|
| `GET /api/health` | `{ "ok": true }` |
| `GET /api/scenarios` | JSON list including `happy` |
| UI loads | OpsSwarm brand + “Launch investigation” panel |
| Start `happy` run | All six steps reach `succeeded`; report appears |
| SSE timeline | Events such as `run_created`, `step_started`, `run_completed` |

Failure signals:

- UI cannot reach API → proxy / port forward / API not running
- Run stuck in `pending` → orchestrator did not start (check server logs)
- Immediate `failed` on analysts → incident evidence IDs do not match fixture citations (use `/api/scenarios/:id`)

---

## Related Documents

- [InstallationGuide.md](./InstallationGuide.md)
- [APIDocumentation.md](./APIDocumentation.md)
- [Workflow.md](./Workflow.md)
- [Troubleshooting.md](./Troubleshooting.md)
