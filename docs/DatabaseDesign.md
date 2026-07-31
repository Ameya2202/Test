# Database Design

OpsSwarm persists durable execution state in **SQLite**.

- Driver: `better-sqlite3`
- ORM definitions: `packages/server/src/db/schema.ts`
- Bootstrap DDL: `packages/server/src/db/client.ts` (`CREATE TABLE IF NOT EXISTS`)
- Default path: `./data/opsswarm.db` (override with `DATABASE_URL`)
- Pragmas: `journal_mode = WAL`, `foreign_keys = ON`

There is **no checked-in Drizzle migration history**. The `db:migrate` package script references `src/db/migrate.ts`, which is **not present**.

---

## Entity Relationship Overview

```text
runs 1───* steps 1───* step_attempts
  │
  └───* events
```

---

## Table: `runs`

Primary investigation unit.

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | TEXT | NO | — | **Primary key** (nanoid) |
| `idempotency_key` | TEXT | YES | NULL | Client idempotency key |
| `status` | TEXT | NO | — | Run status |
| `scenario_id` | TEXT | NO | — | Scripted scenario id |
| `incident_json` | TEXT | NO | — | Serialized incident payload |
| `options_json` | TEXT | NO | — | concurrency / timeout / retries |
| `report_json` | TEXT | YES | NULL | Final incident report JSON |
| `error_message` | TEXT | YES | NULL | Terminal error if any |
| `created_at` | TEXT | NO | — | ISO timestamp |
| `updated_at` | TEXT | NO | — | ISO timestamp |
| `started_at` | TEXT | YES | NULL | When execution started |
| `finished_at` | TEXT | YES | NULL | When execution finished |
| `cancel_requested` | INTEGER | NO | `0` | Boolean cancel flag |

### Keys and indexes

- **Primary key:** `id`
- **Unique index:** `runs_idempotency_key_uidx` on `idempotency_key`

> SQLite unique indexes allow multiple `NULL` idempotency keys.

### Status values (application-level)

`pending`, `running`, `completed`, `failed`, `cancelled`, `partial`

---

## Table: `steps`

One row per pipeline step for a run.

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | TEXT | NO | — | **Primary key** |
| `run_id` | TEXT | NO | — | FK → `runs.id` |
| `name` | TEXT | NO | — | Step name |
| `status` | TEXT | NO | — | Step status |
| `attempt` | INTEGER | NO | `0` | Current attempt count |
| `max_attempts` | INTEGER | NO | `3` | `maxRetries + 1` |
| `output_json` | TEXT | YES | NULL | Validated agent output |
| `error_message` | TEXT | YES | NULL | Last error |
| `token_prompt` | INTEGER | NO | `0` | Accumulated prompt tokens |
| `token_completion` | INTEGER | NO | `0` | Accumulated completion tokens |
| `duration_ms` | INTEGER | YES | NULL | Accumulated duration |
| `started_at` | TEXT | YES | NULL | First start time |
| `finished_at` | TEXT | YES | NULL | Terminal finish time |
| `created_at` | TEXT | NO | — | Created |
| `updated_at` | TEXT | NO | — | Updated |

### Keys and indexes

- **Primary key:** `id`
- **Foreign key:** `run_id` → `runs(id)`
- **Index:** `steps_run_id_idx` on `run_id`
- **Unique index:** `steps_run_name_uidx` on `(run_id, name)`

### Step names created for every run

`validate`, `logs_analyst`, `metrics_analyst`, `deployment_analyst`, `critic`, `synthesizer`

### Status values

`pending`, `running`, `succeeded`, `failed`, `timed_out`, `cancelled`  
(`skipped` exists in shared Zod enums but is unused in persistence paths today.)

---

## Table: `step_attempts`

Attempt-level audit, including repair calls.

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | TEXT | NO | — | **Primary key** |
| `step_id` | TEXT | NO | — | FK → `steps.id` |
| `attempt` | INTEGER | NO | — | Outer attempt number |
| `status` | TEXT | NO | — | Attempt status |
| `is_repair` | INTEGER | NO | `0` | Repair call flag |
| `input_json` | TEXT | YES | NULL | Attempt input snapshot |
| `output_json` | TEXT | YES | NULL | Raw/parsed output snapshot |
| `error_message` | TEXT | YES | NULL | Error text |
| `token_prompt` | INTEGER | NO | `0` | Prompt tokens for attempt |
| `token_completion` | INTEGER | NO | `0` | Completion tokens |
| `duration_ms` | INTEGER | YES | NULL | Attempt duration |
| `started_at` | TEXT | NO | — | Start time |
| `finished_at` | TEXT | YES | NULL | Finish time |

### Keys and indexes

- **Primary key:** `id`
- **Foreign key:** `step_id` → `steps(id)`
- **Index:** `step_attempts_step_id_idx` on `step_id`

---

## Table: `events`

Append-only pipeline timeline (SSE source of truth).

| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | TEXT | NO | — | **Primary key** |
| `run_id` | TEXT | NO | — | FK → `runs.id` |
| `type` | TEXT | NO | — | Event type |
| `step_name` | TEXT | YES | NULL | Related step |
| `attempt` | INTEGER | YES | NULL | Attempt number |
| `message` | TEXT | NO | — | Human-readable message |
| `payload_json` | TEXT | YES | NULL | Optional JSON payload |
| `created_at` | TEXT | NO | — | Event timestamp |

### Keys and indexes

- **Primary key:** `id`
- **Foreign key:** `run_id` → `runs(id)`
- **Index:** `events_run_id_idx` on `run_id`

### Event types (schema)

`run_created`, `run_started`, `run_completed`, `run_failed`, `run_cancelled`, `run_partial`, `step_started`, `step_succeeded`, `step_failed`, `step_retrying`, `step_timed_out`, `step_cancelled`, `step_skipped`, `event`

`step_skipped` is defined but **not emitted** by the orchestrator.

---

## Relationships Summary

| Parent | Child | Relationship |
|---|---|---|
| `runs` | `steps` | One-to-many |
| `runs` | `events` | One-to-many |
| `steps` | `step_attempts` | One-to-many |

Cascade deletes are **not** configured in the bootstrap SQL; cleanup is not implemented as an API.

---

## Storage Notes

- JSON payloads are stored as TEXT (`*_json` columns) and parsed in the repository
- Timestamps are ISO-8601 strings, not SQLite `DATETIME` affinity helpers
- Tests commonly use `DATABASE_URL=:memory:` or temporary file DBs for restart scenarios
