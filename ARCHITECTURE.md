# OpsSwarm architecture

## Pipeline as a directed graph

```
validate
   │
   ├──────────────┬──────────────┐
   ▼              ▼              ▼
logs_analyst  metrics_analyst  deployment_analyst
   │              │              │
   └──────────────┴──────────────┘
                  │
                  ▼
                critic
                  │
                  ▼
             synthesizer
```

The orchestrator (`packages/server/src/orchestrator/pipeline.ts`) is an explicit state machine:

| Phase | Behavior |
|---|---|
| `validate` | Single step; failure fails the run |
| investigate | Fan-out with `mapPool` and configurable concurrency |
| `critic` | Fan-in over successful analyst outputs |
| `synthesizer` | Produces the final cited report |

Terminal run statuses: `completed`, `partial`, `failed`, `cancelled`.

## Persistence & audit trail

SQLite via better-sqlite3 + Drizzle schema:

- `runs` — incident payload, options, status, report, cancel flag, idempotency key
- `steps` — per-agent status, attempts, tokens, duration, output
- `step_attempts` — each try (including repair calls)
- `events` — append-only timeline consumed by SSE and the UI

## Resilience

1. **Retries** — transient model errors retry with exponential backoff (`backoffBaseMs * 2^n`).
2. **Timeouts** — each attempt wrapped in `withTimeout` + `AbortSignal`.
3. **Cancellation** — `cancelRequested` persisted; in-process `AbortController` aborts waits; pending/running steps marked `cancelled`.
4. **Schema validation** — Zod schemas for every agent role; invalid JSON / schema / unsupported citations trigger **one repair call**, then the attempt fails.
5. **Partial success** — permanent failure of an investigation agent does not stop critic/synthesizer; run ends as `partial` with `failedAgents`.
6. **Idempotency** — unique `idempotency_key` on `runs`; duplicate `POST /api/runs` returns the existing run without restarting.
7. **SSE** — `/api/runs/:id/stream` replays persisted events then tails new ones.

## Restart recovery

On API boot (`autoResume: true`):

1. Load runs with status `pending` or `running`.
2. Re-enter `PipelineOrchestrator.startRun`.
3. Steps already `succeeded` / `failed` / `timed_out` are not re-executed.
4. Remaining steps continue with the same `ScriptedModelClient` scripts.

Limitation: in-flight model calls that were mid-flight at crash are not resumed mid-HTTP; the step is re-attempted from the next attempt counter state persisted in SQLite. Scripted counters reset per process, so restart tests use scenarios that still produce valid outputs on fresh counters after durable step skip logic.

## Determinism

`ModelClient.generate` is the only model boundary. Tests and default runtime inject `ScriptedModelClient` keyed by `scenarioId:role`. No network AI providers are called.

## Assumptions

- Single-node process; SQLite is sufficient for the benchmark.
- Investigation concurrency defaults to 3 (all three analysts).
- Token usage is simulated by the scripted client.
- A real LLM provider can implement `ModelClient` but is out of scope for scoring.

## UI

React + Vite dashboard showing:

- Pipeline graph with live step statuses
- SSE event timeline
- Per-agent outputs (tokens, attempts, duration)
- Final incident report with evidence citations
- Start / cancel controls and scenario picker
