/**
 * DBPR Inspector Name Diagnostic — Phase 2
 *
 * Checks multiple DBPR pages to find where (if anywhere) inspector names appear:
 *   1. inspectionDetail.asp         — individual violation detail (confirmed: no name)
 *   2. LicenseDetail.asp            — license profile page with inspection history list
 *   3. wl11.asp (search results)    — license search results page
 *
 * Run: node scripts/inspect_dbpr_page.js
 */

const { chromium } = require('@playwright/test');

const TERMS_URL = 'https://www.myfloridalicense.com/insptermsofuse.asp';

// LA QUINTA INN — License SEA6215501, License ID 6029810, Visit ID 13624053
const PAGES = [
  {
    label: 'License Detail (by numeric ID)',
    url: 'https://www.myfloridalicense.com/LicenseDetail.asp?SID=&id=6029810',
  },
  {
    label: 'License Search Results (by license number)',
    url: 'https://www.myfloridalicense.com/wl11.asp?mode=0&SID=&brd=&typ=&LicNumb=SEA6215501&LicType=&CtyCode=&bus=&add=&cty=&stt=&zip=&con=&app=&dis=&disDate=&expDate=&actCode=&Action=Lic+Search&search=Y',
  },
  {
    label: 'Inspection Search (by license number)',
    url: 'https://www.myfloridalicense.com/inspectionSearch.asp?inspSearchType=LicenseNumber&inspSearchValue=SEA6215501&Action=Search',
  },
  {
    label: 'Inspection Detail (known Visit ID — baseline)',
    url: 'https://www.myfloridalicense.com/inspectionDetail.asp?InspVisitID=13624053',
  },
];

async function checkPage(page, label, url, allRequests) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`PAGE: ${label}`);
  console.log(`URL:  ${url}`);
  console.log('='.repeat(60));

  const pageRequests = [];
  const handler = req => {
    const type = req.resourceType();
    if (['xhr', 'fetch', 'document'].includes(type)) {
      pageRequests.push({ type, url: req.url(), method: req.method() });
      allRequests.push({ label, type, url: req.url(), method: req.method() });
    }
  };
  page.on('request', handler);

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log(`  ERROR loading page: ${e.message}`);
    page.off('request', handler);
    return;
  }
  page.off('request', handler);

  const bodyText = await page.evaluate(() => document.body.innerText);

  // Print full text
  console.log('\n--- RENDERED TEXT ---');
  console.log(bodyText.substring(0, 4000));
  if (bodyText.length > 4000) console.log(`  ... (${bodyText.length} chars total, truncated)`);

  // Network requests beyond the initial document load
  const extra = pageRequests.filter(r => r.type !== 'document');
  if (extra.length) {
    console.log('\n--- AJAX/FETCH REQUESTS ---');
    extra.forEach(r => console.log(`  [${r.type}] ${r.method} ${r.url}`));
  }

  // Inspector name scan — exclude common observation text phrases
  const NOISE = /inspector (discussed|advised|noted|observed|verified|reviewed|corrected|instructed|educated|checked|was|will|has|had|found|determined|conducted|performed|identified)/i;
  const lines = bodyText.split('\n').filter(l => l.trim());
  const hits = lines.filter(l => /inspector/i.test(l) && !NOISE.test(l));
  console.log('\n--- INSPECTOR MENTIONS (filtered) ---');
  hits.forEach(l => console.log(' ', l.trim()));
  if (!hits.length) console.log('  (none)');
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();
  const allRequests = [];

  console.log('Initialising session (terms page)...');
  await page.goto(TERMS_URL, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Session ready.\n');

  for (const { label, url } of PAGES) {
    await checkPage(page, label, url, allRequests);
  }

  console.log('\n\n=== SUMMARY: ALL NETWORK REQUESTS ACROSS ALL PAGES ===');
  allRequests.forEach(r => console.log(`  [${r.label}] [${r.type}] ${r.method} ${r.url}`));

  await browser.close();
})();
