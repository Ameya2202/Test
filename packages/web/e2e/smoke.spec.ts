import { test, expect } from '@playwright/test';

test('happy path shows pipeline progress and final report', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Ops/i })).toBeVisible();
  await page.getByTestId('scenario-select').selectOption('happy');
  await page.getByTestId('start-run').click();
  await expect(page.getByTestId('run-id')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId('incident-report')).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId('incident-report')).toContainText('Executive summary');
  await expect(page.getByTestId('node-synthesizer')).toHaveAttribute('data-status', 'succeeded', {
    timeout: 20_000,
  });
});

test('cancellation control is available during a slow scenario', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('scenario-select').selectOption('cancellation');
  await page.getByTestId('start-run').click();
  await expect(page.getByTestId('run-id')).toBeVisible({ timeout: 15_000 });
  await page.getByTestId('cancel-run').click();
  await expect(page.getByText(/cancelled/i).first()).toBeVisible({ timeout: 20_000 });
});
