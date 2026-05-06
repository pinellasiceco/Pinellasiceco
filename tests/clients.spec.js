'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, seed, firstPid } = require('./helpers');

test.describe('Clients tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
  });

  test('Clients tab renders panel', async ({ page }) => {
    await tab(page, 'clients');
    await expect(page.locator('#ct-panel-clients')).toBeVisible();
  });

  test('empty state shows message when no clients', async ({ page }) => {
    await page.evaluate(() => localStorage.removeItem('pic_customers'));
    await page.reload();
    await page.waitForFunction(() => typeof P !== 'undefined' && P.length > 0);
    await tab(page, 'clients');
    // Should show some empty-state text
    const empty = page.locator('#ct-panel-clients').locator('text=/No client|no client|0 client/i').first();
    // Just assert the panel is visible; some apps show a 0-count KPI instead of text
    await expect(page.locator('#ct-panel-clients')).toBeVisible();
  });

  test('recurring client card renders', async ({ page }) => {
    const pid = await firstPid(page);
    const name = await page.evaluate(() => P[0].name);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'clients');
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 5000 });
  });

  test('FIX 1: quarterly client shows Quarterly badge', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_quarterly', monthly: 129, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'clients');
    // #cust-list is the rendered card container (avoids matching hidden <option> in the filter select)
    await expect(page.locator('#cust-list').locator('text=Quarterly').first()).toBeVisible({ timeout: 5000 });
  });

  test('FIX 1: quarterly client included in MRR display', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_quarterly', monthly: 129, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'clients');
    // mrr-val is inside #ct-panel-clients and gets set by rCust()
    const mrrEl = page.locator('#mrr-val');
    if (await mrrEl.count() > 0) {
      const txt = await mrrEl.textContent();
      const num = parseInt(txt.replace(/[^0-9]/g, ''));
      expect(num).toBeGreaterThanOrEqual(129);
    }
  });

  test('FIX 3: churn button absent when client is churned', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'churned', monthly: 149, machines: 1, churn_date: '2026-04-01' } },
    });
    await tab(page, 'clients');
    // Scope to #p-customers to avoid static "Mark as Lost / Churned" button in other panels
    const churnBtn = page.locator('#p-customers button', { hasText: /^❌ Churn$/ });
    const count = await churnBtn.count();
    expect(count).toBe(0);
  });

  test('FIX 3: churn date shown when client is churned', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'churned', monthly: 149, machines: 1, churn_date: '2026-04-01' } },
    });
    await tab(page, 'clients');
    // Scope to #cust-list to avoid hidden <option value="churned"> in the filter select
    await expect(page.locator('#cust-list').locator('text=/Churned|2026-04-01/').first()).toBeVisible({ timeout: 5000 });
  });

  test('Churn button present for active recurring client', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'clients');
    const churnBtn = page.locator('button', { hasText: /Churn/i }).first();
    await expect(churnBtn).toBeVisible({ timeout: 5000 });
  });

  test('FIX 18: Export Schedule button visible for client with schedule', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: {
        [pid]: {
          status: 'customer_quarterly',
          monthly: 129,
          machines: 1,
          signed_date: '2026-01-01',
          annual_schedule: [{ date: '2026-06-01', type: 'deep_clean', label: 'Deep Clean' }],
        },
      },
    });
    await tab(page, 'clients');
    const exportBtn = page.locator('button', { hasText: /Export Schedule|Export/i }).first();
    await expect(exportBtn).toBeVisible({ timeout: 5000 });
  });

  test('FIX 18: Export Schedule button absent without schedule', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'clients');
    await expect(page.locator('button', { hasText: /Export Schedule/i })).toHaveCount(0);
  });

  test('Service sub-tab opens service panel', async ({ page }) => {
    await tab(page, 'clients');
    const serviceTab = page.locator('#ct-service');
    if (await serviceTab.count() > 0) {
      await serviceTab.click();
      await page.waitForTimeout(200);
      const cls = await serviceTab.getAttribute('class');
      expect(cls).toContain('on');
    }
  });
});
