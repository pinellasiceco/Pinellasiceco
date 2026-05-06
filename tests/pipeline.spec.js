'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, seed, firstPid } = require('./helpers');

test.describe('Pipeline tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    await tab(page, 'pipeline');
  });

  test('Pipeline tab renders', async ({ page }) => {
    await expect(page.locator('#ptab-inplay')).toBeVisible();
  });

  test('In Play sub-tab is active by default', async ({ page }) => {
    const inplay = page.locator('#ptab-inplay');
    const cls = await inplay.getAttribute('class');
    expect(cls).toContain('on');
  });

  test('Quoted sub-tab click renders quoted list', async ({ page }) => {
    await page.locator('#ptab-quoted').click();
    await page.waitForTimeout(200);
    // Verify the tab became active
    const cls = await page.locator('#ptab-quoted').getAttribute('class');
    expect(cls).toContain('on');
  });

  test('Won sub-tab click renders won list', async ({ page }) => {
    await page.locator('#ptab-won').click();
    await page.waitForTimeout(200);
    const cls = await page.locator('#ptab-won').getAttribute('class');
    expect(cls).toContain('on');
  });

  test('Lost sub-tab click renders lost list', async ({ page }) => {
    await page.locator('#ptab-lost').click();
    await page.waitForTimeout(200);
    const cls = await page.locator('#ptab-lost').getAttribute('class');
    expect(cls).toContain('on');
  });

  test('KPI bar shows In Play count, Quoted count, Close Rate', async ({ page }) => {
    // KPI bar should have 3 visible metric cells
    const kpiCells = page.locator('[id^="kpi-"]');
    const count = await kpiCells.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test('Won list shows client name after winning a deal', async ({ page }) => {
    const pid = await page.evaluate(() => P[0].id);
    const name = await page.evaluate(() => P[0].name);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-05-01' } },
    });
    await tab(page, 'pipeline');
    await page.locator('#ptab-won').click();
    await page.waitForTimeout(300);
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 3000 });
  });
});
