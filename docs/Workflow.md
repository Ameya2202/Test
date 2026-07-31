# Workflow

Complete incident investigation lifecycle as implemented by OpsSwarm.

---

## Incident Creation

1. Client obtains an incident payload:
   - UI: `GET /api/scenarios/:id` then `POST /api/runs`
   - Direct API: post a full `CreateRunRequest`
2. Fastify validates the body with `CreateRunRequestSchema`.
3. If `idempotencyKey` matches an existing run, that run is returned (`200`) and **not** restarted.
4. Otherwise `RunRepository.createRun`:
   - Inserts a `runs` row (`status = pending`)
   - Creates six `steps` rows (`pending`)
   - Appends `run_created`
5. API calls `orchestrator.startRun(runId)` asynchronously and returns `201`.

There is **no separate “incident” table**. The incident document is stored as `runs.incident_json`.

---

## Pipeline Execution

On `startRun`:

1. Mark run `running` and emit `run_started` (if still `pending`)
2. Execute `validate`
3. Fan-out investigation agents with concurrency limit
4. Execute `critic`
5. Execute `synthesizer`
6. Persist report and terminal status (`completed` or `partial`)

```text
Incident
   ↓
Validate evidence
   ↓
┌───────────────┬────────────────┬──────────────────┐
│ Logs Analyst  │ Metrics Analyst│ Deployment Analyst│
└───────────────┴────────────────┴──────────────────┘
   ↓
Critic
   ↓
Synthesizer
   ↓
Incident report + audit trail
```

---

## Agent Orchestration

- Orchestrator is in-process (`PipelineOrchestrator`)
- Each step calls `ModelClient.generate` with role, scenarioId, attempt, repair flag, and context
- Outputs are schema-validated; analyst/synthesizer citations must reference known evidence IDs from the incident
- Step/attempt metrics (tokens, duration, status) are persisted

Default model adapter: `ScriptedModelClient` (fixtures). Real LLM providers are **not wired** in the default app.

---

## Evidence Collection

Evidence is **supplied in the incident input**, not scraped live from production systems.

Sources in `IncidentInput`:

- `logs[]` (`evidenceId`, timestamp, level, message, …)
- `metrics[]`
- `deployments[]`
- `configChanges[]`

`collectEvidenceIds(incident)` builds the allow-list used during validation of agent outputs.

---

## Critic Validation

After investigation (including partial failures):

- Critic receives analyst outputs + `failedAgents` in model context
- Output schema: contradictions, unsupported claims, notes
- Critic failure does **not** stop the synthesizer; the critic is added to `failedAgents`

---

## Synthesizer

Produces `IncidentReport`:

- Executive summary
- Most likely root cause
- Confidence score
- Supporting / contradictory evidence (with citations)
- Immediate actions and longer-term remediation
- Unknowns / follow-ups
- `partial` + `failedAgents`

If synthesizer fails after retries, the run status becomes `failed`.

---

## Final Report

Stored on `runs.report_json` and returned by `GET /api/runs/:id`.

UI renders the report sections when present (`data-testid="incident-report"`).

Terminal statuses:

| Status | Meaning |
|---|---|
| `completed` | Pipeline finished; no investigation agent hard-failures tracked |
| `partial` | Report produced but one or more investigation agents failed/timed out |
| `failed` | Validator or synthesizer could not complete successfully |
| `cancelled` | User/API cancellation |

---

## Retry Flow

For each step:

1. Increment attempt (up to `maxAttempts`)
2. Emit `step_started` or `step_retrying`
3. On retry, sleep `BACKOFF_BASE_MS * 2^(attempt-2)`
4. Call model (with timeout)
5. If output invalid → **one repair call**
6. If transient error (`retryable: true`) → retry while attempts remain
7. If permanent / timeout / cancel → terminal step status

Scenario `retry` demonstrates logs analyst failing twice then succeeding.

---

## Failure Handling

| Case | Behavior |
|---|---|
| Validator fails | Run `failed` immediately |
| Metrics permanent failure (`partial_failure`) | Continue; run likely `partial` |
| Malformed JSON (`invalid_output`) | Repair once, then continue |
| Bad citations (`invalid_citation`) | Treated as invalid output → repair |
| Timeout (`timeout`) | Step `timed_out`; continue with partial path |
| Contradiction (`contradiction`) | Critic/report capture conflicts; still `completed` |

---

## Cancellation

1. `POST /api/runs/:id/cancel` or UI **Cancel**
2. Repository sets `cancel_requested` and emits `run_cancelled`
3. Orchestrator aborts the run’s `AbortController`
4. Pending/running steps become `cancelled`
5. Run status becomes `cancelled`

Scenario `cancellation` uses delayed investigation agents to make cancel observable.

---

## Restart Recovery

1. API boots with `autoResume: true` (non-test)
2. `resumeUnfinishedRuns()` loads `pending`/`running` runs
3. For each, `startRun` re-enters the graph
4. Steps already `succeeded` / `failed` / `timed_out` are skipped

Limitation: an interrupted in-flight model call is not resumed mid-request; the step is re-attempted according to persisted counters / skip rules. Scripted attempt counters reset per process.

Scenario `restart` exists for integration testing this path.

---

## Related Documents

- [AgentDocumentation.md](./AgentDocumentation.md)
- [Architecture.md](../Architecture.md)
- [APIDocumentation.md](./APIDocumentation.md)
