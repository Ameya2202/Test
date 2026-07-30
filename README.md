# OpsSwarm

Resilient multi-agent incident-triage application.

## What it does

OpsSwarm accepts a production incident (logs, metrics, deployments, config changes) and runs an explicit pipeline:

1. **Evidence validator**
2. **Logs / Metrics / Deployment analysts** (concurrent, concurrency-limited)
3. **Skeptic/critic** (contradictions & unsupported claims)
4. **Report synthesizer** (cited incident report)

Every run, step, attempt, event, and output is persisted in SQLite. The UI streams live pipeline events over Server-Sent Events.

## Quick start

Requirements: **Node.js 24+** and **pnpm 10+**.

```bash
pnpm install --frozen-lockfile
pnpm build
pnpm --filter @opsswarm/server dev   # API on :3001
pnpm --filter @opsswarm/web dev      # UI on :5173 (proxies /api)
```

Or with Docker Compose:

```bash
docker compose up --build
```

Open http://localhost:5173 (dev) or http://localhost:8080 (compose).

## Verification

```bash
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for state machine design, restart recovery, retries, and limitations.

## Deterministic models

Official runs use `ScriptedModelClient` (no external AI calls). Scenarios live in `@opsswarm/shared` fixtures:

| Scenario | Behavior |
|---|---|
| `happy` | All agents succeed |
| `partial_failure` | Metrics analyst fails permanently |
| `retry` | Logs analyst fails twice, then succeeds |
| `invalid_output` | Deployment analyst returns malformed JSON once (repaired) |
| `timeout` | Logs analyst exceeds deadline |
| `contradiction` | Logs vs deployment disagreement |
| `cancellation` | Slow parallel agents for cancel testing |
| `restart` | Slow investigation for resume testing |
| `duplicate` | Idempotency key demos |
| `invalid_citation` | Unsupported evidence ID repaired |

## API sketch

- `POST /api/runs` — create run (`idempotencyKey` optional)
- `GET /api/runs/:id` — run + steps + events
- `POST /api/runs/:id/cancel` — request cancellation
- `GET /api/runs/:id/stream` — SSE event stream
- `GET /api/pipeline/graph` — static graph descriptor
- `GET /api/scenarios` — fixture scenarios
