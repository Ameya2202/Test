import cors from '@fastify/cors';
import Fastify from 'fastify';
import {
  CreateRunRequestSchema,
  ScriptedModelClient,
  buildScenarioScripts,
  SCENARIO_INCIDENTS,
  type PipelineEvent,
} from '@opsswarm/shared';
import { createDb } from './db/client.js';
import { RunRepository } from './db/repository.js';
import { PipelineOrchestrator } from './orchestrator/pipeline.js';

export interface BuildAppOptions {
  databaseUrl?: string;
  modelClient?: ScriptedModelClient;
  autoResume?: boolean;
}

export async function buildApp(options: BuildAppOptions = {}) {
  const { db } = createDb(options.databaseUrl ?? process.env.DATABASE_URL ?? './data/opsswarm.db');
  const repository = new RunRepository(db);
  const modelClient =
    options.modelClient ??
    new ScriptedModelClient({
      scripts: buildScenarioScripts(),
      defaultDelayMs: 10,
    });
  const orchestrator = new PipelineOrchestrator({
    modelClient,
    repository,
    backoffBaseMs: Number(process.env.BACKOFF_BASE_MS ?? 25),
  });

  const app = Fastify({ logger: process.env.NODE_ENV !== 'test' });
  await app.register(cors, { origin: true });

  app.decorate('repository', repository);
  app.decorate('orchestrator', orchestrator);
  app.decorate('modelClient', modelClient);

  app.get('/api/health', async () => ({ ok: true }));

  app.get('/api/scenarios', async () => ({
    scenarios: Object.keys(SCENARIO_INCIDENTS),
  }));

  app.get('/api/scenarios/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const incident = SCENARIO_INCIDENTS[id];
    if (!incident) {
      return reply.code(404).send({ error: 'scenario not found' });
    }
    return { id, incident };
  });

  app.get('/api/runs', async () => {
    const runs = repository.listRuns().map(serializeRun);
    return { runs };
  });

  app.post('/api/runs', async (request, reply) => {
    const parsed = CreateRunRequestSchema.safeParse(request.body);
    if (!parsed.success) {
      return reply.code(400).send({ error: parsed.error.flatten() });
    }

    const existing = parsed.data.idempotencyKey
      ? repository.findByIdempotencyKey(parsed.data.idempotencyKey)
      : null;

    const run = repository.createRun(parsed.data);
    const created = !existing || existing.id !== run.id ? existing == null : false;
    // Idempotent replay: if key existed, do not restart
    if (!existing) {
      void orchestrator.startRun(run.id);
      return reply.code(201).send({ run: serializeRun(run), steps: repository.getSteps(run.id) });
    }

    return reply.code(200).send({
      run: serializeRun(run),
      steps: repository.getSteps(run.id),
      idempotentReplay: true,
      created,
    });
  });

  app.get('/api/runs/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const run = repository.getRun(id);
    if (!run) return reply.code(404).send({ error: 'run not found' });
    return {
      run: serializeRun(run),
      steps: repository.getSteps(id),
      events: repository.listEvents(id),
    };
  });

  app.post('/api/runs/:id/cancel', async (request, reply) => {
    const { id } = request.params as { id: string };
    const run = repository.getRun(id);
    if (!run) return reply.code(404).send({ error: 'run not found' });
    orchestrator.cancelRun(id);
    return { run: serializeRun(repository.getRun(id)!) };
  });

  app.get('/api/runs/:id/events', async (request, reply) => {
    const { id } = request.params as { id: string };
    const run = repository.getRun(id);
    if (!run) return reply.code(404).send({ error: 'run not found' });
    return { events: repository.listEvents(id) };
  });

  app.get('/api/runs/:id/stream', async (request, reply) => {
    const { id } = request.params as { id: string };
    const run = repository.getRun(id);
    if (!run) return reply.code(404).send({ error: 'run not found' });

    reply.hijack();
    reply.raw.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });

    const send = (event: PipelineEvent) => {
      reply.raw.write(`id: ${event.id}\n`);
      reply.raw.write(`event: ${event.type}\n`);
      reply.raw.write(`data: ${JSON.stringify(event)}\n\n`);
    };

    // Replay existing events
    for (const event of repository.listEvents(id)) {
      send(event);
    }

    const unsubscribe = orchestrator.onEvent((event) => {
      if (event.runId === id) send(event);
    });

    const heartbeat = setInterval(() => {
      reply.raw.write(`: heartbeat\n\n`);
    }, 15_000);

    const cleanup = () => {
      clearInterval(heartbeat);
      unsubscribe();
    };

    request.raw.on('close', cleanup);
    reply.raw.on('close', cleanup);
  });

  app.get('/api/pipeline/graph', async () => ({
    nodes: [
      { id: 'validate', label: 'Evidence Validator' },
      { id: 'logs_analyst', label: 'Logs Analyst' },
      { id: 'metrics_analyst', label: 'Metrics Analyst' },
      { id: 'deployment_analyst', label: 'Deployment Analyst' },
      { id: 'critic', label: 'Skeptic / Critic' },
      { id: 'synthesizer', label: 'Report Synthesizer' },
    ],
    edges: [
      { from: 'validate', to: 'logs_analyst' },
      { from: 'validate', to: 'metrics_analyst' },
      { from: 'validate', to: 'deployment_analyst' },
      { from: 'logs_analyst', to: 'critic' },
      { from: 'metrics_analyst', to: 'critic' },
      { from: 'deployment_analyst', to: 'critic' },
      { from: 'critic', to: 'synthesizer' },
    ],
  }));

  if (options.autoResume !== false && process.env.NODE_ENV !== 'test') {
    await orchestrator.resumeUnfinishedRuns();
  }

  return { app, repository, orchestrator, modelClient, db };
}

function serializeRun(run: ReturnType<RunRepository['getRun']>) {
  if (!run) return null;
  return {
    id: run.id,
    idempotencyKey: run.idempotencyKey,
    status: run.status,
    scenarioId: run.scenarioId,
    incident: run.incident,
    options: run.options,
    report: run.report,
    errorMessage: run.errorMessage,
    createdAt: run.createdAt,
    updatedAt: run.updatedAt,
    startedAt: run.startedAt,
    finishedAt: run.finishedAt,
    cancelRequested: run.cancelRequested,
  };
}

declare module 'fastify' {
  interface FastifyInstance {
    repository: RunRepository;
    orchestrator: PipelineOrchestrator;
    modelClient: ScriptedModelClient;
  }
}
