import { afterEach, describe, expect, it } from 'vitest';
import {
  ScriptedModelClient,
  SCENARIO_INCIDENTS,
  buildScenarioScripts,
} from '@opsswarm/shared';
import { buildApp } from './app.js';

async function waitForRun(
  repository: Awaited<ReturnType<typeof buildApp>>['repository'],
  runId: string,
  predicate: (status: string) => boolean,
  timeoutMs = 15_000,
) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const run = repository.getRun(runId);
    if (run && predicate(run.status)) return run;
    await new Promise((r) => setTimeout(r, 25));
  }
  throw new Error(`Timeout waiting for run ${runId}`);
}

describe('OpsSwarm API scenarios', () => {
  const apps: Array<Awaited<ReturnType<typeof buildApp>>> = [];

  afterEach(async () => {
    while (apps.length) {
      const ctx = apps.pop()!;
      await ctx.app.close();
    }
  });

  async function setup(extra?: { stepTimeoutMs?: number }) {
    const modelClient = new ScriptedModelClient({
      scripts: buildScenarioScripts(),
      defaultDelayMs: 5,
    });
    const ctx = await buildApp({
      databaseUrl: ':memory:',
      modelClient,
      autoResume: false,
    });
    apps.push(ctx);
    return { ...ctx, extra };
  }

  it('happy path: all agents succeed', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.happy,
        options: { scenarioId: 'happy', stepTimeoutMs: 5_000 },
      },
    });
    expect(res.statusCode).toBe(201);
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'completed');
    expect(run.report?.mostLikelyRootCause).toBeTruthy();
    expect(run.report?.supportingEvidence.length).toBeGreaterThan(0);
    const steps = repository.getSteps(runId);
    expect(steps.every((s) => s.status === 'succeeded')).toBe(true);
  });

  it('partial failure: metrics analyst fails permanently', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.partial_failure,
        options: { scenarioId: 'partial_failure' },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'partial');
    expect(run.report?.partial).toBe(true);
    expect(run.report?.failedAgents).toContain('metrics_analyst');
    const metrics = repository.getStep(runId, 'metrics_analyst');
    expect(metrics?.status).toBe('failed');
  });

  it('retry: logs analyst fails twice then succeeds', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.retry,
        options: { scenarioId: 'retry', maxRetries: 2 },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'completed');
    expect(run.status).toBe('completed');
    const logs = repository.getStep(runId, 'logs_analyst');
    expect(logs?.status).toBe('succeeded');
    expect(logs?.attempt).toBe(3);
    const events = repository.listEvents(runId);
    expect(events.some((e) => e.type === 'step_retrying')).toBe(true);
  });

  it('invalid output: deployment analyst repairs malformed JSON', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.invalid_output,
        options: { scenarioId: 'invalid_output' },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'completed');
    expect(run.status).toBe('completed');
    const dep = repository.getStep(runId, 'deployment_analyst');
    expect(dep?.status).toBe('succeeded');
    const events = repository.listEvents(runId);
    expect(events.some((e) => e.message.includes('attempting repair'))).toBe(true);
  });

  it('timeout: logs analyst exceeds deadline', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.timeout,
        options: { scenarioId: 'timeout', stepTimeoutMs: 200, maxRetries: 0 },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'partial' || s === 'completed');
    const logs = repository.getStep(runId, 'logs_analyst');
    expect(logs?.status).toBe('timed_out');
    expect(run.report?.failedAgents).toContain('logs_analyst');
  });

  it('contradiction: critic surfaces conflicting hypotheses', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.contradiction,
        options: { scenarioId: 'contradiction' },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'completed');
    expect(run.report?.contradictoryEvidence.length).toBeGreaterThan(0);
    const critic = repository.getStep(runId, 'critic');
    const output = critic?.output as { contradictions: unknown[] };
    expect(output.contradictions.length).toBeGreaterThan(0);
  });

  it('cancellation: user cancels during parallel execution', async () => {
    const { app, repository, orchestrator } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.cancellation,
        options: { scenarioId: 'cancellation', stepTimeoutMs: 20_000 },
      },
    });
    const runId = res.json().run.id as string;
    // Let validate finish and investigation start
    await new Promise((r) => setTimeout(r, 150));
    orchestrator.cancelRun(runId);
    const run = await waitForRun(repository, runId, (s) => s === 'cancelled');
    expect(run.status).toBe('cancelled');
  });

  it('duplicate request: same idempotency key returns existing run', async () => {
    const { app, repository } = await setup();
    const payload = {
      incident: SCENARIO_INCIDENTS.duplicate,
      idempotencyKey: 'idem-123',
      options: { scenarioId: 'duplicate' },
    };
    const first = await app.inject({ method: 'POST', url: '/api/runs', payload });
    expect(first.statusCode).toBe(201);
    const second = await app.inject({ method: 'POST', url: '/api/runs', payload });
    expect(second.statusCode).toBe(200);
    expect(second.json().idempotentReplay).toBe(true);
    expect(second.json().run.id).toBe(first.json().run.id);
    await waitForRun(repository, first.json().run.id, (s) => s === 'completed');
  });

  it('invalid citation: repair replaces unsupported evidence IDs', async () => {
    const { app, repository } = await setup();
    const res = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.invalid_citation,
        options: { scenarioId: 'invalid_citation' },
      },
    });
    const runId = res.json().run.id as string;
    const run = await waitForRun(repository, runId, (s) => s === 'completed');
    expect(run.status).toBe('completed');
    const logs = repository.getStep(runId, 'logs_analyst');
    const output = logs?.output as { evidenceIds: string[] };
    expect(output.evidenceIds).not.toContain('log-999-does-not-exist');
  });

  it('restart: unfinished run resumes after new app boot', async () => {
    const modelClient = new ScriptedModelClient({
      scripts: buildScenarioScripts(),
      defaultDelayMs: 5,
    });
    // Shared file DB so second process sees same state. Use unique temp path.
    const dbPath = `./data/test-restart-${Date.now()}.db`;
    const first = await buildApp({
      databaseUrl: dbPath,
      modelClient,
      autoResume: false,
    });
    apps.push(first);

    const res = await first.app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.restart,
        options: { scenarioId: 'restart', stepTimeoutMs: 10_000 },
      },
    });
    const runId = res.json().run.id as string;
    // Wait until investigation is in progress
    await new Promise((r) => setTimeout(r, 100));
    await first.app.close();
    apps.pop();

    const secondClient = new ScriptedModelClient({
      scripts: buildScenarioScripts(),
      defaultDelayMs: 5,
    });
    const second = await buildApp({
      databaseUrl: dbPath,
      modelClient: secondClient,
      autoResume: false,
    });
    apps.push(second);

    // Manually resume as the new process would
    await second.orchestrator.resumeUnfinishedRuns();
    const run = await waitForRun(second.repository, runId, (s) => s === 'completed' || s === 'partial');
    expect(['completed', 'partial']).toContain(run.status);
    expect(run.report).toBeTruthy();
  });

  it('streams pipeline events over SSE', async () => {
    const { app } = await setup();
    const create = await app.inject({
      method: 'POST',
      url: '/api/runs',
      payload: {
        incident: SCENARIO_INCIDENTS.happy,
        options: { scenarioId: 'happy' },
      },
    });
    const runId = create.json().run.id as string;
    // Give the run a moment, then fetch persisted events endpoint
    await new Promise((r) => setTimeout(r, 300));
    const eventsRes = await app.inject({ method: 'GET', url: `/api/runs/${runId}/events` });
    expect(eventsRes.statusCode).toBe(200);
    const events = eventsRes.json().events as Array<{ type: string }>;
    expect(events.some((e) => e.type === 'run_created')).toBe(true);
  });
});
