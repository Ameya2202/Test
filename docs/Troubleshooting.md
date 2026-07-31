# Troubleshooting

Common issues when installing or running OpsSwarm, based on the actual stack.

---

## pnpm install failures

**Symptoms:** install aborts; native modules missing; “Ignored build scripts”.

**Checks:**

1. Node major is 24+ (`node -v`, `.nvmrc`).
2. pnpm is `10.33.3` via Corepack.
3. Rebuild allow-listed natives:

```bash
pnpm rebuild better-sqlite3
pnpm rebuild esbuild
```

4. On Linux, ensure build tools exist for node-gyp (`python3`, `make`, `g++`).

5. Prefer:

```bash
pnpm install --frozen-lockfile
```

---

## SQLite issues

**Symptoms:** cannot open database; `SQLITE_CANTOPEN`; empty schema.

**Checks:**

1. `DATABASE_URL` path is writable; parent directory can be created.
2. Default `./data/opsswarm.db` is relative to the **process working directory** (usually repo root when using pnpm filters).
3. Confirm WAL/files aren’t locked by another process.
4. For tests, use `:memory:` or a unique temp file.
5. Remember: schema is bootstrapped in `client.ts`; missing `migrate.ts` means `pnpm db:migrate` will fail if invoked.

---

## Port already in use

**Symptoms:** `EADDRINUSE` on `3001` or `5173`.

**Fixes:**

```bash
# find listeners (Linux)
netstat -tlnp | grep -E '3001|5173'
# or
ss -tlnp | grep -E '3001|5173'
```

Stop the old process, or override:

```bash
PORT=3002 pnpm --filter @opsswarm/server dev
VITE_API_PROXY=http://127.0.0.1:3002 pnpm --filter @opsswarm/web dev
```

For Vite, also ensure you are not colliding with a previous preview on `4173`.

---

## Missing environment variables

OpsSwarm has defaults for all critical settings. “Missing env” is rarely fatal.

If something looks wrong:

| Expectation | Variable |
|---|---|
| DB location | `DATABASE_URL` |
| API port/host | `PORT`, `HOST` |
| Retry timing | `BACKOFF_BASE_MS` |
| UI → API proxy | `VITE_API_PROXY` |

There is **no** required API key because real LLM providers are not wired by default.

---

## Frontend cannot reach API / ERR_CONNECTION_RESET

**Local process healthy but browser fails:** often a port-forward / tunnel issue (for example cloud agent → laptop), not an app crash.

**Fast checks:**

1. From the machine running Node: `curl http://127.0.0.1:3001/api/health`
2. `curl http://127.0.0.1:5173/` (Vite must bind IPv4; use `--host 0.0.0.0` if needed)
3. Prefer `http://127.0.0.1:5173` over `localhost` if IPv6 `::1` is refused
4. Confirm Vite proxy target matches the API port

---

## Runs fail immediately on analysts / synthesizer

**Common cause:** posting a hand-built incident that lacks evidence IDs cited by fixtures (for example missing `log-003`).

**Fix:** create runs from `GET /api/scenarios/:id` fixtures, or include the full evidence set from `baseIncident`.

---

## Idempotency surprises

Posting the same `idempotencyKey` returns the **existing** run without restarting. Use a new key to force a fresh pipeline.

---

## Playwright e2e failures

1. Install browsers: `pnpm --filter @opsswarm/web exec playwright install chromium`
2. Ensure `pnpm build` (or at least web build) succeeded before preview-based e2e
3. Ensure ports `3001` / `4173` are free
4. Run with `CI=1 pnpm test:e2e` for non-reuse of existing servers

---

## TypeScript / lint failures after edits

```bash
pnpm --filter @opsswarm/shared build   # server depends on shared dist types
pnpm typecheck
pnpm lint
```

Root package is `"type": "module"`; keep ESM import suffixes in server/shared source as authored.

---

## Docker issues

1. Build context must include `pnpm-lock.yaml`
2. API data persists in volume `opsswarm-data`
3. Browser should use Compose UI on `:8080` (nginx proxies `/api`), not Vite `:5173`, unless also running local Vite

---

## Related Documents

- [InstallationGuide.md](./InstallationGuide.md)
- [ConfigurationGuide.md](./ConfigurationGuide.md)
- [DeploymentGuide.md](./DeploymentGuide.md)
