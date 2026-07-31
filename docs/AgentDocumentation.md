# Agent Documentation

OpsSwarm agents are **roles** invoked through the `ModelClient` interface. In the shipping application they are driven by `ScriptedModelClient` fixtures keyed as `` `${scenarioId}:${role}` ``.

There are no separate agent microservices. All agents execute inside `PipelineOrchestrator`.

---

## Shared Model Boundary

```ts
interface ModelClient {
  generate(request: ModelRequest): Promise<ModelResponse>;
}
```

`ModelRequest`: `role`, `scenarioId`, `prompt`, `attempt`, `repair`, optional `context`  
`ModelResponse`: `content` (JSON string), `tokenUsage`, optional `latencyMs`

---

## 1. Evidence Validator (`validator` / step `validate`)

| | |
|---|---|
| **Responsibilities** | Confirm incident evidence is usable before investigation |
| **Input** | Incident payload in prompt/context |
| **Output (`ValidatorOutput`)** | `{ valid, evidenceIds[], issues[] }` |
| **Dependencies** | None (first step) |
| **Failure behaviour** | Permanent failure fails the **entire run** |

---

## 2. Logs Analyst (`logs_analyst`)

| | |
|---|---|
| **Responsibilities** | Interpret log evidence; propose log-backed findings/hypotheses |
| **Input** | Incident (esp. `logs`) + validator context |
| **Output (`AnalystOutput`)** | `{ role, findings[], hypotheses[], evidenceIds[] }` |
| **Dependencies** | Successful (or completed) validate phase before fan-out |
| **Failure behaviour** | Permanent/timeout → step fails; pipeline **continues** (partial path) |
| **Citation rules** | Finding/evidence IDs must exist in the incident allow-list |

---

## 3. Metrics Analyst (`metrics_analyst`)

| | |
|---|---|
| **Responsibilities** | Interpret metric snapshots |
| **Input** | Incident metrics + shared context |
| **Output** | `AnalystOutput` with `role: "metrics_analyst"` |
| **Dependencies** | Same fan-out gate as other analysts |
| **Failure behaviour** | Same partial-continue semantics (`partial_failure` scenario) |

---

## 4. Deployment Analyst (`deployment_analyst`)

| | |
|---|---|
| **Responsibilities** | Interpret deployments and configuration changes |
| **Input** | Incident deployments/config changes |
| **Output** | `AnalystOutput` with `role: "deployment_analyst"` |
| **Dependencies** | Fan-out after validate |
| **Failure behaviour** | Partial-continue; `invalid_output` shows repair of malformed JSON |

---

## 5. Skeptic / Critic (`critic`)

| | |
|---|---|
| **Responsibilities** | Detect contradictions and unsupported conclusions across analyst outputs |
| **Input** | Successful analyst outputs + `failedAgents` |
| **Output (`CriticOutput`)** | `{ contradictions[], unsupportedClaims[], notes[] }` |
| **Dependencies** | Investigation phase finished (including partial failures) |
| **Failure behaviour** | Critic added to `failedAgents`; synthesizer still executes |

---

## 6. Report Synthesizer (`synthesizer`)

| | |
|---|---|
| **Responsibilities** | Produce the final cited incident report |
| **Input** | Analyst outputs, critic output (nullable), `failedAgents` |
| **Output (`IncidentReport`)** | Executive summary, root cause, confidence, evidence, actions, unknowns, partial flags |
| **Dependencies** | Critic step attempted |
| **Failure behaviour** | After retries exhausted → run `failed` |
| **Citation rules** | Supporting/contradictory evidence IDs must be known |

---

## Cross-Cutting Agent Behaviour

### Schema validation

Zod schemas in `@opsswarm/shared` validate every structured output.

### Repair

On invalid JSON, schema failure, or unsupported citations:

1. Emit an event noting repair
2. Call `generate` once with `repair: true` and prior error context
3. If still invalid, fail the attempt (retryable for outer retry loop)

### Tokens and duration

Scripted responses include simulated token usage. Orchestrator accumulates tokens/duration on steps and attempts.

### Determinism

Agents do **not** call external LLM APIs in the default configuration. Fixture scripts control success, delays, transient/permanent failures, invalid JSON, timeouts, and repairs.

---

## Scenario Matrix (fixture-level)

| Scenario | Notable agent behaviour |
|---|---|
| `happy` | All succeed |
| `partial_failure` | Metrics permanent failure |
| `retry` | Logs transient fail ×2 then success |
| `invalid_output` | Deployment invalid JSON → repair |
| `timeout` | Logs hangs beyond timeout |
| `contradiction` | Deployment vs logs conflict surfaced by critic |
| `cancellation` | Slow investigation for cancel demos |
| `restart` | Slow investigation for resume demos |
| `duplicate` | Happy scripts for idempotency demos |
| `invalid_citation` | Logs cites unknown ID → repair |

---

## Not Implemented

- Real provider adapters (OpenAI/Anthropic/etc.)
- Per-agent tool calling / retrieval plugins
- Human-in-the-loop approval gates
- Agent-to-agent messaging bus outside the orchestrator context object
