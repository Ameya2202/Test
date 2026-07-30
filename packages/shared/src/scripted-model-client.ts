import type { AgentRole, ModelClient, ModelRequest, ModelResponse } from './schemas.js';

export type ScriptedBehavior =
  | { kind: 'success'; content: string; delayMs?: number; tokens?: number }
  | { kind: 'transient_failure'; message: string; delayMs?: number }
  | { kind: 'permanent_failure'; message: string; delayMs?: number }
  | { kind: 'invalid_json'; content: string; delayMs?: number }
  | { kind: 'timeout'; delayMs: number }
  | { kind: 'repair_success'; content: string; delayMs?: number; tokens?: number };

export type ScriptKey = `${string}:${AgentRole}`;

export interface ScriptedModelClientOptions {
  scripts: Record<ScriptKey, ScriptedBehavior[]>;
  defaultDelayMs?: number;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Deterministic model client that returns fixture responses based on
 * scenarioId + agent role + attempt number. Used for all official tests.
 */
export class ScriptedModelClient implements ModelClient {
  private readonly scripts: Record<ScriptKey, ScriptedBehavior[]>;
  private readonly defaultDelayMs: number;
  private readonly attemptCounters = new Map<string, number>();

  constructor(options: ScriptedModelClientOptions) {
    this.scripts = options.scripts;
    this.defaultDelayMs = options.defaultDelayMs ?? 0;
  }

  reset(): void {
    this.attemptCounters.clear();
  }

  async generate(request: ModelRequest): Promise<ModelResponse> {
    const key = `${request.scenarioId}:${request.role}` as ScriptKey;
    const sequence = this.scripts[key];
    if (!sequence || sequence.length === 0) {
      throw new Error(`No scripted response for ${key}`);
    }

    const counterKey = `${key}:${request.repair ? 'repair' : 'normal'}`;
    const idx = this.attemptCounters.get(counterKey) ?? 0;
    this.attemptCounters.set(counterKey, idx + 1);

    // Repair calls use the last behavior if repair_success isn't present,
    // or a dedicated repair_success when available.
    let behavior: ScriptedBehavior;
    if (request.repair) {
      const repairBehavior = sequence.find((b) => b.kind === 'repair_success');
      behavior = repairBehavior ?? sequence[Math.min(idx, sequence.length - 1)]!;
    } else {
      behavior = sequence[Math.min(idx, sequence.length - 1)]!;
    }

    const delay = behavior.delayMs ?? this.defaultDelayMs;
    if (delay > 0) {
      await sleep(delay);
    }

    switch (behavior.kind) {
      case 'success':
      case 'repair_success':
        return {
          content: behavior.content,
          tokenUsage: {
            promptTokens: behavior.tokens ?? 120,
            completionTokens: behavior.tokens ?? 80,
          },
          latencyMs: delay,
        };
      case 'invalid_json':
        return {
          content: behavior.content,
          tokenUsage: { promptTokens: 50, completionTokens: 20 },
          latencyMs: delay,
        };
      case 'transient_failure':
        throw Object.assign(new Error(behavior.message), {
          code: 'TRANSIENT_MODEL_ERROR',
          retryable: true,
        });
      case 'permanent_failure':
        throw Object.assign(new Error(behavior.message), {
          code: 'PERMANENT_MODEL_ERROR',
          retryable: false,
        });
      case 'timeout':
        // Delay already applied; simulate hanging past timeout by waiting more.
        await sleep(behavior.delayMs);
        return {
          content: '{}',
          tokenUsage: { promptTokens: 10, completionTokens: 0 },
          latencyMs: behavior.delayMs,
        };
      default: {
        const _exhaustive: never = behavior;
        throw new Error(`Unhandled behavior: ${JSON.stringify(_exhaustive)}`);
      }
    }
  }
}
