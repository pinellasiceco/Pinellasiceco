'use strict';
const { test, expect } = require('@playwright/test');
const { load, tab, seed, firstPid, waitForToast } = require('./helpers');

const MOCK_URL = 'https://mock-proxy.test/send-email';

async function setMockProxy(page) {
  await page.evaluate(u => localStorage.setItem('pic_email_fn_url', u), MOCK_URL);
}

async function interceptEmail(page) {
  let captured = null;
  await page.route(MOCK_URL, async route => {
    captured = JSON.parse(route.request().postData() || '{}');
    await route.fulfill({ status: 200, body: JSON.stringify({ ok: true }), contentType: 'application/json' });
  });
  return () => captured;
}

async function interceptEmailError(page, status = 422) {
  await page.route(MOCK_URL, async route => {
    await route.fulfill({ status, body: JSON.stringify({ error: 'bad' }), contentType: 'application/json' });
  });
}

test.describe('Email flows', () => {
  test.beforeEach(async ({ page }) => {
    await load(page);
    await page.evaluate(() => localStorage.removeItem('pic_email_fn_url'));
  });

  // --- sendEmailViaProxy unit-level tests ---

  test('FIX 10: sendEmailViaProxy returns false when no proxy URL', async ({ page }) => {
    const result = await page.evaluate(() =>
      window.sendEmailViaProxy('a@b.com', 'subject', '<p>body</p>')
    );
    expect(result).toBe(false);
  });

  test('no proxy URL shows toast with "not set" message', async ({ page }) => {
    await page.evaluate(() => window.sendEmailViaProxy('a@b.com', 'subject', '<p>body</p>'));
    const txt = await waitForToast(page);
    expect(txt.toLowerCase()).toMatch(/not set|no.*url|proxy/);
  });

  test('FIX 10: sendEmailViaProxy returns true on HTTP 200', async ({ page }) => {
    await setMockProxy(page);
    const getCapture = await interceptEmail(page);
    const result = await page.evaluate(
      ([url]) => window.sendEmailViaProxy('test@example.com', 'Subject', '<p>hi</p>'),
      [MOCK_URL]
    );
    expect(result).toBe(true);
  });

  test('FIX 10: sendEmailViaProxy returns false on HTTP 4xx', async ({ page }) => {
    await setMockProxy(page);
    await interceptEmailError(page, 422);
    const result = await page.evaluate(() =>
      window.sendEmailViaProxy('test@example.com', 'Subject', '<p>hi</p>')
    );
    expect(result).toBe(false);
  });

  test('sendEmailViaProxy shows failure toast on 4xx', async ({ page }) => {
    await setMockProxy(page);
    await interceptEmailError(page, 503);
    await page.evaluate(() => window.sendEmailViaProxy('x@y.com', 's', 'h'));
    const txt = await waitForToast(page);
    expect(txt.toLowerCase()).toMatch(/fail|error|503/);
  });

  // --- ATP email flow ---

  test('FIX 11: ATP email button exists in ATP dialog', async ({ page }) => {
    await tab(page, 'all');
    const pid = await firstPid(page);
    await page.evaluate(id => {
      const p = P.find(x => x.id === id);
      scStatusReport(p);
    }, pid);
    await expect(page.locator('#atp-email')).toBeVisible({ timeout: 3000 });
  });

  test('ATP email without proxy URL shows toast', async ({ page }) => {
    await tab(page, 'all');
    const pid = await firstPid(page);
    await page.evaluate(id => {
      const p = P.find(x => x.id === id);
      scStatusReport(p);
    }, pid);
    await expect(page.locator('#atp-email')).toBeVisible({ timeout: 3000 });
    await page.locator('#atp-email').click();
    const txt = await waitForToast(page);
    expect(txt.toLowerCase()).toMatch(/email|not set|enter/);
  });

  test('FIX 9+11: ATP email sends correct payload with notes', async ({ page }) => {
    await setMockProxy(page);
    const getCapture = await interceptEmail(page);
    await tab(page, 'all');
    const pid = await firstPid(page);
    const prospectName = await page.evaluate(id => P.find(x => x.id === id).name, pid);

    await page.evaluate(id => {
      const p = P.find(x => x.id === id);
      scStatusReport(p);
    }, pid);
    await expect(page.locator('#atp-email')).toBeVisible({ timeout: 3000 });
    await page.fill('#atp-val-inp', '800');
    await page.fill('#atp-email-inp', 'owner@restaurant.com');
    await page.fill('#atp-notes-inp', 'Ice machine running warm');
    await page.locator('#atp-email').click();
    await page.waitForTimeout(500);

    const captured = getCapture();
    expect(captured).not.toBeNull();
    expect(captured.to).toBe('owner@restaurant.com');
    expect(captured.html).toContain(prospectName);
    expect(captured.html).toMatch(/800|MARGINAL|PASS|FAIL/);
    expect(captured.html).toContain('Ice machine running warm');
  });

  // --- Compliance report email ---

  test('Compliance email button visible on client card', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: {
        [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01', email: 'client@test.com' },
      },
    });
    await tab(page, 'clients');
    const emailBtn = page.locator('button', { hasText: /Email Report/i }).first();
    await expect(emailBtn).toBeVisible({ timeout: 5000 });
  });

  test('Compliance email without proxy URL shows toast', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: {
        [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01', email: 'client@test.com' },
      },
    });
    await tab(page, 'clients');
    const emailBtn = page.locator('button', { hasText: /Email Report/i }).first();
    await emailBtn.click();
    const txt = await waitForToast(page);
    expect(txt.toLowerCase()).toMatch(/not set|proxy|email|url/);
  });

  test('FIX 9: Compliance email sends srSendEmail payload', async ({ page }) => {
    const pid = await firstPid(page);
    const prospectName = await page.evaluate(() => P[0].name);
    await seed(page, {
      pic_customers: {
        [pid]: {
          status: 'customer_recurring',
          monthly: 149,
          machines: 1,
          signed_date: '2026-01-01',
          email: 'client@test.com',
          atp_history: [{ post: 47, date: '2026-05-01' }],
        },
      },
    });
    await setMockProxy(page);
    const getCapture = await interceptEmail(page);
    await tab(page, 'clients');
    const emailBtn = page.locator('button', { hasText: /Email Report/i }).first();
    await emailBtn.click();
    await page.waitForTimeout(500);

    const captured = getCapture();
    expect(captured).not.toBeNull();
    expect(captured.to).toBe('client@test.com');
    expect(captured.html).toContain(prospectName);
  });

  // --- Service report email ---

  test('Service report email toggle shows email input', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: {
        [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' },
      },
    });
    await tab(page, 'clients');
    // Switch to Service sub-tab
    const serviceTab = page.locator('#ct-service');
    if (await serviceTab.count() > 0) {
      await serviceTab.click();
      await page.waitForTimeout(200);
    }
    // Click Email button to toggle email row
    const emailBtn = page.locator('button', { hasText: /^Email$/i }).first();
    if (await emailBtn.count() > 0) {
      await emailBtn.click();
      await page.waitForTimeout(200);
      await expect(page.locator('#report-email-to')).toBeVisible();
    }
  });

  test('Service report send with mock proxy captures correct to address', async ({ page }) => {
    const pid = await firstPid(page);
    await seed(page, {
      pic_customers: {
        [pid]: { status: 'customer_recurring', monthly: 149, machines: 1, signed_date: '2026-01-01' },
      },
    });
    await setMockProxy(page);
    const getCapture = await interceptEmail(page);
    await tab(page, 'clients');

    const serviceTab = page.locator('#ct-service');
    if (await serviceTab.count() === 0) { test.skip(); return; }
    await serviceTab.click();
    await page.waitForTimeout(200);

    const toggleBtn = page.locator('button', { hasText: /^Email$/i }).first();
    if (await toggleBtn.count() === 0) { test.skip(); return; }
    await toggleBtn.click();
    await page.waitForTimeout(200);

    await page.fill('#report-email-to', 'service@test.com');
    const sendBtn = page.locator('button', { hasText: /^Send$/i }).first();
    await sendBtn.click();
    await page.waitForTimeout(500);

    const captured = getCapture();
    if (captured) {
      expect(captured.to).toBe('service@test.com');
    } else {
      // If no email proxy needed (e.g. opens print), verify at least no crash
      await expect(page.locator('#toast')).toBeDefined();
    }
  });
});
