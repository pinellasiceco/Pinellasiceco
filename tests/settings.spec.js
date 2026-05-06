'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab } = require('./helpers');

test.describe('Settings overlay', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    // Clear any saved Supabase keys
    await page.evaluate(() => {
      localStorage.removeItem('pic_supabase_url');
      localStorage.removeItem('pic_supabase_key');
    });
  });

  test('Gear button opens settings overlay', async ({ page }) => {
    await page.locator('#gear-btn').click();
    await page.waitForTimeout(200);
    // Gear navigates to the data/settings panel (#p-data)
    await expect(page.locator('#p-data')).toBeVisible({ timeout: 3000 });
  });

  test('FIX 13: sync-dot element exists in DOM', async ({ page }) => {
    await expect(page.locator('#sync-dot')).toHaveCount(1);
  });

  test('FIX 13: sync-dot is grey before Supabase keys are set', async ({ page }) => {
    const dot = page.locator('#sync-dot');
    const style = await dot.getAttribute('style');
    // Grey = no keys configured. Background should be grey/neutral (not green/amber)
    expect(style).toMatch(/#e2e8f0|grey|gray|#6b7280|#9ca3af/i);
  });

  test('FIX 13: sync-dot turns non-grey after Supabase URL and key filled', async ({ page }) => {
    // Open settings
    await page.locator('#gear-btn').click();
    await page.waitForTimeout(200);
    await page.fill('#sb-supabase-url', 'https://test.supabase.co');
    await page.fill('#sb-supabase-key', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test');
    // Trigger blur/onchange to save
    await page.locator('#sb-supabase-key').blur();
    await page.waitForTimeout(300);
    const dot = page.locator('#sync-dot');
    const style = await dot.getAttribute('style');
    // Should now be green or amber — not the default grey
    expect(style).not.toMatch(/#e2e8f0/);
  });

  test('Email function URL input is present', async ({ page }) => {
    await page.locator('#gear-btn').click();
    await page.waitForTimeout(200);
    await expect(page.locator('#sb-email-fn')).toBeVisible();
  });

  test('FIX 14: filter bar has overflow-x auto', async ({ page }) => {
    await tab(page, 'all');
    const overflowX = await page.evaluate(() => {
      const flt = document.querySelector('.flt-sel');
      if (!flt) return null;
      return getComputedStyle(flt.parentElement).overflowX;
    });
    expect(overflowX).toBe('auto');
  });
});
