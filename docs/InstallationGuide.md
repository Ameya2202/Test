# Installation Guide

How to install OpsSwarm from a clean machine using the **actual** repository tooling.

---

## Prerequisites

| Tool | Requirement | Notes |
|---|---|---|
| Node.js | `>= 24.0.0` | Pinned in `.nvmrc` as `24.18.1` |
| pnpm | `10.33.3` | Declared as `packageManager` in root `package.json` |
| Git | Any recent version | Required to clone |
| SQLite | Embedded | Provided by `better-sqlite3` (no standalone SQLite server) |
| Build toolchain | Native compile tools | Needed for `better-sqlite3` on first install |
| Docker (optional) | Docker Engine + Compose | For containerized deployment |

---

## Node.js Version

```bash
node -v
# Expected: v24.x (recommended v24.18.1)
```

Using nvm:

```bash
nvm install 24.18.1
nvm use
# reads .nvmrc → 24.18.1
```

---

## pnpm Version

Enable Corepack (ships with Node 24):

```bash
corepack enable
corepack prepare pnpm@10.33.3 --activate
pnpm -v
# Expected: 10.33.3
```

---

## SQLite

No separate install is required. OpsSwarm uses:

- Runtime driver: `better-sqlite3`
- ORM: `drizzle-orm`
- Default file path: `./data/opsswarm.db` (created automatically)

Ensure the process can create the `data/` directory (or set `DATABASE_URL`).

---

## Git

```bash
git --version
git clone <repository-url> opsswarm
cd opsswarm
```

---

## Install Commands

From the repository root:

```bash
# 1) Use the correct Node version
nvm use

# 2) Activate pnpm
corepack enable
corepack prepare pnpm@10.33.3 --activate

# 3) Install workspace dependencies (preferred for CI / reproducible installs)
pnpm install --frozen-lockfile
```

If there is no lockfile yet (should not happen on this repo):

```bash
pnpm install
```

### Native dependency note

`better-sqlite3` and `esbuild` are allow-listed under `pnpm.onlyBuiltDependencies` in the root `package.json`. If install skips build scripts, rebuild:

```bash
pnpm rebuild better-sqlite3
```

---

## Dependency Installation

The monorepo installs all packages together:

- Root tooling: ESLint, Prettier, TypeScript, typescript-eslint
- `@opsswarm/shared`
- `@opsswarm/server`
- `@opsswarm/web`

Workspace protocol: `"@opsswarm/shared": "workspace:*"`

---

## Environment Setup

OpsSwarm runs with defaults; a `.env` file is **not required**.

Optional overrides:

```bash
export DATABASE_URL=./data/opsswarm.db
export PORT=3001
export HOST=0.0.0.0
export BACKOFF_BASE_MS=25
```

For the Vite proxy (frontend only):

```bash
export VITE_API_PROXY=http://127.0.0.1:3001
```

See [ConfigurationGuide.md](./ConfigurationGuide.md).

---

## Verification Steps

```bash
pnpm build
pnpm lint
pnpm typecheck
pnpm test
```

Quick runtime smoke:

```bash
pnpm --filter @opsswarm/server dev
# in another shell:
curl http://127.0.0.1:3001/api/health
# → {"ok":true}
```

Playwright (optional for install verification):

```bash
pnpm --filter @opsswarm/web exec playwright install chromium
pnpm test:e2e
```

---

## Common Install Failures

See [Troubleshooting.md](./Troubleshooting.md) for:

- `pnpm install` failures / ignored build scripts
- `better-sqlite3` compile errors
- Wrong Node major version (`engines.node` rejects < 24)
