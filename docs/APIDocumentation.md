# API Documentation

REST and SSE API reference for `@opsswarm/server`. All routes are defined in `packages/server/src/app.ts`.

Base URL (local default): `http://127.0.0.1:3001`

CORS: enabled for all origins (`@fastify/cors` with `origin: true`).

Authentication: **not implemented**.

---

## `GET /api/health`

| | |
|---|---|
| **Purpose** | Liveness probe |
| **Request** | None |
| **Response** | `{ "ok": true }` |
| **Status codes** | `200` |

---

## `GET /api/scenarios`

| | |
|---|---|
| **Purpose** | List fixture scenario IDs |
| **Request** | None |
| **Response** | `{ "scenarios": string[] }` |
| **Status codes** | `200` |

Example response values include: `happy`, `partial_failure`, `retry`, `invalid_output`, `timeout`, `contradiction`, `cancellation`, `restart`, `duplicate`, `invalid_citation`.

---

## `GET /api/scenarios/:id`

| | |
|---|---|
| **Purpose** | Fetch a scenario’s incident fixture |
| **Request** | Path param `id` |
| **Response** | `{ "id": string, "incident": IncidentInput }` |
| **Status codes** | `200`, `404` `{ "error": "scenario not found" }` |

---

## `GET /api/pipeline/graph`

| | |
|---|---|
| **Purpose** | Static pipeline graph descriptor for UIs |
| **Request** | None |
| **Response** | `{ "nodes": [...], "edges": [...] }` |
| **Status codes** | `200` |

Nodes: `validate`, `logs_analyst`, `metrics_analyst`, `deployment_analyst`, `critic`, `synthesizer`.

---

## `GET /api/runs`

| | |
|---|---|
| **Purpose** | List all runs (oldest first) |
| **Request** | None |
| **Response** | `{ "runs": Run[] }` |
| **Status codes** | `200` |

> The React UI does **not** currently render this list.

---

## `POST /api/runs`

| | |
|---|---|
| **Purpose** | Create and start an investigation run (idempotent when key provided) |
| **Request body** | See below |
| **Status codes** | `201` created, `200` idempotent replay, `400` validation error |

### Request

```json
{
  "incident": {
    "serviceName": "checkout-api",
    "severity": "SEV2",
    "alertDescription": "...",
    "occurredAt": "2026-07-30T10:15:00.000Z",
    "logs": [],
    "metrics": [],
    "deployments": [],
    "configChanges": [],
    "scenarioId": "happy"
  },
  "idempotencyKey": "optional-key",
  "options": {
    "concurrencyLimit": 3,
    "stepTimeoutMs": 10000,
    "maxRetries": 2,
    "scenarioId": "happy"
  }
}
```

Validated by `CreateRunRequestSchema` (`@opsswarm/shared`).

Defaults when `options` omitted:

- `concurrencyLimit`: `3`
- `stepTimeoutMs`: `10000`
- `maxRetries`: `2`
- `scenarioId`: from `options.scenarioId` → `incident.scenarioId` → `"happy"`

### Response (`201`)

```json
{
  "run": { "...": "serialized run" },
  "steps": [ { "...": "step records" } ]
}
```

### Response (`200` idempotent replay)

```json
{
  "run": { "...": "existing run" },
  "steps": [ ],
  "idempotentReplay": true,
  "created": false
}
```

On idempotent replay the existing run is **not** restarted.

### Error (`400`)

```json
{ "error": { /* Zod flatten() */ } }
```

---

## `GET /api/runs/:id`

| | |
|---|---|
| **Purpose** | Fetch run + steps + events |
| **Request** | Path param `id` |
| **Response** | `{ "run": Run, "steps": Step[], "events": PipelineEvent[] }` |
| **Status codes** | `200`, `404` `{ "error": "run not found" }` |

### Serialized `run` fields

`id`, `idempotencyKey`, `status`, `scenarioId`, `incident`, `options`, `report`, `errorMessage`, `createdAt`, `updatedAt`, `startedAt`, `finishedAt`, `cancelRequested`

### Run `status` values

`pending` | `running` | `completed` | `failed` | `cancelled` | `partial`

---

## `POST /api/runs/:id/cancel`

| | |
|---|---|
| **Purpose** | Request cancellation of an in-flight run |
| **Request** | Path param `id` |
| **Response** | `{ "run": Run }` |
| **Status codes** | `200`, `404` |

Sets `cancelRequested` and aborts the in-process AbortController. Terminal runs are left unchanged.

---

## `GET /api/runs/:id/events`

| | |
|---|---|
| **Purpose** | List persisted pipeline events for a run |
| **Request** | Path param `id` |
| **Response** | `{ "events": PipelineEvent[] }` |
| **Status codes** | `200`, `404` |

### Event object

```json
{
  "id": "…",
  "runId": "…",
  "type": "step_started",
  "stepName": "logs_analyst",
  "attempt": 1,
  "message": "Starting logs_analyst",
  "payload": {},
  "createdAt": "2026-07-30T10:15:01.000Z"
}
```

---

## `GET /api/runs/:id/stream`

| | |
|---|---|
| **Purpose** | Server-Sent Events stream of pipeline events |
| **Request** | Path param `id` |
| **Response** | `text/event-stream` |
| **Status codes** | `200` (hijacked stream), `404` before hijack |

Behavior:

1. Replays all persisted events for the run
2. Tails new orchestrator events for that `runId`
3. Sends comment heartbeats every 15 seconds (`: heartbeat`)

SSE framing:

```text
id: <eventId>
event: <type>
data: <json PipelineEvent>
```

---

## Common Types (conceptual)

### `IncidentInput`

`serviceName`, `severity` (`SEV1`–`SEV4`), `alertDescription`, `occurredAt`, `logs[]`, `metrics[]`, `deployments[]`, `configChanges[]`, optional `scenarioId`.

Evidence items each include an `evidenceId` used for citation validation.

### `IncidentReport` (on completed/partial runs)

`executiveSummary`, `mostLikelyRootCause`, `confidenceScore`, `supportingEvidence[]`, `contradictoryEvidence[]`, `recommendedImmediateActions[]`, `longerTermRemediation[]`, `unknownsAndFollowUps[]`, `partial`, `failedAgents[]`.

---

## Not Implemented

- OpenAPI / Swagger UI
- Authentication headers or API keys
- Pagination / filtering on `GET /api/runs`
- WebSocket transport
- Multipart uploads for evidence bundles
