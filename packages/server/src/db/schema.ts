import { integer, sqliteTable, text, index, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const runs = sqliteTable(
  'runs',
  {
    id: text('id').primaryKey(),
    idempotencyKey: text('idempotency_key'),
    status: text('status').notNull(),
    scenarioId: text('scenario_id').notNull(),
    incidentJson: text('incident_json').notNull(),
    optionsJson: text('options_json').notNull(),
    reportJson: text('report_json'),
    errorMessage: text('error_message'),
    createdAt: text('created_at').notNull(),
    updatedAt: text('updated_at').notNull(),
    startedAt: text('started_at'),
    finishedAt: text('finished_at'),
    cancelRequested: integer('cancel_requested', { mode: 'boolean' }).notNull().default(false),
  },
  (t) => [uniqueIndex('runs_idempotency_key_uidx').on(t.idempotencyKey)],
);

export const steps = sqliteTable(
  'steps',
  {
    id: text('id').primaryKey(),
    runId: text('run_id')
      .notNull()
      .references(() => runs.id),
    name: text('name').notNull(),
    status: text('status').notNull(),
    attempt: integer('attempt').notNull().default(0),
    maxAttempts: integer('max_attempts').notNull().default(3),
    outputJson: text('output_json'),
    errorMessage: text('error_message'),
    tokenPrompt: integer('token_prompt').notNull().default(0),
    tokenCompletion: integer('token_completion').notNull().default(0),
    durationMs: integer('duration_ms'),
    startedAt: text('started_at'),
    finishedAt: text('finished_at'),
    createdAt: text('created_at').notNull(),
    updatedAt: text('updated_at').notNull(),
  },
  (t) => [index('steps_run_id_idx').on(t.runId), uniqueIndex('steps_run_name_uidx').on(t.runId, t.name)],
);

export const stepAttempts = sqliteTable(
  'step_attempts',
  {
    id: text('id').primaryKey(),
    stepId: text('step_id')
      .notNull()
      .references(() => steps.id),
    attempt: integer('attempt').notNull(),
    status: text('status').notNull(),
    isRepair: integer('is_repair', { mode: 'boolean' }).notNull().default(false),
    inputJson: text('input_json'),
    outputJson: text('output_json'),
    errorMessage: text('error_message'),
    tokenPrompt: integer('token_prompt').notNull().default(0),
    tokenCompletion: integer('token_completion').notNull().default(0),
    durationMs: integer('duration_ms'),
    startedAt: text('started_at').notNull(),
    finishedAt: text('finished_at'),
  },
  (t) => [index('step_attempts_step_id_idx').on(t.stepId)],
);

export const events = sqliteTable(
  'events',
  {
    id: text('id').primaryKey(),
    runId: text('run_id')
      .notNull()
      .references(() => runs.id),
    type: text('type').notNull(),
    stepName: text('step_name'),
    attempt: integer('attempt'),
    message: text('message').notNull(),
    payloadJson: text('payload_json'),
    createdAt: text('created_at').notNull(),
  },
  (t) => [index('events_run_id_idx').on(t.runId)],
);
