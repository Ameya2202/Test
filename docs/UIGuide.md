# UI Guide

OpsSwarm ships a **single-page** React application (`packages/web/src/App.tsx`). There is no client-side router and no multi-page navigation.

This guide maps documentation names to **actual UI sections**. Where a requested screen is not implemented, that is called out explicitly.

---

## Application Shell

- Brand header: **OpsSwarm**
- Tagline: “Multi-agent incident triage with durable orchestration”
- When a run exists, a status indicator shows the run status (`pending`, `running`, `completed`, `partial`, `failed`, `cancelled`)

---

## Dashboard

**Partially applicable.** The page functions as an investigation dashboard (graph + timeline + outputs + report), not a multi-widget ops homepage.

There are **no** KPI cards, service maps, or alert inbox widgets.

---

## Investigation Form / Launch Panel

Aside panel titled **Launch investigation** (`controls`).

Fields:

| Control | Test id / notes |
|---|---|
| Scenario select | `data-testid="scenario-select"` |
| Idempotency key | `data-testid="idempotency-input"` (optional) |
| Concurrency limit | number input 1–10 (default 3) |
| Start run | `data-testid="start-run"` |
| Cancel | `data-testid="cancel-run"` |
| Run id display | `data-testid="run-id"` |

On start, the UI:

1. Loads the scenario incident from `/api/scenarios/:id`
2. Posts `/api/runs`
3. Subscribes to `/api/runs/:id/stream`
4. Refreshes run state via `/api/runs/:id`

Special case: selecting scenario `timeout` sets `stepTimeoutMs: 500` for easier demos.

---

## Scenario Selection

Implemented via the scenario dropdown populated from `GET /api/scenarios`.

Operators do **not** author free-form incidents in the UI. Custom incident editing is **not implemented**.

---

## Evidence Panel

**Not implemented** as a dedicated panel.

Evidence exists inside the incident fixture used for the run and appears indirectly inside agent JSON outputs / report citations. There is no standalone evidence browser.

---

## Pipeline Status

Section **Pipeline graph** (`data-testid="pipeline-graph"`).

Nodes (`data-testid="node-<step>"`):

- Evidence Validator (`validate`)
- Logs Analyst / Metrics Analyst / Deployment Analyst
- Skeptic / Critic
- Report Synthesizer

Each node shows:

- Live status pill
- Attempt `current/max`
- Duration (ms) when available
- Simulated token total when available

Visual states: pending, active/running, done/succeeded, bad/failed|timed_out|cancelled.

---

## Recent Runs

**Not implemented in the UI.**

The API exposes `GET /api/runs`, but the web app does not list historical runs. Only the active session’s current run is shown.

---

## Event Timeline

Section **Event timeline** (`data-testid="event-timeline"`).

Shows SSE (and refreshed) events with timestamp, type, optional step name, and message. Empty state: “Events will stream here via SSE.”

---

## Agent Outputs

Section **Agent outputs**.

For each step, a block shows status and a JSON/preformatted output (`data-testid="output-<stepName>"`), or the error message if no output.

---

## Report View

Section **Incident report** (`data-testid="incident-report"`).

Rendered fields when `run.report` exists:

1. Executive summary
2. Most likely root cause + confidence %
3. Supporting evidence (with evidence IDs)
4. Contradictory evidence
5. Immediate actions
6. Longer-term remediation
7. Unknowns & follow-ups
8. Partial-report note listing `failedAgents` when applicable

Empty state: “Final report appears after synthesizer completes.”

---

## Responsive Behaviour

CSS switches the two-column layout to a single column below 900px width. No separate mobile app is provided.

---

## Styling Notes

- Fonts: Sora (display) + IBM Plex Mono
- Dark atmospheric gradient background
- Motion: rise/fade/pulse animations for presence

---

## Related Documents

- [RunGuide.md](./RunGuide.md)
- [APIDocumentation.md](./APIDocumentation.md)
- [Workflow.md](./Workflow.md)
