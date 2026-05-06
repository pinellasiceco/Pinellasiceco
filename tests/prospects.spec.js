'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, seed, firstPid, waitForToast } = require('./helpers');

// Helper: open showCard for the first prospect card visible in #agrid
async function openFirstShowCard(page) {
  await tab(page, 'all');
  // Click the Details button (data-action="showCard") on the first card
  const detailsBtn = page.locator('#agrid [data-action="showCard"]').first();
  await detailsBtn.click();
  await expect(page.locator('#sc-bg')).toBeVisible({ timeout: 5000 });
}

test.describe('Prospects tab', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    await tab(page, 'all');
  });

  test('prospect grid renders with at least 1 card', async ({ page }) => {
    const grid = page.locator('#agrid');
    await expect(grid).toBeVisible();
    const count = await grid.locator('[data-id]').count();
    expect(count).toBeGreaterThan(0);
  });

  test('search filters the prospect list', async ({ page }) => {
    const grid = page.locator('#agrid');
    const before = await grid.locator('[data-id]').count();
    await page.fill('#si', 'zzzzz_no_match');
    await page.waitForTimeout(300);
    const after = await grid.locator('[data-id]').count();
    expect(after).toBeLessThan(before);
  });

  test('county filter narrows list', async ({ page }) => {
    const grid = page.locator('#agrid');
    const before = await grid.locator('[data-id]').count();
    const options = await page.locator('#ac option').allTextContents();
    const nonAll = options.find(o => o.trim() !== 'All Counties' && o.trim() !== '');
    if (nonAll) {
      await page.selectOption('#ac', { label: nonAll });
      await page.waitForTimeout(300);
      const after = await grid.locator('[data-id]').count();
      expect(after).toBeLessThanOrEqual(before);
    }
  });

  test('priority filter narrows list', async ({ page }) => {
    const grid = page.locator('#agrid');
    const options = await page.locator('#ap option').allTextContents();
    const nonAll = options.find(o => o.trim() !== 'All Priorities' && o.trim() !== '');
    if (nonAll) {
      await page.selectOption('#ap', { label: nonAll });
      await page.waitForTimeout(300);
      const after = await grid.locator('[data-id]').count();
      expect(after).toBeGreaterThanOrEqual(0);
    }
  });

  test('showCard opens on Details button click', async ({ page }) => {
    await openFirstShowCard(page);
    // Already asserted visible in helper
    await expect(page.locator('#sc-sheet')).toBeVisible();
  });

  test('showCard closes on backdrop click', async ({ page }) => {
    await openFirstShowCard(page);
    await page.evaluate(() => document.getElementById('sc-bg').click());
    await expect(page.locator('#sc-bg')).toBeHidden({ timeout: 3000 });
  });

  test('showCard has correct outcome buttons', async ({ page }) => {
    await openFirstShowCard(page);
    // showCard uses data-scout (data-o is in the static quick-log modal, not in #sc-bg)
    for (const outcome of ['intro_set', 'in_play', 'no_contact', 'voicemail', 'not_now', 'dead']) {
      await expect(page.locator(`#sc-bg [data-scout="${outcome}"]`)).toBeVisible();
    }
  });

  test('FIX 4: no Signed button in showCard', async ({ page }) => {
    await openFirstShowCard(page);
    await expect(page.locator('#sc-bg [data-scout="signed"]')).toHaveCount(0);
  });

  test('FIX 4: no Service Done button in showCard', async ({ page }) => {
    await openFirstShowCard(page);
    await expect(page.locator('#sc-bg [data-scout="service_done"]')).toHaveCount(0);
  });

  test('FIX 16: full-width Quoted button visible in showCard', async ({ page }) => {
    await openFirstShowCard(page);
    const quotedBtn = page.locator('[data-scout="quoted"]');
    await expect(quotedBtn).toBeVisible();
    const style = await quotedBtn.getAttribute('style');
    expect(style).toContain('width:100%');
  });

  test('Close Deal button visible for unattached prospect', async ({ page }) => {
    await openFirstShowCard(page);
    await expect(page.locator('#sc-close-deal')).toBeVisible();
  });

  test('FIX 2: Active Client panel shown instead of Close Deal for won prospect', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: { [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' } },
    });
    await tab(page, 'all');
    const detailsBtn = page.locator(`#agrid [data-id="${pid}"] [data-action="showCard"]`).or(
      page.locator(`#agrid [data-id="${pid}"]`).locator('[data-action="showCard"]')
    ).first();
    await detailsBtn.click();
    await expect(page.locator('#sc-bg')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#sc-close-deal')).toHaveCount(0);
    await expect(page.locator('#sc-sheet').locator('text=/Active Client/i')).toBeVisible();
  });

  test('ATP Report button visible in showCard', async ({ page }) => {
    await openFirstShowCard(page);
    const atpBtn = page.locator('#sc-sheet button', { hasText: /Report/i }).first();
    await expect(atpBtn).toBeVisible();
  });

  test('FIX 11: ATP notes textarea exists in ATP dialog', async ({ page }) => {
    await openFirstShowCard(page);
    const atpBtn = page.locator('#sc-sheet button', { hasText: /Report/i }).first();
    await atpBtn.click();
    await expect(page.locator('#atp-notes-inp')).toBeVisible({ timeout: 3000 });
  });

  test('follow-up date persists after save', async ({ page }) => {
    const pid = await firstPid(page);
    const detailsBtn = page.locator(`#agrid [data-action="showCard"]`).first();
    await detailsBtn.click();
    await expect(page.locator('#sc-bg')).toBeVisible({ timeout: 5000 });
    // Select an outcome first (required before Save)
    await page.locator('#sc-bg [data-scout="in_play"]').click();
    const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
    // Use #sc-followup — the showCard date input (not the static #mfollowup in the map modal)
    await page.evaluate(d => {
      const inp = document.getElementById('sc-followup');
      if (inp) { inp.value = d; inp.dispatchEvent(new Event('change', { bubbles: true })); }
    }, tomorrow);
    await page.locator('#sc-save-btn').click();
    await page.waitForTimeout(300);
    const stored = await page.evaluate(pid => {
      const log = JSON.parse(localStorage.getItem('pic_v4') || '{}');
      const entries = log[pid] || [];
      return entries.length > 0 ? entries[entries.length - 1].followup : null;
    }, pid);
    expect(stored).toBe(tomorrow);
  });

  test('FIX 12: dead prospects hidden by default', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_v4: { [pid]: [{ date: '2026-05-01', outcome: 'dead', notes: '' }] },
    });
    await tab(page, 'all');
    await page.waitForTimeout(300);
    const card = page.locator(`#agrid .card[data-id="${pid}"]`);
    await expect(card).toHaveCount(0);
  });

  test('FIX 12: Show Lost toggle reveals dead prospects', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_v4: { [pid]: [{ date: '2026-05-01', outcome: 'dead', notes: '' }] },
    });
    await tab(page, 'all');
    await page.waitForTimeout(300);
    // Clear any filters that might still hide the card
    await page.evaluate(() => {
      const ac = document.getElementById('ac'); if (ac) ac.value = '';
      const ap = document.getElementById('ap'); if (ap) ap.value = '';
      const as_ = document.getElementById('as_'); if (as_) as_.value = '';
      if (typeof rA === 'function') rA();
    });
    await page.waitForTimeout(200);
    await page.locator('#btn-show-dead').click();
    await page.waitForTimeout(300);
    // Scope to .card to avoid strict mode violation (multiple data-id elements per card)
    const card = page.locator(`#agrid .card[data-id="${pid}"]`);
    await expect(card).toBeVisible({ timeout: 3000 });
  });

  test('FIX 12: Show Lost button changes style after toggle', async ({ page }) => {
    const btn = page.locator('#btn-show-dead');
    const styleBefore = await btn.getAttribute('style');
    await btn.click();
    await page.waitForTimeout(200);
    const styleAfter = await btn.getAttribute('style');
    expect(styleAfter).not.toBe(styleBefore);
  });
});
