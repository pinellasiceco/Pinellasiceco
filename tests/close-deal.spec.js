'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab } = require('./helpers');

// Open the Close Deal overlay for the first prospect in the Prospects grid
async function openCloseDeal(page) {
  await tab(page, 'all');
  const detailsBtn = page.locator('#agrid [data-action="showCard"]').first();
  await detailsBtn.click();
  await expect(page.locator('#sc-bg')).toBeVisible({ timeout: 5000 });
  await page.locator('#sc-close-deal').click();
  await expect(page.locator('#close-overlay')).toBeVisible({ timeout: 5000 });
}

test.describe('Close Deal overlay', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
  });

  test('overlay opens and shows key elements', async ({ page }) => {
    await openCloseDeal(page);
    await expect(page.locator('#co-mach-count')).toBeVisible();
    await expect(page.locator('#co-monthly')).toBeVisible();
    await expect(page.locator('#co-quarterly')).toBeVisible();
    await expect(page.locator('#co-year1-val')).toBeVisible();
    await expect(page.locator('#co-entry-disc')).toBeVisible();
    await expect(page.locator('#co-plan-disc')).toBeVisible();
    await expect(page.locator('#co-send-btn')).toBeVisible();
    await expect(page.locator('#co-charge-btn')).toBeVisible();
    await expect(page.locator('#co-confirm')).toBeVisible();
  });

  test('Cancel button closes the overlay', async ({ page }) => {
    await openCloseDeal(page);
    await page.locator('#co-cancel').click();
    await expect(page.locator('#close-overlay')).not.toBeVisible({ timeout: 3000 });
  });

  test('machine +/- adjusts count and Year 1 total', async ({ page }) => {
    await openCloseDeal(page);
    const y1Before = await page.locator('#co-year1-val').textContent();
    await page.locator('#co-mach-plus').click();
    await expect(page.locator('#co-mach-count')).toHaveText('2');
    const y1After = await page.locator('#co-year1-val').textContent();
    // Year 1 should be higher with 2 machines
    const toNum = s => parseInt(s.replace(/[^0-9]/g, ''));
    expect(toNum(y1After)).toBeGreaterThan(toNum(y1Before));
    // Back to 1
    await page.locator('#co-mach-minus').click();
    await expect(page.locator('#co-mach-count')).toHaveText('1');
  });

  test('Monthly/Quarterly toggle updates Year 1 total', async ({ page }) => {
    await openCloseDeal(page);
    const y1Monthly = await page.locator('#co-year1-val').textContent();
    await page.locator('#co-quarterly').click();
    await page.waitForTimeout(100);
    const y1Quarterly = await page.locator('#co-year1-val').textContent();
    const toNum = s => parseInt(s.replace(/[^0-9]/g, ''));
    // Quarterly is cheaper so Year 1 should be lower
    expect(toNum(y1Quarterly)).toBeLessThan(toNum(y1Monthly));
    // Switch back
    await page.locator('#co-monthly').click();
    await page.waitForTimeout(100);
    const y1Back = await page.locator('#co-year1-val').textContent();
    expect(toNum(y1Back)).toEqual(toNum(y1Monthly));
  });

  test('entry fee discount reduces Year 1 total', async ({ page }) => {
    await openCloseDeal(page);
    const y1Before = await page.locator('#co-year1-val').textContent();
    await page.fill('#co-entry-disc', '50');
    await page.dispatchEvent('#co-entry-disc', 'input');
    const y1After = await page.locator('#co-year1-val').textContent();
    const toNum = s => parseInt(s.replace(/[^0-9]/g, ''));
    expect(toNum(y1After)).toBe(toNum(y1Before) - 50);
  });

  test('plan discount reduces Year 1 total', async ({ page }) => {
    await openCloseDeal(page);
    const y1Before = await page.locator('#co-year1-val').textContent();
    await page.fill('#co-plan-disc', '20');
    await page.dispatchEvent('#co-plan-disc', 'input');
    const y1After = await page.locator('#co-year1-val').textContent();
    const toNum = s => parseInt(s.replace(/[^0-9]/g, ''));
    // $20/mo discount × 12 months = $240 off Year 1
    expect(toNum(y1After)).toBe(toNum(y1Before) - 240);
  });

  test('Mark Won closes overlay and toasts', async ({ page }) => {
    await openCloseDeal(page);
    await page.locator('#co-confirm').click();
    await expect(page.locator('#close-overlay')).not.toBeVisible({ timeout: 3000 });
  });

  test('one-time toggle switches plan and updates display', async ({ page }) => {
    await openCloseDeal(page);
    const link = page.locator('#co-onetime-link');
    await expect(link).toContainText('one-time');
    // Toggle to one-time
    await link.click();
    await expect(link).toContainText('Switch to monthly');
    // Year 1 detail should say "one-time" not "/mo × 12"
    await expect(page.locator('#co-year1-detail')).toContainText('one-time');
    // Discount label should say "Price discount"
    await expect(page.locator('#co-disc-label')).toHaveText('Price discount');
    // Toggle back to monthly
    await link.click();
    await expect(link).toContainText('one-time');
    await expect(page.locator('#co-year1-detail')).toContainText('/mo');
    await expect(page.locator('#co-disc-label')).toHaveText('Monthly discount');
  });
});
