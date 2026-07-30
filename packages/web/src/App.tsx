import { useEffect, useRef, useState } from 'react';
import {
  cancelRun,
  createRun,
  getRun,
  listScenarios,
  subscribeRunEvents,
  type IncidentReportDto,
  type PipelineEventDto,
  type RunDto,
  type StepDto,
} from './api';

const GRAPH_ORDER: Array<{ id: string; label: string; row: number }> = [
  { id: 'validate', label: 'Evidence Validator', row: 0 },
  { id: 'logs_analyst', label: 'Logs Analyst', row: 1 },
  { id: 'metrics_analyst', label: 'Metrics Analyst', row: 1 },
  { id: 'deployment_analyst', label: 'Deployment Analyst', row: 1 },
  { id: 'critic', label: 'Skeptic / Critic', row: 2 },
  { id: 'synthesizer', label: 'Report Synthesizer', row: 3 },
];

function StatusDot({ status }: { status: string }) {
  return (
    <span className="status-pill">
      <span className={`status-dot ${status}`} />
      {status}
    </span>
  );
}

function nodeClass(status?: string): string {
  if (!status || status === 'pending') return '';
  if (status === 'running') return 'active';
  if (status === 'succeeded') return 'done';
  if (['failed', 'timed_out', 'cancelled'].includes(status)) return 'bad';
  return '';
}

function ReportView({ report }: { report: IncidentReportDto }) {
  return (
    <div className="report" data-testid="incident-report">
      <section>
        <h3>Executive summary</h3>
        <p>{report.executiveSummary}</p>
      </section>
      <section>
        <h3>Most likely root cause</h3>
        <p>{report.mostLikelyRootCause}</p>
        <p className="evidence">Confidence: {(report.confidenceScore * 100).toFixed(0)}%</p>
      </section>
      <section>
        <h3>Supporting evidence</h3>
        <ul>
          {report.supportingEvidence.map((item) => (
            <li key={item.claim}>
              {item.claim}{' '}
              <span className="evidence">[{item.evidenceIds.join(', ')}]</span>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3>Contradictory evidence</h3>
        {report.contradictoryEvidence.length === 0 ? (
          <p className="empty">None</p>
        ) : (
          <ul>
            {report.contradictoryEvidence.map((item) => (
              <li key={item.description}>
                {item.description}{' '}
                <span className="evidence">[{item.evidenceIds.join(', ')}]</span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section>
        <h3>Immediate actions</h3>
        <ul>
          {report.recommendedImmediateActions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3>Longer-term remediation</h3>
        <ul>
          {report.longerTermRemediation.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </section>
      <section>
        <h3>Unknowns & follow-ups</h3>
        <ul>
          {report.unknownsAndFollowUps.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </section>
      {report.partial && (
        <p className="evidence">Partial report — failed agents: {report.failedAgents.join(', ')}</p>
      )}
    </div>
  );
}

export function App() {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [scenarioId, setScenarioId] = useState('happy');
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [concurrencyLimit, setConcurrencyLimit] = useState(3);
  const [run, setRun] = useState<RunDto | null>(null);
  const [steps, setSteps] = useState<StepDto[]>([]);
  const [events, setEvents] = useState<PipelineEventDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const unsubRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    void listScenarios().then((ids) => {
      setScenarios(ids);
      if (ids.includes('happy')) setScenarioId('happy');
      else if (ids[0]) setScenarioId(ids[0]);
    });
    return () => unsubRef.current?.();
  }, []);

  async function refresh(runId: string) {
    const data = await getRun(runId);
    setRun(data.run);
    setSteps(data.steps);
    setEvents(data.events);
  }

  async function onStart() {
    setError(null);
    setBusy(true);
    try {
      unsubRef.current?.();
      const created = await createRun({
        scenarioId,
        idempotencyKey: idempotencyKey || undefined,
        concurrencyLimit,
        stepTimeoutMs: scenarioId === 'timeout' ? 500 : 10_000,
      });
      setRun(created.run);
      setSteps(created.steps);
      setEvents([]);
      unsubRef.current = subscribeRunEvents(created.run.id, (event) => {
        setEvents((prev) => {
          if (prev.some((e) => e.id === event.id)) return prev;
          return [...prev, event];
        });
        void refresh(created.run.id);
      });
      await refresh(created.run.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onCancel() {
    if (!run) return;
    setBusy(true);
    try {
      await cancelRun(run.id);
      await refresh(run.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const stepMap = new Map(steps.map((s) => [s.name, s]));
  const rows = [0, 1, 2, 3];

  return (
    <div className="app-shell">
      <header className="brand-bar">
        <div>
          <h1 className="brand">
            Ops<span>Swarm</span>
          </h1>
          <p className="tagline">Multi-agent incident triage with durable orchestration</p>
        </div>
        {run && <StatusDot status={run.status} />}
      </header>

      <div className="layout">
        <aside className="panel">
          <h2>Launch investigation</h2>
          <div className="controls">
            <label>
              Scenario
              <select
                data-testid="scenario-select"
                value={scenarioId}
                onChange={(e) => setScenarioId(e.target.value)}
              >
                {scenarios.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Idempotency key
              <input
                data-testid="idempotency-input"
                value={idempotencyKey}
                onChange={(e) => setIdempotencyKey(e.target.value)}
                placeholder="optional"
              />
            </label>
            <label>
              Concurrency limit
              <input
                type="number"
                min={1}
                max={10}
                value={concurrencyLimit}
                onChange={(e) => setConcurrencyLimit(Number(e.target.value))}
              />
            </label>
            <div className="btn-row">
              <button
                className="btn btn-primary"
                data-testid="start-run"
                disabled={busy}
                onClick={() => void onStart()}
              >
                Start run
              </button>
              <button
                className="btn btn-danger"
                data-testid="cancel-run"
                disabled={busy || !run || ['completed', 'failed', 'cancelled', 'partial'].includes(run.status)}
                onClick={() => void onCancel()}
              >
                Cancel
              </button>
            </div>
            {error && <p className="evidence">{error}</p>}
            {run && (
              <p className="empty" data-testid="run-id">
                Run {run.id}
              </p>
            )}
          </div>
        </aside>

        <main style={{ display: 'grid', gap: 16 }}>
          <section className="panel" data-testid="pipeline-graph">
            <h2>Pipeline graph</h2>
            <div className="graph">
              {rows.map((row) => (
                <div key={row} className="graph-row">
                  {GRAPH_ORDER.filter((n) => n.row === row).map((node) => {
                    const step = stepMap.get(node.id);
                    return (
                      <div
                        key={node.id}
                        className={`graph-node ${nodeClass(step?.status)}`}
                        data-testid={`node-${node.id}`}
                        data-status={step?.status ?? 'pending'}
                      >
                        <div className="name">{node.label}</div>
                        <div className="meta">
                          <StatusDot status={step?.status ?? 'pending'} />
                          {step && (
                            <>
                              {' '}
                              · attempt {step.attempt}/{step.maxAttempts}
                              {step.durationMs != null ? ` · ${step.durationMs}ms` : ''}
                              {step.tokenPrompt + step.tokenCompletion > 0
                                ? ` · ${step.tokenPrompt + step.tokenCompletion} tok`
                                : ''}
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2>Event timeline</h2>
            <div className="timeline" data-testid="event-timeline">
              {events.length === 0 ? (
                <p className="empty">Events will stream here via SSE.</p>
              ) : (
                events.map((event) => (
                  <div key={event.id} className="event">
                    <div className="when">
                      {new Date(event.createdAt).toLocaleTimeString()} · {event.type}
                      {event.stepName ? ` · ${event.stepName}` : ''}
                    </div>
                    <div className="msg">{event.message}</div>
                  </div>
                ))
              )}
            </div>
          </section>

          <div className="split">
            <section className="panel">
              <h2>Agent outputs</h2>
              <div style={{ display: 'grid', gap: 10 }}>
                {steps.length === 0 ? (
                  <p className="empty">No agent output yet.</p>
                ) : (
                  steps.map((step) => (
                    <div key={step.id}>
                      <div className="meta" style={{ marginBottom: 4 }}>
                        {step.name} · <StatusDot status={step.status} />
                      </div>
                      <pre className="output-block" data-testid={`output-${step.name}`}>
                        {step.output
                          ? JSON.stringify(step.output, null, 2)
                          : step.errorMessage || '—'}
                      </pre>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section className="panel">
              <h2>Incident report</h2>
              {run?.report ? (
                <ReportView report={run.report} />
              ) : (
                <p className="empty">Final report appears after synthesizer completes.</p>
              )}
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
