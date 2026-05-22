/**
 * DBPR Inspector Name Diagnostic
 *
 * Fetches one DBPR inspection detail page with a real Chromium browser,
 * intercepts all network requests, and dumps the rendered DOM text.
 *
 * Run from repo root:
 *   PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node scripts/inspect_dbpr_page.js
 *
 * Or if browsers are in the default location:
 *   node scripts/inspect_dbpr_page.js
 *
 * Output tells us:
 *   1. Whether inspector name appears anywhere in the rendered page text
 *   2. Whether any AJAX/fetch calls fire after initial load (and to what URLs)
 */

const { chromium } = require('@playwright/test');

const TERMS_URL  = 'https://www.myfloridalicense.com/insptermsofuse.asp';
const DETAIL_URL = 'https://www.myfloridalicense.com/inspectionDetail.asp?InspVisitID=13624053';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  // Collect every network request the page fires
  const requests = [];
  page.on('request', req => {
    const type = req.resourceType();
    if (['xhr', 'fetch', 'document'].includes(type)) {
      requests.push({ type, url: req.url(), method: req.method() });
    }
  });

  console.log('Step 1: Loading terms page (session init)...');
  await page.goto(TERMS_URL, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('  Terms page loaded.\n');

  console.log('Step 2: Loading inspection detail page...');
  await page.goto(DETAIL_URL, { waitUntil: 'networkidle', timeout: 30000 });
  // Extra wait for any deferred JS
  await page.waitForTimeout(3000);
  console.log('  Detail page loaded.\n');

  // Dump full rendered text
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('=== FULL RENDERED PAGE TEXT ===');
  console.log(bodyText);
  console.log('=== END PAGE TEXT ===\n');

  // Report all network requests
  console.log('=== NETWORK REQUESTS FIRED ===');
  requests.forEach(r => console.log(`  [${r.type}] ${r.method} ${r.url}`));
  if (requests.length === 0) console.log('  (none beyond initial document load)');
  console.log('=== END NETWORK REQUESTS ===\n');

  // Quick scan for inspector-looking content
  const lines = bodyText.split('\n').filter(l => l.trim());
  const inspectorLines = lines.filter(l =>
    /inspector/i.test(l) && !/inspector (discussed|advised|noted|observed|verified|reviewed|corrected|instructed|educated|checked)/i.test(l)
  );
  console.log('=== LINES MENTIONING INSPECTOR (filtered) ===');
  inspectorLines.forEach(l => console.log(' ', l.trim()));
  if (inspectorLines.length === 0) console.log('  (none found outside violation text)');
  console.log('=== END ===');

  await browser.close();
})();
