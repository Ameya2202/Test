export interface RunDto {
  id: string;
  status: string;
  scenarioId: string;
  incident: unknown;
  options: {
    concurrencyLimit: number;
    stepTimeoutMs: number;
    maxRetries: number;
    scenarioId: string;
  };
  report: IncidentReportDto | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  cancelRequested: boolean;
  idempotencyKey: string | null;
}

export interface StepDto {
  id: string;
  runId: string;
  name: string;
  status: string;
  attempt: number;
  maxAttempts: number;
  output: unknown;
  errorMessage: string | null;
  tokenPrompt: number;
  tokenCompletion: number;
  durationMs: number | null;
  startedAt: string | null;
  finishedAt: string | null;
}

export interface PipelineEventDto {
  id: string;
  runId: string;
  type: string;
  stepName?: string;
  attempt?: number;
  message: string;
  payload?: Record<string, unknown>;
  createdAt: string;
}

export interface IncidentReportDto {
  executiveSummary: string;
  mostLikelyRootCause: string;
  confidenceScore: number;
  supportingEvidence: Array<{ claim: string; evidenceIds: string[] }>;
  contradictoryEvidence: Array<{ description: string; evidenceIds: string[] }>;
  recommendedImmediateActions: string[];
  longerTermRemediation: string[];
  unknownsAndFollowUps: string[];
  partial: boolean;
  failedAgents: string[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function listScenarios(): Promise<string[]> {
  const data = await json<{ scenarios: string[] }>(await fetch('/api/scenarios'));
  return data.scenarios;
}

export async function createRun(input: {
  scenarioId: string;
  idempotencyKey?: string;
  concurrencyLimit?: number;
  stepTimeoutMs?: number;
  maxRetries?: number;
}): Promise<{ run: RunDto; steps: StepDto[] }> {
  const scenario = await json<{ incident: Record<string, unknown> }>(
    await fetch(`/api/scenarios/${input.scenarioId}`),
  );
  return json(
    await fetch('/api/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident: scenario.incident,
        idempotencyKey: input.idempotencyKey || undefined,
        options: {
          scenarioId: input.scenarioId,
          concurrencyLimit: input.concurrencyLimit ?? 3,
          stepTimeoutMs: input.stepTimeoutMs ?? 10_000,
          maxRetries: input.maxRetries ?? 2,
        },
      }),
    }),
  );
}

export async function getRun(runId: string): Promise<{
  run: RunDto;
  steps: StepDto[];
  events: PipelineEventDto[];
}> {
  return json(await fetch(`/api/runs/${runId}`));
}

export async function cancelRun(runId: string): Promise<{ run: RunDto }> {
  return json(
    await fetch(`/api/runs/${runId}/cancel`, {
      method: 'POST',
    }),
  );
}

export function subscribeRunEvents(
  runId: string,
  onEvent: (event: PipelineEventDto) => void,
): () => void {
  const source = new EventSource(`/api/runs/${runId}/stream`);
  const handler = (e: MessageEvent) => {
    try {
      onEvent(JSON.parse(e.data) as PipelineEventDto);
    } catch {
      // ignore malformed
    }
  };
  source.onmessage = handler;
  // Named event types also carry data
  for (const type of [
    'run_created',
    'run_started',
    'run_completed',
    'run_failed',
    'run_cancelled',
    'run_partial',
    'step_started',
    'step_succeeded',
    'step_failed',
    'step_retrying',
    'step_timed_out',
    'step_cancelled',
    'step_skipped',
    'event',
  ]) {
    source.addEventListener(type, handler as EventListener);
  }
  return () => source.close();
}
