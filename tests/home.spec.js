'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, seed, firstPid } = require('./helpers');

test.describe('Home tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
  });

  test('page loads without uncaught JS errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.reload();
    await page.waitForFunction(() => typeof P !== 'undefined' && P.length > 0);
    expect(errors).toHaveLength(0);
  });

  test('TODAY\'S PLAN section renders', async ({ page }) => {
    await tab(page, 'today');
    // Plan section heading or list container
    const planSection = page.locator('text=TODAY\'S PLAN').or(page.locator('#plan-list')).first();
    await expect(planSection).toBeVisible({ timeout: 5000 });
  });

  test('Strike Zone section renders', async ({ page }) => {
    await tab(page, 'today');
    const strike = page.locator('text=Strike Zone').or(page.locator('text=STRIKE ZONE')).first();
    await expect(strike).toBeVisible({ timeout: 5000 });
  });

  test('Add All to Route button exists on Home tab', async ({ page }) => {
    await tab(page, 'today');
    const btn = page.locator('button', { hasText: /Add All/i }).first();
    await expect(btn).toBeVisible({ timeout: 5000 });
  });

  test('In Play follow-ups section renders when data exists', async ({ page }) => {
    const pid = await firstPid(page);
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    await seed(page, {
      pic_v4: { [pid]: [{ date: yesterday, outcome: 'in_play', followup: yesterday, notes: '' }] },
    });
    await tab(page, 'today');
    // Should have an Overdue/Today/Week section or just follow-up items
    const section = page.locator('text=Overdue').or(page.locator('text=Follow')).first();
    await expect(section).toBeVisible({ timeout: 5000 });
  });
});
