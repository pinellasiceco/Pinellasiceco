'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, firstPartnerId } = require('./helpers');

test.describe('Partners tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    await tab(page, 'partners');
  });

  test('Partners tab renders partner cards', async ({ page }) => {
    // PARTNERS[] is baked into the HTML — expect at least 1 card
    const cards = page.locator('.partner-card');
    await expect(cards.first()).toBeVisible({ timeout: 5000 });
  });

  test('Partner type filter chips render', async ({ page }) => {
    for (const chip of ['Hood', 'Pest', 'Refrig', 'HVAC', 'Beverage']) {
      const btn = page.locator(`button:has-text("${chip}")`).first();
      await expect(btn).toBeVisible();
    }
  });

  test('Partner filter by type narrows list', async ({ page }) => {
    const before = await page.locator('.partner-card').count();
    // Click Hood filter
    await page.locator('button:has-text("Hood")').first().click();
    await page.waitForTimeout(300);
    const after = await page.locator('.partner-card').count();
    expect(after).toBeLessThanOrEqual(before);
  });

  test('KPI bar shows partner metrics', async ({ page }) => {
    const kpiBar = page.locator('#partner-kpi-bar');
    await expect(kpiBar).toBeVisible({ timeout: 5000 });
    // KPI bar renders 3 grid cells
    const cells = kpiBar.locator('div');
    const count = await cells.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test('Partner card click opens detail overlay', async ({ page }) => {
    await page.locator('.partner-card').first().click();
    await expect(page.locator('#partner-overlay-bg')).toBeVisible({ timeout: 3000 });
  });

  test('FIX 6: Log Outreach opens outreach modal', async ({ page }) => {
    // Log Outreach button is inside the partner detail overlay
    await page.locator('.partner-card').first().click();
    await expect(page.locator('#partner-overlay-bg')).toBeVisible({ timeout: 3000 });
    const outreachBtn = page.locator('#partner-overlay-bg button', { hasText: /Log Outreach/i }).first();
    await expect(outreachBtn).toBeVisible({ timeout: 3000 });
    await outreachBtn.click();
    await expect(page.locator('#po-outreach-modal')).toBeVisible({ timeout: 3000 });
  });

  test('FIX 6: Outreach modal has method, outcome, and notes fields', async ({ page }) => {
    await page.locator('.partner-card').first().click();
    await expect(page.locator('#partner-overlay-bg')).toBeVisible({ timeout: 3000 });
    await page.locator('#partner-overlay-bg button', { hasText: /Log Outreach/i }).first().click();
    await expect(page.locator('#po-outreach-modal')).toBeVisible({ timeout: 3000 });
    const modal = page.locator('#po-outreach-modal');
    await expect(modal.locator('select').first()).toBeVisible();
    await expect(modal.locator('textarea').first()).toBeVisible();
  });

  test('FIX 17: Partner contact fields in detail overlay', async ({ page }) => {
    const pid = await firstPartnerId(page);
    if (!pid) { test.skip(); return; }
    await page.evaluate(id => openPartner(id), pid);
    await expect(page.locator('#partner-overlay-bg')).toBeVisible({ timeout: 3000 });
    for (const field of ['#po-contact-name', '#po-contact-role', '#po-contact-phone', '#po-contact-email', '#po-contact-address']) {
      await expect(page.locator(field)).toBeVisible();
    }
  });

  test('Add Partner button opens add form', async ({ page }) => {
    const addBtn = page.locator('button', { hasText: /Add Partner/i }).first();
    await expect(addBtn).toBeVisible({ timeout: 5000 });
    await addBtn.click();
    await page.waitForTimeout(300);
    // Add partner form has #ap-name input with placeholder "Business name"
    await expect(page.locator('#ap-name')).toBeVisible({ timeout: 3000 });
  });
});
