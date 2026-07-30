import { eq, asc } from 'drizzle-orm';
import { nanoid } from 'nanoid';
import type {
  CreateRunRequest,
  IncidentInput,
  IncidentReport,
  PipelineEvent,
  PipelineEventType,
  PipelineStepName,
  RunStatus,
  StepStatus,
} from '@opsswarm/shared';
import type { AppDb } from './client.js';
import { events, runs, stepAttempts, steps } from './schema.js';

export interface RunOptions {
  concurrencyLimit: number;
  stepTimeoutMs: number;
  maxRetries: number;
  scenarioId: string;
}

export interface RunRecord {
  id: string;
  idempotencyKey: string | null;
  status: RunStatus;
  scenarioId: string;
  incident: IncidentInput;
  options: RunOptions;
  report: IncidentReport | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  cancelRequested: boolean;
}

export interface StepRecord {
  id: string;
  runId: string;
  name: PipelineStepName;
  status: StepStatus;
  attempt: number;
  maxAttempts: number;
  output: unknown | null;
  errorMessage: string | null;
  tokenPrompt: number;
  tokenCompletion: number;
  durationMs: number | null;
  startedAt: string | null;
  finishedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

function nowIso(): string {
  return new Date().toISOString();
}

function parseJson<T>(value: string | null, fallback: T): T {
  if (value == null) return fallback;
  return JSON.parse(value) as T;
}

export class RunRepository {
  constructor(private readonly db: AppDb) {}

  findByIdempotencyKey(key: string): RunRecord | null {
    const row = this.db.select().from(runs).where(eq(runs.idempotencyKey, key)).get();
    return row ? this.mapRun(row) : null;
  }

  getRun(runId: string): RunRecord | null {
    const row = this.db.select().from(runs).where(eq(runs.id, runId)).get();
    return row ? this.mapRun(row) : null;
  }

  listRuns(): RunRecord[] {
    return this.db.select().from(runs).orderBy(asc(runs.createdAt)).all().map((r) => this.mapRun(r));
  }

  createRun(request: CreateRunRequest): RunRecord {
    if (request.idempotencyKey) {
      const existing = this.findByIdempotencyKey(request.idempotencyKey);
      if (existing) return existing;
    }

    const id = nanoid();
    const createdAt = nowIso();
    const scenarioId =
      request.options?.scenarioId ?? request.incident.scenarioId ?? 'happy';
    const options: RunOptions = {
      concurrencyLimit: request.options?.concurrencyLimit ?? 3,
      stepTimeoutMs: request.options?.stepTimeoutMs ?? 10_000,
      maxRetries: request.options?.maxRetries ?? 2,
      scenarioId,
    };

    const incident: IncidentInput = {
      ...request.incident,
      scenarioId,
    };

    this.db
      .insert(runs)
      .values({
        id,
        idempotencyKey: request.idempotencyKey ?? null,
        status: 'pending',
        scenarioId,
        incidentJson: JSON.stringify(incident),
        optionsJson: JSON.stringify(options),
        reportJson: null,
        errorMessage: null,
        createdAt,
        updatedAt: createdAt,
        startedAt: null,
        finishedAt: null,
        cancelRequested: false,
      })
      .run();

    const stepNames: PipelineStepName[] = [
      'validate',
      'logs_analyst',
      'metrics_analyst',
      'deployment_analyst',
      'critic',
      'synthesizer',
    ];

    for (const name of stepNames) {
      this.db
        .insert(steps)
        .values({
          id: nanoid(),
          runId: id,
          name,
          status: 'pending',
          attempt: 0,
          maxAttempts: options.maxRetries + 1,
          outputJson: null,
          errorMessage: null,
          tokenPrompt: 0,
          tokenCompletion: 0,
          durationMs: null,
          startedAt: null,
          finishedAt: null,
          createdAt,
          updatedAt: createdAt,
        })
        .run();
    }

    this.appendEvent({
      runId: id,
      type: 'run_created',
      message: `Run created for scenario ${scenarioId}`,
      payload: { scenarioId, idempotencyKey: request.idempotencyKey ?? null },
    });

    return this.getRun(id)!;
  }

  updateRunStatus(
    runId: string,
    status: RunStatus,
    extra: Partial<{
      report: IncidentReport;
      errorMessage: string;
      startedAt: string;
      finishedAt: string;
    }> = {},
  ): void {
    const updatedAt = nowIso();
    this.db
      .update(runs)
      .set({
        status,
        updatedAt,
        reportJson: extra.report ? JSON.stringify(extra.report) : undefined,
        errorMessage: extra.errorMessage,
        startedAt: extra.startedAt,
        finishedAt: extra.finishedAt,
      })
      .where(eq(runs.id, runId))
      .run();
  }

  requestCancel(runId: string): RunRecord | null {
    const run = this.getRun(runId);
    if (!run) return null;
    if (['completed', 'failed', 'cancelled', 'partial'].includes(run.status)) {
      return run;
    }
    this.db
      .update(runs)
      .set({ cancelRequested: true, updatedAt: nowIso() })
      .where(eq(runs.id, runId))
      .run();
    this.appendEvent({
      runId,
      type: 'run_cancelled',
      message: 'Cancellation requested',
    });
    return this.getRun(runId);
  }

  isCancelRequested(runId: string): boolean {
    const run = this.getRun(runId);
    return Boolean(run?.cancelRequested);
  }

  getSteps(runId: string): StepRecord[] {
    return this.db
      .select()
      .from(steps)
      .where(eq(steps.runId, runId))
      .all()
      .map((s) => this.mapStep(s));
  }

  getStep(runId: string, name: PipelineStepName): StepRecord | null {
    const row = this.db
      .select()
      .from(steps)
      .where(eq(steps.runId, runId))
      .all()
      .find((s) => s.name === name);
    return row ? this.mapStep(row) : null;
  }

  updateStep(
    stepId: string,
    patch: Partial<{
      status: StepStatus;
      attempt: number;
      output: unknown;
      errorMessage: string | null;
      tokenPrompt: number;
      tokenCompletion: number;
      durationMs: number;
      startedAt: string;
      finishedAt: string;
    }>,
  ): void {
    this.db
      .update(steps)
      .set({
        status: patch.status,
        attempt: patch.attempt,
        outputJson: patch.output !== undefined ? JSON.stringify(patch.output) : undefined,
        errorMessage: patch.errorMessage,
        tokenPrompt: patch.tokenPrompt,
        tokenCompletion: patch.tokenCompletion,
        durationMs: patch.durationMs,
        startedAt: patch.startedAt,
        finishedAt: patch.finishedAt,
        updatedAt: nowIso(),
      })
      .where(eq(steps.id, stepId))
      .run();
  }

  createAttempt(input: {
    stepId: string;
    attempt: number;
    isRepair: boolean;
    inputJson?: unknown;
  }): string {
    const id = nanoid();
    this.db
      .insert(stepAttempts)
      .values({
        id,
        stepId: input.stepId,
        attempt: input.attempt,
        status: 'running',
        isRepair: input.isRepair,
        inputJson: input.inputJson ? JSON.stringify(input.inputJson) : null,
        outputJson: null,
        errorMessage: null,
        tokenPrompt: 0,
        tokenCompletion: 0,
        durationMs: null,
        startedAt: nowIso(),
        finishedAt: null,
      })
      .run();
    return id;
  }

  finishAttempt(
    attemptId: string,
    patch: {
      status: StepStatus;
      output?: unknown;
      errorMessage?: string;
      tokenPrompt?: number;
      tokenCompletion?: number;
      durationMs?: number;
    },
  ): void {
    this.db
      .update(stepAttempts)
      .set({
        status: patch.status,
        outputJson: patch.output !== undefined ? JSON.stringify(patch.output) : undefined,
        errorMessage: patch.errorMessage,
        tokenPrompt: patch.tokenPrompt,
        tokenCompletion: patch.tokenCompletion,
        durationMs: patch.durationMs,
        finishedAt: nowIso(),
      })
      .where(eq(stepAttempts.id, attemptId))
      .run();
  }

  appendEvent(input: {
    runId: string;
    type: PipelineEventType;
    message: string;
    stepName?: PipelineStepName;
    attempt?: number;
    payload?: Record<string, unknown>;
  }): PipelineEvent {
    const event: PipelineEvent = {
      id: nanoid(),
      runId: input.runId,
      type: input.type,
      stepName: input.stepName,
      attempt: input.attempt,
      message: input.message,
      payload: input.payload,
      createdAt: nowIso(),
    };
    this.db
      .insert(events)
      .values({
        id: event.id,
        runId: event.runId,
        type: event.type,
        stepName: event.stepName ?? null,
        attempt: event.attempt ?? null,
        message: event.message,
        payloadJson: event.payload ? JSON.stringify(event.payload) : null,
        createdAt: event.createdAt,
      })
      .run();
    return event;
  }

  listEvents(runId: string): PipelineEvent[] {
    return this.db
      .select()
      .from(events)
      .where(eq(events.runId, runId))
      .orderBy(asc(events.createdAt))
      .all()
      .map((e) => ({
        id: e.id,
        runId: e.runId,
        type: e.type as PipelineEventType,
        stepName: (e.stepName as PipelineStepName | null) ?? undefined,
        attempt: e.attempt ?? undefined,
        message: e.message,
        payload: parseJson<Record<string, unknown> | undefined>(e.payloadJson, undefined),
        createdAt: e.createdAt,
      }));
  }

  listResumableRuns(): RunRecord[] {
    return this.listRuns().filter((r) => r.status === 'pending' || r.status === 'running');
  }

  private mapRun(row: typeof runs.$inferSelect): RunRecord {
    return {
      id: row.id,
      idempotencyKey: row.idempotencyKey,
      status: row.status as RunStatus,
      scenarioId: row.scenarioId,
      incident: parseJson(row.incidentJson, {} as IncidentInput),
      options: parseJson(row.optionsJson, {
        concurrencyLimit: 3,
        stepTimeoutMs: 10_000,
        maxRetries: 2,
        scenarioId: row.scenarioId,
      }),
      report: parseJson(row.reportJson, null),
      errorMessage: row.errorMessage,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
      startedAt: row.startedAt,
      finishedAt: row.finishedAt,
      cancelRequested: row.cancelRequested,
    };
  }

  private mapStep(row: typeof steps.$inferSelect): StepRecord {
    return {
      id: row.id,
      runId: row.runId,
      name: row.name as PipelineStepName,
      status: row.status as StepStatus,
      attempt: row.attempt,
      maxAttempts: row.maxAttempts,
      output: parseJson(row.outputJson, null),
      errorMessage: row.errorMessage,
      tokenPrompt: row.tokenPrompt,
      tokenCompletion: row.tokenCompletion,
      durationMs: row.durationMs,
      startedAt: row.startedAt,
      finishedAt: row.finishedAt,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    };
  }
}
