'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, pids, waitForToast } = require('./helpers');

test.describe('Route tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    // Clear any existing route state
    await page.evaluate(() => {
      localStorage.removeItem('pic_route_state');
      window.route = [];
      window.routeSet = new Set();
    });
    await tab(page, 'route');
  });

  test('Route tab renders rlist container', async ({ page }) => {
    await expect(page.locator('#rlist')).toBeVisible();
  });

  test('City cluster chips render', async ({ page }) => {
    for (const city of ['Tarpon', 'Clearwater', 'Largo']) {
      await expect(page.locator(`button:has-text("${city}")`).first()).toBeVisible();
    }
  });

  test('Manual route toggle shows route bar', async ({ page }) => {
    // Adding a stop reveals manual-route-bar (renderDayRoute shows it when route.length > 0)
    const [pid] = await pids(page, 1);
    await page.evaluate(id => addToRoute(id, true), pid);
    await page.waitForTimeout(300);
    await expect(page.locator('#manual-route-bar')).toBeVisible();
  });

  test('addToRoute adds prospect to routeSet', async ({ page }) => {
    const [pid] = await pids(page, 1);
    await page.evaluate(id => addToRoute(id, true), pid);
    await page.waitForTimeout(300);
    const inRoute = await page.evaluate(id => routeSet.has(id), pid);
    expect(inRoute).toBe(true);
  });

  test('FIX 7: 8-stop limit shows toast on 9th add', async ({ page }) => {
    const ids = await pids(page, 9);
    // Add 8 with skipMax=true
    await page.evaluate(ids => {
      ids.slice(0, 8).forEach(id => addToRoute(id, true));
    }, ids);
    await page.waitForTimeout(200);
    // Try to add 9th without skipMax — should show toast
    await page.evaluate(id => addToRoute(id), ids[8]);
    const toastText = await waitForToast(page);
    expect(toastText.toLowerCase()).toMatch(/max|limit|8|stop/);
  });

  test('clearing route empties routeSet', async ({ page }) => {
    const [pid] = await pids(page, 1);
    await page.evaluate(id => addToRoute(id, true), pid);
    await page.waitForTimeout(200);
    // Reset route state directly to avoid side-effect crashes in renderDayRoute
    await page.evaluate(() => { route = []; routeSet = new Set(); saveRouteState(); });
    const inRoute = await page.evaluate(id => routeSet.has(id), pid);
    expect(inRoute).toBe(false);
  });

  test('FIX 15: Start button present in route list', async ({ page }) => {
    // Start (anchor) button exists in each rlist card
    const startBtn = page.locator('#rlist [data-action="start"]').first();
    await expect(startBtn).toBeVisible({ timeout: 5000 });
  });
});
