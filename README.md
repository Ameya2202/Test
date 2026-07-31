# OpsSwarm

Resilient multi-agent incident-triage application.

OpsSwarm accepts a production incident (logs, metrics, deployments, and configuration changes), runs a durable investigation pipeline across specialized agents, and produces a cited incident report with a full audit trail.

---

## Project Overview

OpsSwarm coordinates six deterministic agent roles through an explicit directed-graph orchestrator:

1. **Evidence Validator** — validates incident evidence before investigation
2. **Logs Analyst**, **Metrics Analyst**, **Deployment Analyst** — run concurrently
3. **Skeptic / Critic** — identifies contradictions and unsupported claims
4. **Report Synthesizer** — produces the final cited incident report

Every run, step, attempt, event, and agent output is persisted in SQLite. The React UI streams live pipeline events over Server-Sent Events (SSE).

Official execution uses a deterministic `ScriptedModelClient` so results are reproducible. No external AI API calls are made by default.

---

## Features

| Feature | Status |
|---|---|
| Explicit pipeline state machine / directed graph | Implemented |
| Concurrent investigation agents with configurable concurrency | Implemented |
| Durable persistence (runs, steps, attempts, events, outputs) | Implemented |
| Exponential backoff retries for transient failures | Implemented |
| Step timeouts and run cancellation | Implemented |
| Zod schema validation of agent outputs | Implemented |
| One repair call on invalid structured output | Implemented |
| Partial reports when an investigation agent fails permanently | Implemented |
| Restart recovery for unfinished runs | Implemented |
| Idempotent run creation | Implemented |
| SSE event streaming to the UI | Implemented |
| Token usage, duration, attempts, and status audit fields | Implemented |
| Scenario-driven deterministic fixtures | Implemented |
| React investigation dashboard | Implemented |
| Docker / Docker Compose packaging | Implemented |
| Authentication / multi-user tenancy | **Not implemented** |
| Real LLM provider integration in UI | **Not implemented** (optional `ModelClient` interface only) |
| Custom free-form incident editor in UI | **Not implemented** (scenario fixtures only) |
| Run history browser in UI | **Not implemented** (`GET /api/runs` exists; UI does not list past runs) |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Runtime | Node.js 24 LTS (pinned `.nvmrc` → `24.18.1`) |
| Language | TypeScript (strict) |
| Package manager | pnpm workspaces (`pnpm@10.33.3`) |
| Backend | Fastify 5 |
| Frontend | React 19 + Vite 7 |
| Database | SQLite via better-sqlite3 |
| ORM | Drizzle ORM |
| Validation | Zod |
| Streaming | Server-Sent Events |
| Unit / integration tests | Vitest |
| Browser tests | Playwright |
| Lint / format | ESLint 9 + Prettier |
| Containers | Docker multi-stage + Docker Compose + nginx |

---

## Folder Structure

```
opsswarm/
├── packages/
│   ├── shared/                 # Schemas, ModelClient, ScriptedModelClient, fixtures
│   ├── server/                 # Fastify API, orchestrator, SQLite persistence
│   └── web/                    # React UI + Playwright e2e
├── deploy/
│   └── nginx.conf              # Compose web reverse proxy
├── docs/                       # Project documentation (this set)
├── screenshots/                # Screenshot placeholders
├── data/                       # Local SQLite files (gitignored)
├── Dockerfile
├── docker-compose.yml
├── ARCHITECTURE.md             # Legacy short architecture note
├── Architecture.md             # Full architecture document
├── README.md
├── package.json
├── pnpm-workspace.yaml
└── tsconfig.base.json
```

---

## Project Architecture Summary

```
Browser (React / Vite)
        │  REST + SSE
        ▼
Fastify API  ──► RunRepository (SQLite)
        │
        ▼
PipelineOrchestrator (state machine)
        │
        ├── ScriptedModelClient (deterministic fixtures)
        └── Agents: validator → analysts → critic → synthesizer
```

Persistence is the source of truth. The orchestrator emits events that are both stored and streamed to the UI. On process restart, unfinished `pending` / `running` runs are resumed.

See [Architecture.md](./Architecture.md) for diagrams and design decisions.

---

## Prerequisites

- **Node.js** ≥ 24.0.0 (recommended: `24.18.1` via `.nvmrc`)
- **pnpm** 10.33.3 (via Corepack)
- **Git**
- **SQLite** (embedded via `better-sqlite3`; no separate server required)
- Optional: **Docker** + **Docker Compose** for containerized runs

---

## Installation Steps

```bash
git clone <repository-url>
cd opsswarm
nvm use          # or install Node 24
corepack enable
pnpm install --frozen-lockfile
pnpm build
```

Detailed steps: [docs/InstallationGuide.md](./docs/InstallationGuide.md)

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `./data/opsswarm.db` | SQLite database path (`:memory:` supported in tests) |
| `PORT` | `3001` | API listen port |
| `HOST` | `0.0.0.0` | API bind host |
| `BACKOFF_BASE_MS` | `25` | Base delay for exponential retry backoff |
| `NODE_ENV` | _(unset)_ | `test` disables logger noise and auto-resume |
| `VITE_API_PROXY` | `http://127.0.0.1:3001` | Vite proxy target for `/api` |
| `E2E_PORT` / `E2E_API_PORT` | `4173` / `3001` | Playwright ports |
| `CI` | _(unset)_ | Playwright CI behavior |

No `.env` file is required for local development. See [docs/ConfigurationGuide.md](./docs/ConfigurationGuide.md).

---

## Running the Backend

```bash
pnpm --filter @opsswarm/server dev
# → http://0.0.0.0:3001
# Health: GET /api/health → { "ok": true }
```

Production-style start after build:

```bash
pnpm --filter @opsswarm/server build
pnpm --filter @opsswarm/server start
```

---

## Running the Frontend

```bash
pnpm --filter @opsswarm/web dev
# → http://localhost:5173  (proxies /api → API)
```

Or run both together:

```bash
pnpm dev
```

---

## Running Tests

```bash
pnpm lint
pnpm typecheck
pnpm test          # shared + server Vitest suites
pnpm build
pnpm test:e2e      # Playwright smoke tests (requires Chromium install)
```

See [docs/TestingGuide.md](./docs/TestingGuide.md).

---

## Common Commands

| Command | Description |
|---|---|
| `pnpm install --frozen-lockfile` | Install dependencies |
| `pnpm dev` | Start API + UI in watch mode |
| `pnpm build` | Build shared, server, and web |
| `pnpm lint` | ESLint (zero warnings allowed) |
| `pnpm typecheck` | TypeScript across packages |
| `pnpm test` | Unit / integration tests |
| `pnpm test:e2e` | Playwright browser tests |
| `pnpm format` | Prettier write |
| `docker compose up --build` | Run API + nginx UI via Compose |

---

## Screenshots

Place screenshots in [`screenshots/`](./screenshots/). Suggested captures (not checked in yet):

| File | Description |
|---|---|
| `screenshots/01-dashboard.png` | OpsSwarm launch panel + empty pipeline |
| `screenshots/02-pipeline-running.png` | Live step statuses during investigation |
| `screenshots/03-event-timeline.png` | SSE event timeline |
| `screenshots/04-incident-report.png` | Final cited report view |

> Screenshots are placeholders. Capture them from a local `pnpm dev` session when documenting releases.

---

## Known Limitations

- **Single-node only** — SQLite; no multi-process locking or horizontal scaling
- **Deterministic models only by default** — no shipping UI for real LLM providers
- **No authentication** — API is open; CORS allows all origins
- **Scenario-driven UI** — operators pick a fixture scenario; there is no custom incident form
- **No run-history UI** — past runs are available via `GET /api/runs` but not rendered in the web app
- **Drizzle migrate script is incomplete** — `pnpm db:migrate` references a missing `migrate.ts`; schema is bootstrapped with `CREATE TABLE IF NOT EXISTS` in `packages/server/src/db/client.ts`
- **`@fastify/static` is unused** — Compose serves the SPA through nginx, not Fastify
- **Step status `skipped` / event `step_skipped`** — defined in shared schemas but not emitted by the orchestrator

---

## Documentation Index

| Document | Description |
|---|---|
| [Architecture.md](./Architecture.md) | System design, layers, sequences |
| [docs/InstallationGuide.md](./docs/InstallationGuide.md) | Prerequisites and install |
| [docs/RunGuide.md](./docs/RunGuide.md) | How to run and verify |
| [docs/APIDocumentation.md](./docs/APIDocumentation.md) | REST + SSE API reference |
| [docs/DatabaseDesign.md](./docs/DatabaseDesign.md) | Tables, keys, indexes |
| [docs/Workflow.md](./docs/Workflow.md) | Incident lifecycle |
| [docs/AgentDocumentation.md](./docs/AgentDocumentation.md) | Agent roles and I/O |
| [docs/UIGuide.md](./docs/UIGuide.md) | UI sections |
| [docs/ConfigurationGuide.md](./docs/ConfigurationGuide.md) | Env vars and config files |
| [docs/TestingGuide.md](./docs/TestingGuide.md) | Test strategy |
| [docs/Troubleshooting.md](./docs/Troubleshooting.md) | Common failures |
| [docs/DeploymentGuide.md](./docs/DeploymentGuide.md) | Local / Docker / production notes |
| [docs/FutureEnhancements.md](./docs/FutureEnhancements.md) | Realistic next steps |
