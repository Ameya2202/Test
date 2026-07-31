# Future Enhancements

Realistic improvements that build on the **current** OpsSwarm implementation without rewriting the core durable orchestrator.

---

## Near-term (low risk)

1. **Add `.env.example`** documenting `DATABASE_URL`, `PORT`, `HOST`, `BACKOFF_BASE_MS`, `VITE_API_PROXY`.
2. **Implement `packages/server/src/db/migrate.ts`** (or drop the script) and optionally check in Drizzle SQL migrations.
3. **Run history UI** using existing `GET /api/runs` + run detail navigation.
4. **Evidence panel** showing incident logs/metrics/deployments/config for the active run.
5. **Screenshot capture** into `screenshots/` referenced by README.
6. **Remove or use `@fastify/static`** — either serve `web/dist` from the API for single-process deploys, or drop the unused dependency.
7. **CI workflow** running `pnpm install --frozen-lockfile`, lint, typecheck, test, build, and Playwright.

---

## Medium-term (architecture)

1. **Real `ModelClient` providers** (OpenAI/Anthropic/Azure) behind feature flags, keeping ScriptedModelClient as the default for tests.
2. **Extract a RunService layer** between Fastify routes and the orchestrator for clearer transaction boundaries.
3. **Event retention / compaction** jobs for long-lived SQLite deployments.
4. **OpenAPI document** generated from Zod schemas.
5. **Custom incident builder UI** (still validated by `IncidentInputSchema`) in addition to scenarios.
6. **Emit or remove `step_skipped`** to eliminate schema/runtime drift.

---

## Longer-term (productization)

1. **Authentication / tenancy** (API tokens or OIDC) and CORS lockdown.
2. **Postgres (or other shared SQL)** for multi-instance deployments with lease-based run ownership.
3. **Queue-backed workers** if investigation fan-out must survive multi-process scaling.
4. **Observability**: OpenTelemetry traces around steps/attempts; metrics for success/partial/cancel rates.
5. **Human-in-the-loop** gates before synthesizer publication.
6. **Evidence connectors** that pull live logs/metrics/deployments (today evidence is fixture/payload-only).

---

## Explicit non-goals (for now)

- Replacing the hand-rolled orchestrator with LangGraph/LangChain for the benchmark track
- Multi-region active-active SQLite
- Unbounded autonomous remediation that mutates production systems

---

## Related Documents

- [Architecture.md](../Architecture.md)
- [DeploymentGuide.md](./DeploymentGuide.md)
