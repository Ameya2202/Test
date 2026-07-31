# Testing Guide

OpsSwarm’s verification surface as implemented in the repository.

---

## Test Commands

```bash
pnpm lint
pnpm typecheck
pnpm test          # @opsswarm/shared + @opsswarm/server
pnpm build
pnpm test:e2e      # Playwright via @opsswarm/web
```

Root `pnpm test` does **not** run Playwright. Web unit Vitest is configured with `--passWithNoTests` and currently has **no** component unit tests.

---

## Unit Tests

### `@opsswarm/shared` — `packages/shared/src/schemas.test.ts`

| Case | Asserts |
|---|---|
| Incident schema | `IncidentInputSchema` parses `baseIncident`; `collectEvidenceIds` includes `log-001` |
| Scripted retries | `retry:logs_analyst` fails twice (`retryable: true`) then succeeds |

Runner: Vitest (`packages/shared/vitest.config.ts`).

---

## Integration Tests

### `@opsswarm/server` — `packages/server/src/app.test.ts`

Uses Fastify `inject`, in-memory or temp SQLite, and `ScriptedModelClient`.

| Scenario covered | Assertion focus |
|---|---|
| `happy` | Run `completed`; all steps succeeded; report present |
| `partial_failure` | Run `partial`; metrics failed; `failedAgents` contains metrics |
| `retry` | Logs attempt count 3; `step_retrying` events |
| `invalid_output` | Deployment repaired; run completed |
| `timeout` | Logs `timed_out`; failedAgents includes logs |
| `contradiction` | Critic contradictions; report contradictory evidence |
| `cancellation` | Cancel mid-flight → `cancelled` |
| `duplicate` | Same idempotency key → `200` + `idempotentReplay` |
| `invalid_citation` | Repair removes unknown evidence id |
| `restart` | App restart + `resumeUnfinishedRuns` completes run |
| SSE-related | Persisted events include `run_created` via events endpoint |

Note: the SSE hijack stream itself is not fully asserted end-to-end in Vitest; events persistence is.

---

## End-to-End (Browser) Tests

### Playwright — `packages/web/e2e/smoke.spec.ts`

| Test | Flow |
|---|---|
| Happy path | Select `happy`, start run, wait for report + synthesizer `succeeded` |
| Cancellation | Select `cancellation`, start, cancel, expect cancelled status text |

Config starts:

1. Server via `tsx src/index.ts` with `DATABASE_URL=./data/e2e.db`
2. `vite preview` with `/api` proxy

Install browsers once:

```bash
pnpm --filter @opsswarm/web exec playwright install chromium
```

---

## Manual Testing

1. `pnpm dev`
2. Open http://localhost:5173/
3. Exercise scenarios from the dropdown
4. Confirm timeline events update live
5. Confirm cancel on `cancellation`
6. Optional: kill API mid-`restart` scenario and restart API to observe resume (advanced)

### Sample manual matrix

| Scenario | What to look for |
|---|---|
| `happy` | Full green pipeline + report confidence |
| `partial_failure` | Metrics node bad; report marked partial |
| `retry` | Retry events before logs success |
| `invalid_output` | Repair event; still completes |
| `timeout` | Logs timed out; partial/failedAgents |
| `contradiction` | Contradictory evidence section populated |
| `duplicate` + same idempotency key | Second start should reuse run (via API easiest) |

---

## Determinism Guidance

- Prefer `ScriptedModelClient` fixtures
- Do not introduce live LLM calls into official suites
- Prefer isolated DB per test (`:memory:` / unique file)
- Server vitest uses `fileParallelism: false` and `pool: 'forks'`

---

## Gaps (not implemented)

- Frontend component unit tests
- Load / chaos testing harness beyond fixture scenarios
- Contract tests / OpenAPI-generated clients
- Coverage gates in CI config (no CI workflow is defined in this repo snapshot)

---

## Related Documents

- [RunGuide.md](./RunGuide.md)
- [Workflow.md](./Workflow.md)
- [Troubleshooting.md](./Troubleshooting.md)
