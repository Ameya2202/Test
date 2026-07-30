import { EventEmitter } from 'node:events';
import {
  AnalystOutputSchema,
  CriticOutputSchema,
  IncidentReportSchema,
  INVESTIGATION_STEPS,
  ValidatorOutputSchema,
  collectEvidenceIds,
  roleForStep,
  type AgentRole,
  type AnalystOutput,
  type CriticOutput,
  type IncidentInput,
  type IncidentReport,
  type ModelClient,
  type PipelineEvent,
  type PipelineStepName,
  type ValidatorOutput,
} from '@opsswarm/shared';
import type { RunRepository, StepRecord } from '../db/repository.js';

export interface OrchestratorOptions {
  modelClient: ModelClient;
  repository: RunRepository;
  /** Base delay for exponential backoff in ms */
  backoffBaseMs?: number;
}

type StepResult =
  | { ok: true; output: unknown; cancelled?: false; timedOut?: false }
  | {
      ok: false;
      error: string;
      retryable: boolean;
      timedOut?: boolean;
      cancelled?: boolean;
    };

function isRetryableError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  return Boolean((err as { retryable?: boolean }).retryable);
}

function withTimeout<T>(promise: Promise<T>, ms: number, signal: AbortSignal): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    if (signal.aborted) {
      reject(Object.assign(new Error('cancelled'), { cancelled: true, retryable: false }));
      return;
    }

    const timer = setTimeout(() => {
      reject(Object.assign(new Error(`step timed out after ${ms}ms`), { timedOut: true, retryable: false }));
    }, ms);

    const onAbort = () => {
      clearTimeout(timer);
      reject(Object.assign(new Error('cancelled'), { cancelled: true, retryable: false }));
    };
    signal.addEventListener('abort', onAbort, { once: true });

    promise.then(
      (value) => {
        clearTimeout(timer);
        signal.removeEventListener('abort', onAbort);
        resolve(value);
      },
      (err: unknown) => {
        clearTimeout(timer);
        signal.removeEventListener('abort', onAbort);
        reject(err);
      },
    );
  });
}

async function mapPool<T, R>(
  items: T[],
  limit: number,
  worker: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let next = 0;

  async function runWorker(): Promise<void> {
    while (next < items.length) {
      const index = next++;
      results[index] = await worker(items[index]!);
    }
  }

  const workers = Array.from({ length: Math.min(limit, items.length) }, () => runWorker());
  await Promise.all(workers);
  return results;
}

function validateEvidenceCitations(
  evidenceIds: string[],
  known: Set<string>,
): string | null {
  const missing = evidenceIds.filter((id) => !known.has(id));
  if (missing.length > 0) {
    return `Unsupported evidence citations: ${missing.join(', ')}`;
  }
  return null;
}

function parseAgentOutput(
  step: PipelineStepName,
  content: string,
  knownEvidence: Set<string>,
): { ok: true; output: unknown } | { ok: false; error: string } {
  let parsed: unknown;
  try {
    parsed = JSON.parse(content);
  } catch {
    return { ok: false, error: 'Invalid JSON from model' };
  }

  try {
    switch (step) {
      case 'validate': {
        const output = ValidatorOutputSchema.parse(parsed);
        return { ok: true, output };
      }
      case 'logs_analyst':
      case 'metrics_analyst':
      case 'deployment_analyst': {
        const output = AnalystOutputSchema.parse(parsed);
        const cited = [
          ...output.evidenceIds,
          ...output.findings.flatMap((f) => f.evidenceIds),
        ];
        const citationError = validateEvidenceCitations(cited, knownEvidence);
        if (citationError) return { ok: false, error: citationError };
        return { ok: true, output };
      }
      case 'critic': {
        const output = CriticOutputSchema.parse(parsed);
        return { ok: true, output };
      }
      case 'synthesizer': {
        const output = IncidentReportSchema.parse(parsed);
        const cited = [
          ...output.supportingEvidence.flatMap((s) => s.evidenceIds),
          ...output.contradictoryEvidence.flatMap((c) => c.evidenceIds),
        ];
        const citationError = validateEvidenceCitations(cited, knownEvidence);
        if (citationError) return { ok: false, error: citationError };
        return { ok: true, output };
      }
    }
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : 'Schema validation failed',
    };
  }
}

/**
 * Explicit directed-graph / state-machine orchestrator.
 *
 * Graph:
 *   validate → (logs | metrics | deployment)[parallel] → critic → synthesizer
 */
export class PipelineOrchestrator {
  private readonly modelClient: ModelClient;
  private readonly repository: RunRepository;
  private readonly backoffBaseMs: number;
  private readonly emitter = new EventEmitter();
  private readonly activeAbortControllers = new Map<string, AbortController>();
  private readonly running = new Set<string>();

  constructor(options: OrchestratorOptions) {
    this.modelClient = options.modelClient;
    this.repository = options.repository;
    this.backoffBaseMs = options.backoffBaseMs ?? 50;
    this.emitter.setMaxListeners(100);
  }

  onEvent(listener: (event: PipelineEvent) => void): () => void {
    this.emitter.on('event', listener);
    return () => this.emitter.off('event', listener);
  }

  private emitPersisted(event: PipelineEvent): void {
    this.emitter.emit('event', event);
  }

  private persistEvent(
    runId: string,
    type: PipelineEvent['type'],
    message: string,
    extra: Partial<Pick<PipelineEvent, 'stepName' | 'attempt' | 'payload'>> = {},
  ): PipelineEvent {
    const event = this.repository.appendEvent({
      runId,
      type,
      message,
      stepName: extra.stepName,
      attempt: extra.attempt,
      payload: extra.payload,
    });
    this.emitPersisted(event);
    return event;
  }

  async startRun(runId: string): Promise<void> {
    if (this.running.has(runId)) return;
    this.running.add(runId);
    const controller = new AbortController();
    this.activeAbortControllers.set(runId, controller);

    try {
      await this.executeRun(runId, controller.signal);
    } finally {
      this.running.delete(runId);
      this.activeAbortControllers.delete(runId);
    }
  }

  cancelRun(runId: string): void {
    this.repository.requestCancel(runId);
    const controller = this.activeAbortControllers.get(runId);
    controller?.abort();
  }

  /** Resume unfinished runs after process restart. */
  async resumeUnfinishedRuns(): Promise<string[]> {
    const resumable = this.repository.listResumableRuns();
    const ids: string[] = [];
    for (const run of resumable) {
      ids.push(run.id);
      // Fire and forget; each run is tracked in `running`.
      void this.startRun(run.id);
    }
    return ids;
  }

  private async executeRun(runId: string, signal: AbortSignal): Promise<void> {
    const run = this.repository.getRun(runId);
    if (!run) return;

    if (run.cancelRequested) {
      this.markCancelled(runId);
      return;
    }

    if (run.status === 'pending') {
      this.repository.updateRunStatus(runId, 'running', { startedAt: new Date().toISOString() });
      this.persistEvent(runId, 'run_started', 'Pipeline started');
    }

    const incident = run.incident;
    const knownEvidence = collectEvidenceIds(incident);
    const failedAgents: string[] = [];

    // Step 1: validate
    const validateResult = await this.runStep(runId, 'validate', incident, knownEvidence, signal, {});
    if (validateResult.cancelled || this.repository.isCancelRequested(runId)) {
      this.markCancelled(runId);
      return;
    }
    if (!validateResult.ok) {
      this.repository.updateRunStatus(runId, 'failed', {
        errorMessage: validateResult.error,
        finishedAt: new Date().toISOString(),
      });
      this.persistEvent(runId, 'run_failed', validateResult.error);
      return;
    }

    // Step 2: parallel investigation with concurrency limit
    const investigateResults = await mapPool(
      [...INVESTIGATION_STEPS],
      run.options.concurrencyLimit,
      async (stepName) => {
        if (signal.aborted || this.repository.isCancelRequested(runId)) {
          return { stepName, result: { ok: false, error: 'cancelled', retryable: false, cancelled: true } as StepResult };
        }
        const existing = this.repository.getStep(runId, stepName);
        if (existing && (existing.status === 'succeeded' || existing.status === 'failed' || existing.status === 'timed_out')) {
          // Resume: skip completed/terminal steps
          return {
            stepName,
            result: existing.status === 'succeeded'
              ? ({ ok: true, output: existing.output } as StepResult)
              : ({ ok: false, error: existing.errorMessage ?? 'failed', retryable: false, timedOut: existing.status === 'timed_out' } as StepResult),
          };
        }
        const result = await this.runStep(runId, stepName, incident, knownEvidence, signal, {
          validator: validateResult.output,
        });
        return { stepName, result };
      },
    );

    if (signal.aborted || this.repository.isCancelRequested(runId)) {
      this.markCancelled(runId);
      return;
    }

    const analystOutputs: AnalystOutput[] = [];
    for (const { stepName, result } of investigateResults) {
      if (result.ok) {
        analystOutputs.push(result.output as AnalystOutput);
      } else if (!result.cancelled) {
        failedAgents.push(stepName);
        // Permanent failure: continue to partial report
        this.persistEvent(runId, 'event', `Investigation agent ${stepName} failed permanently; continuing`, {
          stepName,
          payload: { error: result.error },
        });
      }
    }

    // Step 3: critic
    const criticResult = await this.runStep(runId, 'critic', incident, knownEvidence, signal, {
      analysts: analystOutputs,
      failedAgents,
    });
    if (criticResult.cancelled || this.repository.isCancelRequested(runId)) {
      this.markCancelled(runId);
      return;
    }
    if (!criticResult.ok) {
      failedAgents.push('critic');
    }

    // Step 4: synthesizer
    const synthResult = await this.runStep(runId, 'synthesizer', incident, knownEvidence, signal, {
      analysts: analystOutputs,
      critic: criticResult.ok ? criticResult.output : null,
      failedAgents,
    });
    if (synthResult.cancelled || this.repository.isCancelRequested(runId)) {
      this.markCancelled(runId);
      return;
    }

    if (!synthResult.ok) {
      this.repository.updateRunStatus(runId, 'failed', {
        errorMessage: synthResult.error,
        finishedAt: new Date().toISOString(),
      });
      this.persistEvent(runId, 'run_failed', synthResult.error);
      return;
    }

    const report = synthResult.output as IncidentReport;
    const finalReport: IncidentReport = {
      ...report,
      partial: failedAgents.length > 0 || report.partial,
      failedAgents: [...new Set([...report.failedAgents, ...failedAgents])],
    };

    const status = failedAgents.length > 0 ? 'partial' : 'completed';
    this.repository.updateRunStatus(runId, status, {
      report: finalReport,
      finishedAt: new Date().toISOString(),
    });
    this.persistEvent(
      runId,
      status === 'partial' ? 'run_partial' : 'run_completed',
      status === 'partial' ? 'Run completed with partial results' : 'Run completed successfully',
      { payload: { failedAgents } },
    );
  }

  private markCancelled(runId: string): void {
    const steps = this.repository.getSteps(runId);
    for (const step of steps) {
      if (step.status === 'pending' || step.status === 'running') {
        this.repository.updateStep(step.id, {
          status: 'cancelled',
          finishedAt: new Date().toISOString(),
          errorMessage: 'cancelled',
        });
        this.persistEvent(runId, 'step_cancelled', `Step ${step.name} cancelled`, {
          stepName: step.name,
        });
      }
    }
    this.repository.updateRunStatus(runId, 'cancelled', {
      finishedAt: new Date().toISOString(),
      errorMessage: 'cancelled',
    });
  }

  private async runStep(
    runId: string,
    stepName: PipelineStepName,
    incident: IncidentInput,
    knownEvidence: Set<string>,
    signal: AbortSignal,
    context: Record<string, unknown>,
  ): Promise<StepResult> {
    const run = this.repository.getRun(runId);
    if (!run) return { ok: false, error: 'run not found', retryable: false };

    let step = this.repository.getStep(runId, stepName);
    if (!step) return { ok: false, error: `step ${stepName} missing`, retryable: false };

    // Resume: already succeeded
    if (step.status === 'succeeded' && step.output != null) {
      return { ok: true, output: step.output };
    }
    if (step.status === 'failed' || step.status === 'timed_out' || step.status === 'cancelled') {
      return {
        ok: false,
        error: step.errorMessage ?? step.status,
        retryable: false,
        timedOut: step.status === 'timed_out',
        cancelled: step.status === 'cancelled',
      };
    }

    const maxAttempts = step.maxAttempts;
    let attempt = step.attempt;

    while (attempt < maxAttempts) {
      if (signal.aborted || this.repository.isCancelRequested(runId)) {
        this.repository.updateStep(step.id, {
          status: 'cancelled',
          finishedAt: new Date().toISOString(),
          errorMessage: 'cancelled',
        });
        return { ok: false, error: 'cancelled', retryable: false, cancelled: true };
      }

      attempt += 1;
      const startedAt = new Date().toISOString();
      this.repository.updateStep(step.id, {
        status: 'running',
        attempt,
        startedAt: step.startedAt ?? startedAt,
        errorMessage: null,
      });

      if (attempt > 1) {
        this.persistEvent(runId, 'step_retrying', `Retrying ${stepName} (attempt ${attempt})`, {
          stepName,
          attempt,
        });
        const backoff = this.backoffBaseMs * 2 ** (attempt - 2);
        await sleep(backoff, signal).catch(() => undefined);
      } else {
        this.persistEvent(runId, 'step_started', `Starting ${stepName}`, { stepName, attempt });
      }

      const result = await this.executeAttempt(
        runId,
        step,
        stepName,
        attempt,
        false,
        incident,
        knownEvidence,
        run.options.stepTimeoutMs,
        signal,
        context,
      );

      step = this.repository.getStep(runId, stepName)!;

      if (result.ok) {
        return result;
      }

      if (result.cancelled) {
        this.repository.updateStep(step.id, {
          status: 'cancelled',
          finishedAt: new Date().toISOString(),
          errorMessage: 'cancelled',
        });
        this.persistEvent(runId, 'step_cancelled', `Step ${stepName} cancelled`, {
          stepName,
          attempt,
        });
        return result;
      }

      if (result.timedOut) {
        this.repository.updateStep(step.id, {
          status: 'timed_out',
          finishedAt: new Date().toISOString(),
          errorMessage: result.error,
        });
        this.persistEvent(runId, 'step_timed_out', result.error, { stepName, attempt });
        return result;
      }

      if (!result.retryable || attempt >= maxAttempts) {
        this.repository.updateStep(step.id, {
          status: 'failed',
          finishedAt: new Date().toISOString(),
          errorMessage: result.error,
        });
        this.persistEvent(runId, 'step_failed', result.error, { stepName, attempt });
        return result;
      }
    }

    return { ok: false, error: 'max attempts exceeded', retryable: false };
  }

  private async executeAttempt(
    runId: string,
    step: StepRecord,
    stepName: PipelineStepName,
    attempt: number,
    isRepair: boolean,
    incident: IncidentInput,
    knownEvidence: Set<string>,
    timeoutMs: number,
    signal: AbortSignal,
    context: Record<string, unknown>,
  ): Promise<StepResult> {
    const role: AgentRole = roleForStep(stepName);
    const run = this.repository.getRun(runId)!;
    const attemptId = this.repository.createAttempt({
      stepId: step.id,
      attempt,
      isRepair,
      inputJson: { role, context },
    });
    const t0 = Date.now();

    try {
      const response = await withTimeout(
        this.modelClient.generate({
          role,
          scenarioId: run.scenarioId,
          prompt: buildPrompt(stepName, incident, context),
          attempt: attempt - 1,
          repair: isRepair,
          context,
        }),
        timeoutMs,
        signal,
      );

      const durationMs = Date.now() - t0;
      const parsed = parseAgentOutput(stepName, response.content, knownEvidence);

      if (!parsed.ok) {
        // One repair attempt before failing this attempt
        if (!isRepair) {
          this.persistEvent(runId, 'event', `Invalid output from ${stepName}; attempting repair`, {
            stepName,
            attempt,
            payload: { error: parsed.error },
          });
          this.repository.finishAttempt(attemptId, {
            status: 'failed',
            errorMessage: parsed.error,
            tokenPrompt: response.tokenUsage.promptTokens,
            tokenCompletion: response.tokenUsage.completionTokens,
            durationMs,
          });
          return this.executeAttempt(
            runId,
            step,
            stepName,
            attempt,
            true,
            incident,
            knownEvidence,
            timeoutMs,
            signal,
            { ...context, previousInvalidOutput: response.content, validationError: parsed.error },
          );
        }

        this.repository.finishAttempt(attemptId, {
          status: 'failed',
          errorMessage: parsed.error,
          tokenPrompt: response.tokenUsage.promptTokens,
          tokenCompletion: response.tokenUsage.completionTokens,
          durationMs,
        });
        this.repository.updateStep(step.id, {
          tokenPrompt: step.tokenPrompt + response.tokenUsage.promptTokens,
          tokenCompletion: step.tokenCompletion + response.tokenUsage.completionTokens,
          durationMs: (step.durationMs ?? 0) + durationMs,
        });
        return { ok: false, error: parsed.error, retryable: true };
      }

      this.repository.finishAttempt(attemptId, {
        status: 'succeeded',
        output: parsed.output,
        tokenPrompt: response.tokenUsage.promptTokens,
        tokenCompletion: response.tokenUsage.completionTokens,
        durationMs,
      });
      this.repository.updateStep(step.id, {
        status: 'succeeded',
        output: parsed.output,
        finishedAt: new Date().toISOString(),
        tokenPrompt: step.tokenPrompt + response.tokenUsage.promptTokens,
        tokenCompletion: step.tokenCompletion + response.tokenUsage.completionTokens,
        durationMs: (step.durationMs ?? 0) + durationMs,
        errorMessage: null,
      });
      this.persistEvent(runId, 'step_succeeded', `Step ${stepName} succeeded`, {
        stepName,
        attempt,
        payload: {
          tokenUsage: response.tokenUsage,
          durationMs,
        },
      });
      return { ok: true, output: parsed.output };
    } catch (err) {
      const durationMs = Date.now() - t0;
      const cancelled = Boolean((err as { cancelled?: boolean })?.cancelled) || signal.aborted;
      const timedOut = Boolean((err as { timedOut?: boolean })?.timedOut);
      const message = err instanceof Error ? err.message : String(err);

      this.repository.finishAttempt(attemptId, {
        status: cancelled ? 'cancelled' : timedOut ? 'timed_out' : 'failed',
        errorMessage: message,
        durationMs,
      });
      this.repository.updateStep(step.id, {
        durationMs: (step.durationMs ?? 0) + durationMs,
      });

      if (cancelled) {
        return { ok: false, error: message, retryable: false, cancelled: true };
      }
      if (timedOut) {
        return { ok: false, error: message, retryable: false, timedOut: true };
      }
      return {
        ok: false,
        error: message,
        retryable: isRetryableError(err),
      };
    }
  }
}

function buildPrompt(
  stepName: PipelineStepName,
  incident: IncidentInput,
  context: Record<string, unknown>,
): string {
  return JSON.stringify({ stepName, incident, context });
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(Object.assign(new Error('cancelled'), { cancelled: true }));
      return;
    }
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      'abort',
      () => {
        clearTimeout(timer);
        reject(Object.assign(new Error('cancelled'), { cancelled: true }));
      },
      { once: true },
    );
  });
}

// Silence unused type import warnings in some TS configs
export type { ValidatorOutput, CriticOutput };
