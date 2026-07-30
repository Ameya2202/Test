import type { IncidentInput } from './schemas.js';
import type { ScriptedBehavior, ScriptKey } from './scripted-model-client.js';

export const baseIncident: IncidentInput = {
  serviceName: 'checkout-api',
  severity: 'SEV2',
  alertDescription: 'Elevated 5xx rate on checkout-api; p99 latency spike',
  occurredAt: '2026-07-30T10:15:00.000Z',
  logs: [
    {
      evidenceId: 'log-001',
      timestamp: '2026-07-30T10:14:50.000Z',
      level: 'error',
      message: 'connection pool exhausted talking to payments-db',
      service: 'checkout-api',
    },
    {
      evidenceId: 'log-002',
      timestamp: '2026-07-30T10:14:55.000Z',
      level: 'error',
      message: 'timeout waiting for payment authorization',
      service: 'checkout-api',
    },
    {
      evidenceId: 'log-003',
      timestamp: '2026-07-30T10:15:01.000Z',
      level: 'warn',
      message: 'circuit breaker opened for payments-db',
      service: 'checkout-api',
    },
  ],
  metrics: [
    {
      evidenceId: 'met-001',
      timestamp: '2026-07-30T10:14:00.000Z',
      name: 'http_5xx_rate',
      value: 0.02,
      unit: 'ratio',
    },
    {
      evidenceId: 'met-002',
      timestamp: '2026-07-30T10:15:00.000Z',
      name: 'http_5xx_rate',
      value: 0.18,
      unit: 'ratio',
    },
    {
      evidenceId: 'met-003',
      timestamp: '2026-07-30T10:15:00.000Z',
      name: 'db_connection_pool_usage',
      value: 0.99,
      unit: 'ratio',
    },
  ],
  deployments: [
    {
      evidenceId: 'dep-001',
      timestamp: '2026-07-30T09:50:00.000Z',
      service: 'checkout-api',
      version: '1.42.0',
      environment: 'prod',
      changeSummary: 'Increase payment client pool size default and add retries',
      author: 'platform-team',
    },
  ],
  configChanges: [
    {
      evidenceId: 'cfg-001',
      timestamp: '2026-07-30T09:55:00.000Z',
      service: 'checkout-api',
      key: 'PAYMENTS_DB_MAX_CONNECTIONS',
      oldValue: '50',
      newValue: '200',
      author: 'sre-oncall',
    },
  ],
};

function json(value: unknown): string {
  return JSON.stringify(value);
}

const happyValidator = json({
  valid: true,
  evidenceIds: ['log-001', 'log-002', 'log-003', 'met-001', 'met-002', 'met-003', 'dep-001', 'cfg-001'],
  issues: [],
});

const happyLogs = json({
  role: 'logs_analyst',
  findings: [
    {
      summary: 'Database connection pool exhaustion preceding circuit breaker open',
      confidence: 0.9,
      evidenceIds: ['log-001', 'log-003'],
      details: 'Error logs show pool exhaustion then breaker open.',
    },
  ],
  hypotheses: ['payments-db saturation caused checkout failures'],
  evidenceIds: ['log-001', 'log-002', 'log-003'],
});

const happyMetrics = json({
  role: 'metrics_analyst',
  findings: [
    {
      summary: '5xx rate rose from 2% to 18% with pool usage at 99%',
      confidence: 0.88,
      evidenceIds: ['met-001', 'met-002', 'met-003'],
    },
  ],
  hypotheses: ['resource exhaustion on DB connections'],
  evidenceIds: ['met-001', 'met-002', 'met-003'],
});

const happyDeploy = json({
  role: 'deployment_analyst',
  findings: [
    {
      summary: 'Config increased max connections shortly after deploy 1.42.0',
      confidence: 0.7,
      evidenceIds: ['dep-001', 'cfg-001'],
    },
  ],
  hypotheses: ['misconfigured pool size may amplify DB pressure'],
  evidenceIds: ['dep-001', 'cfg-001'],
});

const happyCritic = json({
  contradictions: [],
  unsupportedClaims: [],
  notes: ['Analyst findings are mutually consistent around DB saturation'],
});

const happyReport = json({
  executiveSummary:
    'Checkout-api SEV2 is most likely caused by payments-db connection pool exhaustion after a recent pool-size config change.',
  mostLikelyRootCause:
    'PAYMENTS_DB_MAX_CONNECTIONS increase overloaded the database, exhausting the pool and tripping the circuit breaker.',
  confidenceScore: 0.86,
  supportingEvidence: [
    {
      claim: 'Logs show pool exhaustion and circuit breaker open',
      evidenceIds: ['log-001', 'log-003'],
    },
    {
      claim: 'Metrics show 5xx spike and 99% pool usage',
      evidenceIds: ['met-002', 'met-003'],
    },
    {
      claim: 'Config change raised max connections before the alert',
      evidenceIds: ['cfg-001'],
    },
  ],
  contradictoryEvidence: [],
  recommendedImmediateActions: [
    'Roll back PAYMENTS_DB_MAX_CONNECTIONS to 50',
    'Scale payments-db read replicas / connections',
    'Reset circuit breaker after DB recovers',
  ],
  longerTermRemediation: [
    'Add load tests for pool sizing changes',
    'Gate config changes behind progressive rollout',
    'Alert on pool usage before breaker trips',
  ],
  unknownsAndFollowUps: [
    'Was payments-db CPU/IO saturated?',
    'Did any other services share the same pool increase?',
  ],
  partial: false,
  failedAgents: [],
});

const contradictionCritic = json({
  contradictions: [
    {
      description:
        'Logs point to database saturation while deployment analyst emphasizes a bad release as primary cause',
      relatedEvidenceIds: ['log-001', 'dep-001'],
      conflictingClaims: [
        'Database pool exhaustion is primary',
        'Bad release 1.42.0 is primary',
      ],
    },
  ],
  unsupportedClaims: [],
  notes: ['Need synthesizer to weigh both lines of evidence'],
});

const contradictionDeploy = json({
  role: 'deployment_analyst',
  findings: [
    {
      summary: 'Release 1.42.0 introduced payment client retries that likely caused a thundering herd',
      confidence: 0.85,
      evidenceIds: ['dep-001'],
    },
  ],
  hypotheses: ['bad release is the primary root cause'],
  evidenceIds: ['dep-001'],
});

const contradictionReport = json({
  executiveSummary:
    'Evidence conflicts: logs/metrics implicate DB pool saturation; deployment analysis implicates release 1.42.0 retries.',
  mostLikelyRootCause:
    'Combined effect of release 1.42.0 retries and elevated PAYMENTS_DB_MAX_CONNECTIONS amplifying DB pressure.',
  confidenceScore: 0.62,
  supportingEvidence: [
    {
      claim: 'Pool exhaustion and breaker open in logs',
      evidenceIds: ['log-001', 'log-003'],
    },
    {
      claim: 'Deploy added retries near incident time',
      evidenceIds: ['dep-001'],
    },
  ],
  contradictoryEvidence: [
    {
      description: 'Analysts disagree whether DB saturation or bad release is primary',
      evidenceIds: ['log-001', 'dep-001'],
    },
  ],
  recommendedImmediateActions: [
    'Disable aggressive payment client retries',
    'Revert pool max connections',
  ],
  longerTermRemediation: [
    'Add chaos tests for retry storms',
    'Coordinate deploy + config change review',
  ],
  unknownsAndFollowUps: ['Need A/B of retries alone vs config alone'],
  partial: false,
  failedAgents: [],
});

const invalidCitationLogs = json({
  role: 'logs_analyst',
  findings: [
    {
      summary: 'Mysterious upstream failure',
      confidence: 0.5,
      evidenceIds: ['log-999-does-not-exist'],
    },
  ],
  hypotheses: [],
  evidenceIds: ['log-999-does-not-exist'],
});

const repairedLogs = json({
  role: 'logs_analyst',
  findings: [
    {
      summary: 'Database connection pool exhaustion',
      confidence: 0.85,
      evidenceIds: ['log-001', 'log-003'],
    },
  ],
  hypotheses: ['DB saturation'],
  evidenceIds: ['log-001', 'log-003'],
});

const partialReport = json({
  executiveSummary:
    'Partial investigation: metrics analyst failed permanently; remaining evidence still points to DB pool pressure.',
  mostLikelyRootCause: 'Likely payments-db connection pool exhaustion (metrics unavailable).',
  confidenceScore: 0.55,
  supportingEvidence: [
    {
      claim: 'Logs show pool exhaustion',
      evidenceIds: ['log-001', 'log-003'],
    },
    {
      claim: 'Config raised max connections',
      evidenceIds: ['cfg-001'],
    },
  ],
  contradictoryEvidence: [],
  recommendedImmediateActions: ['Rollback config change', 'Collect metrics manually'],
  longerTermRemediation: ['Improve metrics agent reliability'],
  unknownsAndFollowUps: ['What did metrics show at T+0?'],
  partial: true,
  failedAgents: ['metrics_analyst'],
});

export function buildScenarioScripts(): Record<ScriptKey, ScriptedBehavior[]> {
  const scripts: Record<ScriptKey, ScriptedBehavior[]> = {
    'happy:validator': [{ kind: 'success', content: happyValidator }],
    'happy:logs_analyst': [{ kind: 'success', content: happyLogs }],
    'happy:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'happy:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'happy:critic': [{ kind: 'success', content: happyCritic }],
    'happy:synthesizer': [{ kind: 'success', content: happyReport }],

    'partial_failure:validator': [{ kind: 'success', content: happyValidator }],
    'partial_failure:logs_analyst': [{ kind: 'success', content: happyLogs }],
    'partial_failure:metrics_analyst': [
      { kind: 'permanent_failure', message: 'metrics backend unreachable' },
    ],
    'partial_failure:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'partial_failure:critic': [{ kind: 'success', content: happyCritic }],
    'partial_failure:synthesizer': [{ kind: 'success', content: partialReport }],

    'retry:validator': [{ kind: 'success', content: happyValidator }],
    'retry:logs_analyst': [
      { kind: 'transient_failure', message: 'temporary rate limit' },
      { kind: 'transient_failure', message: 'temporary rate limit' },
      { kind: 'success', content: happyLogs },
    ],
    'retry:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'retry:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'retry:critic': [{ kind: 'success', content: happyCritic }],
    'retry:synthesizer': [{ kind: 'success', content: happyReport }],

    'invalid_output:validator': [{ kind: 'success', content: happyValidator }],
    'invalid_output:logs_analyst': [{ kind: 'success', content: happyLogs }],
    'invalid_output:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'invalid_output:deployment_analyst': [
      { kind: 'invalid_json', content: '{not-valid-json' },
      { kind: 'repair_success', content: happyDeploy },
    ],
    'invalid_output:critic': [{ kind: 'success', content: happyCritic }],
    'invalid_output:synthesizer': [{ kind: 'success', content: happyReport }],

    'timeout:validator': [{ kind: 'success', content: happyValidator }],
    'timeout:logs_analyst': [{ kind: 'timeout', delayMs: 30_000 }],
    'timeout:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'timeout:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'timeout:critic': [{ kind: 'success', content: happyCritic }],
    'timeout:synthesizer': [{ kind: 'success', content: partialReport }],

    'contradiction:validator': [{ kind: 'success', content: happyValidator }],
    'contradiction:logs_analyst': [{ kind: 'success', content: happyLogs }],
    'contradiction:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'contradiction:deployment_analyst': [{ kind: 'success', content: contradictionDeploy }],
    'contradiction:critic': [{ kind: 'success', content: contradictionCritic }],
    'contradiction:synthesizer': [{ kind: 'success', content: contradictionReport }],

    'cancellation:validator': [{ kind: 'success', content: happyValidator, delayMs: 50 }],
    'cancellation:logs_analyst': [{ kind: 'success', content: happyLogs, delayMs: 5_000 }],
    'cancellation:metrics_analyst': [{ kind: 'success', content: happyMetrics, delayMs: 5_000 }],
    'cancellation:deployment_analyst': [{ kind: 'success', content: happyDeploy, delayMs: 5_000 }],
    'cancellation:critic': [{ kind: 'success', content: happyCritic }],
    'cancellation:synthesizer': [{ kind: 'success', content: happyReport }],

    'restart:validator': [{ kind: 'success', content: happyValidator }],
    'restart:logs_analyst': [{ kind: 'success', content: happyLogs, delayMs: 2_000 }],
    'restart:metrics_analyst': [{ kind: 'success', content: happyMetrics, delayMs: 2_000 }],
    'restart:deployment_analyst': [{ kind: 'success', content: happyDeploy, delayMs: 2_000 }],
    'restart:critic': [{ kind: 'success', content: happyCritic }],
    'restart:synthesizer': [{ kind: 'success', content: happyReport }],

    'duplicate:validator': [{ kind: 'success', content: happyValidator }],
    'duplicate:logs_analyst': [{ kind: 'success', content: happyLogs }],
    'duplicate:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'duplicate:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'duplicate:critic': [{ kind: 'success', content: happyCritic }],
    'duplicate:synthesizer': [{ kind: 'success', content: happyReport }],

    'invalid_citation:validator': [{ kind: 'success', content: happyValidator }],
    'invalid_citation:logs_analyst': [
      { kind: 'invalid_json', content: invalidCitationLogs },
      { kind: 'repair_success', content: repairedLogs },
    ],
    'invalid_citation:metrics_analyst': [{ kind: 'success', content: happyMetrics }],
    'invalid_citation:deployment_analyst': [{ kind: 'success', content: happyDeploy }],
    'invalid_citation:critic': [{ kind: 'success', content: happyCritic }],
    'invalid_citation:synthesizer': [{ kind: 'success', content: happyReport }],
  };

  return scripts;
}

export const SCENARIO_INCIDENTS: Record<string, IncidentInput> = {
  happy: { ...baseIncident, scenarioId: 'happy' },
  partial_failure: { ...baseIncident, scenarioId: 'partial_failure' },
  retry: { ...baseIncident, scenarioId: 'retry' },
  invalid_output: { ...baseIncident, scenarioId: 'invalid_output' },
  timeout: { ...baseIncident, scenarioId: 'timeout' },
  contradiction: { ...baseIncident, scenarioId: 'contradiction' },
  cancellation: { ...baseIncident, scenarioId: 'cancellation' },
  restart: { ...baseIncident, scenarioId: 'restart' },
  duplicate: { ...baseIncident, scenarioId: 'duplicate' },
  invalid_citation: { ...baseIncident, scenarioId: 'invalid_citation' },
};
