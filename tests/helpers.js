'use strict';

async function load(page) {
  await page.goto('/');
  // P is a const in the page script scope — NOT on window; use bare P in evaluate
  await page.waitForFunction(() => typeof P !== 'undefined' && P.length > 0, { timeout: 60000 });
}

async function tab(page, name) {
  await page.evaluate(n => sw(n), name);
  await page.waitForTimeout(200);
}

async function clearStorage(page) {
  await page.evaluate(() => localStorage.clear());
}

// Seed localStorage keys then reload so the app picks them up
async function seed(page, data) {
  for (const [k, v] of Object.entries(data)) {
    await page.evaluate(([key, val]) => localStorage.setItem(key, JSON.stringify(val)), [k, v]);
  }
  await page.reload();
  await page.waitForFunction(() => typeof P !== 'undefined' && P.length > 0, { timeout: 60000 });
}

// Get the first prospect id from the baked-in P[] array
async function firstPid(page) {
  return page.evaluate(() => P[0].id);
}

// Get first N prospect ids
async function pids(page, n) {
  return page.evaluate(n => P.slice(0, n).map(p => p.id), n);
}

// Get first partner id
async function firstPartnerId(page) {
  return page.evaluate(() => typeof PARTNERS !== 'undefined' && PARTNERS[0] ? PARTNERS[0].id : null);
}

// Wait for #toast.on then return its text
async function waitForToast(page, timeout = 3000) {
  await page.waitForSelector('#toast.on', { timeout });
  return page.textContent('#toast');
}

module.exports = { load, tab, clearStorage, seed, firstPid, pids, firstPartnerId, waitForToast };
