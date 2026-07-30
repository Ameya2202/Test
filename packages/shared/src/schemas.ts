import { z } from 'zod';

export const SeveritySchema = z.enum(['SEV1', 'SEV2', 'SEV3', 'SEV4']);
export type Severity = z.infer<typeof SeveritySchema>;

export const LogEntrySchema = z.object({
  evidenceId: z.string().min(1),
  timestamp: z.string().datetime(),
  level: z.enum(['debug', 'info', 'warn', 'error', 'fatal']),
  message: z.string(),
  service: z.string().optional(),
  attributes: z.record(z.unknown()).optional(),
});
export type LogEntry = z.infer<typeof LogEntrySchema>;

export const MetricSnapshotSchema = z.object({
  evidenceId: z.string().min(1),
  timestamp: z.string().datetime(),
  name: z.string(),
  value: z.number(),
  unit: z.string().optional(),
  labels: z.record(z.string()).optional(),
});
export type MetricSnapshot = z.infer<typeof MetricSnapshotSchema>;

export const DeploymentSchema = z.object({
  evidenceId: z.string().min(1),
  timestamp: z.string().datetime(),
  service: z.string(),
  version: z.string(),
  environment: z.string(),
  changeSummary: z.string(),
  author: z.string().optional(),
});
export type Deployment = z.infer<typeof DeploymentSchema>;

export const ConfigChangeSchema = z.object({
  evidenceId: z.string().min(1),
  timestamp: z.string().datetime(),
  service: z.string(),
  key: z.string(),
  oldValue: z.string().nullable(),
  newValue: z.string(),
  author: z.string().optional(),
});
export type ConfigChange = z.infer<typeof ConfigChangeSchema>;

export const IncidentInputSchema = z.object({
  serviceName: z.string().min(1),
  severity: SeveritySchema,
  alertDescription: z.string().min(1),
  occurredAt: z.string().datetime(),
  logs: z.array(LogEntrySchema).default([]),
  metrics: z.array(MetricSnapshotSchema).default([]),
  deployments: z.array(DeploymentSchema).default([]),
  configChanges: z.array(ConfigChangeSchema).default([]),
  scenarioId: z.string().optional(),
});
export type IncidentInput = z.infer<typeof IncidentInputSchema>;

export const AgentRoleSchema = z.enum([
  'validator',
  'logs_analyst',
  'metrics_analyst',
  'deployment_analyst',
  'critic',
  'synthesizer',
]);
export type AgentRole = z.infer<typeof AgentRoleSchema>;

export const PipelineStepNameSchema = z.enum([
  'validate',
  'logs_analyst',
  'metrics_analyst',
  'deployment_analyst',
  'critic',
  'synthesizer',
]);
export type PipelineStepName = z.infer<typeof PipelineStepNameSchema>;

export const StepStatusSchema = z.enum([
  'pending',
  'running',
  'succeeded',
  'failed',
  'timed_out',
  'cancelled',
  'skipped',
]);
export type StepStatus = z.infer<typeof StepStatusSchema>;

export const RunStatusSchema = z.enum([
  'pending',
  'running',
  'completed',
  'failed',
  'cancelled',
  'partial',
]);
export type RunStatus = z.infer<typeof RunStatusSchema>;

export const FindingSchema = z.object({
  summary: z.string(),
  confidence: z.number().min(0).max(1),
  evidenceIds: z.array(z.string()).min(1),
  details: z.string().optional(),
});
export type Finding = z.infer<typeof FindingSchema>;

export const AnalystOutputSchema = z.object({
  role: z.enum(['logs_analyst', 'metrics_analyst', 'deployment_analyst']),
  findings: z.array(FindingSchema),
  hypotheses: z.array(z.string()).default([]),
  evidenceIds: z.array(z.string()).default([]),
});
export type AnalystOutput = z.infer<typeof AnalystOutputSchema>;

export const CriticOutputSchema = z.object({
  contradictions: z.array(
    z.object({
      description: z.string(),
      relatedEvidenceIds: z.array(z.string()).default([]),
      conflictingClaims: z.array(z.string()).default([]),
    }),
  ),
  unsupportedClaims: z.array(
    z.object({
      claim: z.string(),
      reason: z.string(),
      evidenceIds: z.array(z.string()).default([]),
    }),
  ),
  notes: z.array(z.string()).default([]),
});
export type CriticOutput = z.infer<typeof CriticOutputSchema>;

export const IncidentReportSchema = z.object({
  executiveSummary: z.string(),
  mostLikelyRootCause: z.string(),
  confidenceScore: z.number().min(0).max(1),
  supportingEvidence: z.array(
    z.object({
      claim: z.string(),
      evidenceIds: z.array(z.string()).min(1),
    }),
  ),
  contradictoryEvidence: z.array(
    z.object({
      description: z.string(),
      evidenceIds: z.array(z.string()).default([]),
    }),
  ),
  recommendedImmediateActions: z.array(z.string()),
  longerTermRemediation: z.array(z.string()),
  unknownsAndFollowUps: z.array(z.string()),
  partial: z.boolean().default(false),
  failedAgents: z.array(z.string()).default([]),
});
export type IncidentReport = z.infer<typeof IncidentReportSchema>;

export const ValidatorOutputSchema = z.object({
  valid: z.boolean(),
  evidenceIds: z.array(z.string()),
  issues: z.array(z.string()).default([]),
});
export type ValidatorOutput = z.infer<typeof ValidatorOutputSchema>;

export const ModelRequestSchema = z.object({
  role: AgentRoleSchema,
  scenarioId: z.string(),
  prompt: z.string(),
  attempt: z.number().int().nonnegative(),
  repair: z.boolean().default(false),
  context: z.record(z.unknown()).optional(),
});
export type ModelRequest = z.infer<typeof ModelRequestSchema>;

export const ModelResponseSchema = z.object({
  content: z.string(),
  tokenUsage: z.object({
    promptTokens: z.number().int().nonnegative(),
    completionTokens: z.number().int().nonnegative(),
  }),
  latencyMs: z.number().int().nonnegative().optional(),
});
export type ModelResponse = z.infer<typeof ModelResponseSchema>;

export interface ModelClient {
  generate(request: ModelRequest): Promise<ModelResponse>;
}

export const PipelineEventTypeSchema = z.enum([
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
]);
export type PipelineEventType = z.infer<typeof PipelineEventTypeSchema>;

export const PipelineEventSchema = z.object({
  id: z.string(),
  runId: z.string(),
  type: PipelineEventTypeSchema,
  stepName: PipelineStepNameSchema.optional(),
  attempt: z.number().int().optional(),
  message: z.string(),
  payload: z.record(z.unknown()).optional(),
  createdAt: z.string().datetime(),
});
export type PipelineEvent = z.infer<typeof PipelineEventSchema>;

export const CreateRunRequestSchema = z.object({
  incident: IncidentInputSchema,
  idempotencyKey: z.string().min(1).optional(),
  options: z
    .object({
      concurrencyLimit: z.number().int().min(1).max(10).default(3),
      stepTimeoutMs: z.number().int().min(100).default(10_000),
      maxRetries: z.number().int().min(0).max(5).default(2),
      scenarioId: z.string().optional(),
    })
    .optional(),
});
export type CreateRunRequest = z.infer<typeof CreateRunRequestSchema>;

export const INVESTIGATION_STEPS = [
  'logs_analyst',
  'metrics_analyst',
  'deployment_analyst',
] as const satisfies readonly PipelineStepName[];

export const PIPELINE_GRAPH = {
  validate: { next: [...INVESTIGATION_STEPS] },
  logs_analyst: { next: ['critic'] as const, parallelGroup: 'investigate' },
  metrics_analyst: { next: ['critic'] as const, parallelGroup: 'investigate' },
  deployment_analyst: { next: ['critic'] as const, parallelGroup: 'investigate' },
  critic: { next: ['synthesizer'] as const },
  synthesizer: { next: [] as const },
} as const;

export function collectEvidenceIds(incident: IncidentInput): Set<string> {
  const ids = new Set<string>();
  for (const item of incident.logs) ids.add(item.evidenceId);
  for (const item of incident.metrics) ids.add(item.evidenceId);
  for (const item of incident.deployments) ids.add(item.evidenceId);
  for (const item of incident.configChanges) ids.add(item.evidenceId);
  return ids;
}

export function roleForStep(step: PipelineStepName): AgentRole {
  switch (step) {
    case 'validate':
      return 'validator';
    case 'logs_analyst':
      return 'logs_analyst';
    case 'metrics_analyst':
      return 'metrics_analyst';
    case 'deployment_analyst':
      return 'deployment_analyst';
    case 'critic':
      return 'critic';
    case 'synthesizer':
      return 'synthesizer';
  }
}
