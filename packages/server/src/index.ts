import { buildApp } from './app.js';

const port = Number(process.env.PORT ?? 3001);
const host = process.env.HOST ?? '0.0.0.0';

const { app } = await buildApp({
  databaseUrl: process.env.DATABASE_URL ?? './data/opsswarm.db',
  autoResume: true,
});

await app.listen({ port, host });
app.log.info(`OpsSwarm API listening on http://${host}:${port}`);
