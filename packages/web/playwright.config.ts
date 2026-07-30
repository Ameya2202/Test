import { defineConfig, devices } from '@playwright/test';

const port = Number(process.env.E2E_PORT ?? 4173);
const apiPort = Number(process.env.E2E_API_PORT ?? 3001);

export default defineConfig({
  testDir: '../../e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `DATABASE_URL=./data/e2e.db PORT=${apiPort} pnpm --filter @opsswarm/server exec tsx src/index.ts`,
      url: `http://127.0.0.1:${apiPort}/api/health`,
      reuseExistingServer: !process.env.CI,
      cwd: '../..',
      timeout: 120_000,
    },
    {
      command: `pnpm exec vite preview --host 127.0.0.1 --port ${port}`,
      url: `http://127.0.0.1:${port}`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
