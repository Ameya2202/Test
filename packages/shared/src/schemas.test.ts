import { describe, expect, it } from 'vitest';
import { IncidentInputSchema, collectEvidenceIds } from './schemas.js';
import { ScriptedModelClient } from './scripted-model-client.js';
import { baseIncident, buildScenarioScripts } from './fixtures.js';

describe('IncidentInputSchema', () => {
  it('parses base incident', () => {
    const parsed = IncidentInputSchema.parse(baseIncident);
    expect(parsed.serviceName).toBe('checkout-api');
    expect(collectEvidenceIds(parsed).has('log-001')).toBe(true);
  });
});

describe('ScriptedModelClient', () => {
  it('returns success then advances attempts for retries', async () => {
    const client = new ScriptedModelClient({ scripts: buildScenarioScripts() });
    await expect(
      client.generate({
        role: 'logs_analyst',
        scenarioId: 'retry',
        prompt: 'x',
        attempt: 0,
        repair: false,
      }),
    ).rejects.toMatchObject({ retryable: true });

    await expect(
      client.generate({
        role: 'logs_analyst',
        scenarioId: 'retry',
        prompt: 'x',
        attempt: 1,
        repair: false,
      }),
    ).rejects.toMatchObject({ retryable: true });

    const ok = await client.generate({
      role: 'logs_analyst',
      scenarioId: 'retry',
      prompt: 'x',
      attempt: 2,
      repair: false,
    });
    expect(JSON.parse(ok.content).role).toBe('logs_analyst');
  });
});
