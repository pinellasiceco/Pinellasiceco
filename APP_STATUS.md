# Pinellas Ice Co — App Status
*Last updated: 2026-05-06 (session 13) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-05-06 (session 13 — compliance PDF notes & ATP status change detection)
- Build script: `build.py` (repo root) → outputs `index.html` directly
- `index.html` regenerated from `build.py` using existing P[] data — fully in sync

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` runs as **final step in rebuild.yml** — always sends after fresh data is built
- Daily briefing fallback: `send_briefing.yml` cron at 13:00 UTC (9am ET) if rebuild fails
- sw.js cache bumped manually when patching index.html; `build.py` auto-stamps on CI rebuild

### Navigation
- 6-tab layout: Home / Prospects / Pipeline / Route / Clients / Partners
- Gear ⚙️ button opens Settings overlay
- `sw('customers')` and `sw('service')` alias to Clients tab (backward compatible)
- Clients tab has inner sub-tabs: Clients / Service (via `setClientTab()`)

### Home Tab
- **TODAY'S PLAN** section at top: ranked action list (action score = urgency × revenue × recency × ice risk boost), max 8 stops
- **Add All to Route** button in TODAY'S PLAN adds all stops and switches to Route tab
- Strike Zone section shows top-scored prospects by city cluster
- In Play follow-ups grouped by urgency: Overdue / Today / This Week / This Month
- Cold targets grid loads on first open

### Prospects Tab
- Full prospect list with search/filter
- showCard detail overlay:
  - All buttons use `data-action` / `data-id` + event delegation on modal backdrop (iOS-safe)
  - Pitch/walkin/objection scripts removed
  - ATP Status Report button (📋 Report) opens print-ready leave-behind
  - Follow-up: standard `input[type=date]` pre-filled with existing date if set
  - Save button: large "Save & Disposition Lead" button, always saves (no blocking)
  - Missing follow-up on in_play/not_now shows soft toast tip, does not block

### Route Tab
- ZIP always syncs from Settings on load (no stale value)
- **City cluster chips**: Tarpon / Palm Harbor / Dunedin / Clearwater / Largo / Safety Harbor / St. Pete / All — sets ZIP + triggers rRoute()
- Manual mode: explicit green **➕ Add** / orange **✓ Added** toggle buttons per card with inline `ontouchend` — fires reliably on iOS PWA
- Manual mode displays hint text explaining how to build route
- Card body tap opens Details; only the Add button adds to route (no accidental adds)
- Optimized build available (hours input triggers TSP routing)
- Anchor stop supported (`routeAnchor` / `clearAnchor()`)
- Start 📍 button also uses inline `ontouchend` for iOS reliability

### Pipeline Tab
- 4-stage tab UI: **In Play / Quoted / Won / Lost** (via `setPipeStage()` / `pipeStage` state)
- KPI bar: In Play count, Quoted count, Close Rate %
- `getProspectStage(p)` classifies each prospect by stage (checks p.status + last log outcome)
- In Play / Quoted: grouped by follow-up urgency (Overdue / Today / Week / Month / Later)
- Won / Lost: chronological list with outcome badge
- Ice risk badges (High/Med) shown on In Play / Quoted cards
- Lost `not_now` (Timing) auto-resurfaces after 90 days (not shown in Lost)
- Quoted outcome button in showCard (purple style, logs `quoted` outcome)

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Client card service row: **Email Report only** (Log Visit + Set Next Due removed — use Service sub-tab)
- `churnClient(id)` marks prospect churned with confirm dialog; red Churn button on non-churned cards
- Service sub-tab: log service visits, track next service date, machine info
- Save Service Visit button: iOS-safe (`onclick` + `ontouchend`)

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard; persists entered ATP value + notes to `atp_history` before generating PDF/email
- `srGenerate(p, atpVal, notes)` generates print-ready letter-size HTML report; shows amber STATUS CHANGE banner if ATP label (PASS/MARGINAL/FAIL) differs from previous visit
- `srSendEmail(p, atpVal, emailTo, notes)` emails same report via proxy; same status change banner logic
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL
- `atp_history` entries: `{date, pre, post, notes}` — notes field populated by both `submitServiceLog` and `scStatusReport`
- Pop-up blocker fallback toast if `window.open` is blocked
- 3-button layout: Cancel / 📧 Email / Print
- Print CSS: `@page { margin: 0.3in }`, `zoom: 0.92`, padding reduced — guaranteed 1-page output on iOS and desktop

### showCard Detail Overlay
- **WHY THIS PROSPECT MATTERS** navy intel panel (`buildIntelSummary(p)`) — shows ice violations, callback count, inspection timeline, machine count, risk level
- **Ice risk badges** (🧊 High Risk / 🧊 Med Risk) in chips row
- **Quoted** outcome button (purple) added alongside In Play / Intro Set
- All buttons: iOS-safe inline `ontouchend` + `onclick`

### Ice Compliance Risk Score
- `calc_ice_risk(record)` Python function bakes `ice_risk_prob` (0–100), `ice_risk_level` (Low/Med/High), `ice_risk_reason` into every P[] record
- Factors: ice violations <6mo (+25), total ice violations (×8), callbacks (×15), chronic flag (+15), days since inspection (+5/10), machine count (+4/8), business type keywords (+6)
- High ≥65, Medium ≥35, Low <35
- Ice risk boosts action score in TODAY'S PLAN: High=1.4×, Medium=1.2×

### Email System
- **Proxy required**: Resend blocks browser-direct calls (CORS 403) — all email goes through Supabase Edge Function
- Edge Function: `supabase/functions/send-email/index.ts` — deployed via GitHub Actions (`deploy_edge_functions.yml`)
- App setting: `pic_email_fn_url` (localStorage) = Edge Function URL; set in Settings → Cloud Sync
- App setting: `pic_supabase_key` (localStorage) = Supabase anon key (used as Bearer token)
- `sendEmailViaProxy(to, subject, html)` — central send function used by all email buttons
- Email buttons on: ATP report overlay, service report preview, customer card (compliance summary), service log row
- Customer email address stored in `customers[id].email` via `saveCustomerEmail()`
- `emailServiceReport(id)` — emails rendered report HTML from `#report-content`
- `emailComplianceReport(id)` — emails compliance summary (last service, ATP, machine, next due) + technician notes from most recent `atp_history` entry
- **Deploy**: any change to `supabase/functions/**` on main auto-triggers `deploy_edge_functions.yml`

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All 23 date storage sites use `localISO()` — no UTC off-by-one after 8pm ET
- Prospect follow-up dates: stored as local ISO string, compared correctly

## What's Broken / Watch List ⚠️

- **iPad copy-paste**: copying code blocks from chat on iPad adds angle brackets around URLs. Never paste code directly into Supabase editor — use the GitHub Actions deploy workflow instead.

If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

### Channel Partners Tab (session 11)
- 6th tab: &#x1F91D; Partners — channel partner prospect management
- **Python pipeline** (`build.py`): `classify_partner()`, `build_partner_records()` — keyword detection on FL DBPR contractor license CSV (if downloaded) + fallback seed list; bakes `PARTNERS[]` into HTML at CI rebuild time
- **Data**: `PARTNERS[]` static array in HTML, merged at runtime with `localStorage` overrides (`pic_partners_v1`)
- **Filter chips**: by partner type (Hood / Pest / Refrig / HVAC / Beverage) and status (Not Contacted / Active / In Conversation)
- **KPI bar**: Total Prospects · Active Partners · Fees Owed (3 columns)
- **Partner card** → detail overlay: status dropdown, notes textarea, phone/email links, referral list, "Copy Email" / "Log Outreach" buttons
- **Close Deal integration**: active partner dropdown in Close Deal overlay; `logPartnerReferral()` records referral + calculates tier (Bronze/Silver/Gold)
- **Payout report**: downloads `.txt` file listing all fees owed by partner
- **Add Partner** button: manually add any business not in seed list
- **Daily briefing**: `send_briefing.py` includes top 5 not-contacted partners in email
- **CI**: `download_data.py` tries 3 DBPR contractor CSV URLs to populate `data/partner_licenses.csv`
- **sw.js**: bumped to `pic-20260430a`

## What's Missing 🔲
- Nothing from the current feature roadmap is missing

## Recent Changes
- **2026-05-06 (s13):** Compliance PDF notes & ATP status change detection — `atp_history.push` now includes `notes` field so repeat inspections of existing locations persist technician notes; `emailComplianceReport` reads notes from most recent `atp_history` entry and appends to email body; `srGenerate`/`srSendEmail` detect PASS/MARGINAL/FAIL status changes between consecutive visits and show amber ⚠ STATUS CHANGE banner; `scStatusReport` persists entered ATP value and notes back to `atp_history` before dispatching PDF/email so subsequent compliance emails can retrieve them; UA test suite remains 75 passed, 0 failed
- **2026-05-05 (s12):** 18 bug fixes — quarterly plan schedule, prevent re-close on won deals, churn button gating, remove Signed/Service Done buttons, partner Log Outreach modal wiring, Add All to Route 8-stop limit with skipMax param, one-time clean sets `customer_once`, emailComplianceReport reuses srSendEmail HTML output, sendEmailViaProxy returns true/false, ATP notes field in report, hide dead prospects toggle (`_showDead`/`toggleShowDead()`), Supabase input onblur/onchange + Save Credentials button + sync dot indicator, filter bar overflow-x scroll, full-width purple Quoted button in showCard, partner contact fields (name/role/phone/email/address), generateICS() calendar export for quarterly clients
- **2026-04-30 (s11c):** Bug fixes — (1) Supabase URL + key inputs added to Settings panel so `sendEmailViaProxy()` and `exportToBriefing()` can be configured from UI; (2) ATP PDF guaranteed 1-page via `@page{margin:0.3in}` + `zoom:0.92` + tighter element spacing; (3) Close deal MRR fix: `rCust()` now reads `customers[p.id].monthly` (actual closed price) instead of `p.monthly` (DBPR estimate), and `scMarkWon()` syncs `p.monthly`/`p.machines` back to P[] for consistency; (4) Daily briefing JSON parse fix: `load_current()` delimiter changed to `';\nconst PARTNERS='` so trailing semicolon is excluded from the `json.loads()` slice; duplicate `main()` in build.py removed
- **2026-04-30 (s11b):** Partner Fit Score — `calc_partner_fit_score()` auto-scores 0-100 from type, years in business, review count, rating, food service focus, geography, website; `scrape_website_keywords()` caches to `data/partner_web_cache.json`; fit score badge on partner cards; fit score breakdown in detail overlay; "Best to Contact First" top-5 section; sort by fit score; daily briefing shows top 3 by score; sw.js bumped to `pic-20260430b`
- **2026-04-30 (s11):** Channel Partner Program — Partners tab, partner detection pipeline, referral attribution, payout report, daily briefing integration
- **2026-04-29 (s10):** Email/Supabase restored — `srSendEmail()`, `emailServiceReport()`, `emailComplianceReport()`, `sendEmailViaProxy()`, `exportToBriefing()`, `saveEmailFnUrl()`, `sb-email-fn` input, Daily Briefing section with export button — were missing from manually-patched s9 index.html; fixed by regenerating index.html directly from build.py
- **2026-04-29 (s10):** Pricing v2 — `est_deep_clean` now per-machine ($395 + $149 each additional, standalone no-plan); `calc_year1(plan, machines)` Python function; `year1_monthly` + `year1_quarterly` baked into P[]; `calcOnetime()` + `calcYear1()` JS functions; factRows updated with "Filters NOT included"; ATP CTA "$99 to start · Annual plans from $129/mo"
- **2026-04-29 (s10):** Close Deal overlay v2 — machine +/− spinner, editable entry price field ($99 default), live Year 1 Total Value display ($entry + $monthly × 12), "Use $X one-time instead" link at bottom; `coAdjMachines()`, `coUpdateEntry()`, `coUseOnetime()` functions added; `scMarkWon(onetime)` stores `entry_price`, `entry_discount`, `filters_included:false` to customer record
- **2026-04-29 (s10):** Service schedule intervals fixed — monthly plan: 60-day intervals (was 61); quarterly plan: 90-day intervals (was 91); maintenance type `maintenance_61`→`maintenance_60`, label `61-Day`→`60-Day`
- **2026-04-29 (s10):** sw.js bumped to `pic-20260429b`
- **2026-04-29 (s9):** Pricing overhaul — `est_monthly_plan(machines, plan)`, `est_deep_clean()`, `est_intro()` Python functions; `quarterly` field baked into P[]; monthly $149/mo, quarterly $129/mo, intro $99+$49/extra
- **2026-04-29 (s9):** Close Deal overlay — single 🤝 Close Deal button → modal with Monthly/Quarterly toggle + $99 intro checkbox; `scOpenClose()`, `updateCloseDisplay()`, `scMarkWon()`; Lost moved to confirm() dialog
- **2026-04-29 (s9):** buildAnnualSchedule quarterly — monthly=6 visits/61-day, quarterly=4 visits/91-day; deep cleans at visits 1+4 (monthly) or 1+3 (quarterly); all contracts renew at 1 year
- **2026-04-29 (s9):** Golf course detection — `GOLF_KEYWORDS`, `is_golf_venue()`, `venue_type` field baked into P[]; golf floors machines at 2, +10 score bonus; ⛳ Golf filter chip in Prospects; ⛳ Golf cluster chip in Route tab; golf badge in cards + showCard; F&B Director default in contact role dropdown
- **2026-04-29 (s9):** WHY THIS PROSPECT MATTERS — added to index.html (was missing from s8 patch); includes golf intel line; ice risk chips added to showCard chips row
- **2026-04-29 (s9):** Pricing displays — showCard factRows updated (quarterly, annual commitment language); ATP CTA "Annual plans from $129/mo · Annual commitment · Cancel anytime after year 1"; removed all "no commitment" language
- **2026-04-29 (s9):** Daily email fix — `send_briefing.py` embedded as final step in `rebuild.yml` (GitHub bot pushes never trigger other workflows, so the push trigger was never firing); `send_briefing.yml` cron moved to 13:00 UTC as true fallback
- **2026-04-29 (s9):** sw.js bumped to `pic-20260429`, asset path fixed (removed stray space)
- **2026-04-28 (s8):** Pipeline overhaul — 4-stage tabs (In Play/Quoted/Won/Lost), KPI bar, getProspectStage(), setPipeStage(), ice risk badges on cards, Quoted outcome button in showCard
- **2026-04-28 (s8):** TODAY'S PLAN — ranked action list on Home tab (action score formula), Add All to Route button
- **2026-04-28 (s8):** WHY THIS PROSPECT MATTERS — navy intel panel in showCard with ice violation + callback intel
- **2026-04-28 (s8):** Ice Compliance Risk Score — calc_ice_risk() Python bakes risk level/score/reason into every prospect record
- **2026-04-28 (s8):** City cluster chips in Route tab — 7 Pinellas area presets + All, sets ZIP and triggers rRoute()
- **2026-04-28 (s8):** Clients tab cleanup — removed Log Visit + Set Next Due buttons (kept Email Report only); service actions remain in Service sub-tab
- **2026-04-28 (s8):** churnClient() + Churn button on client cards — red, confirm dialog, only for non-churned
- **2026-04-28 (s8):** Print CSS — @page 0.45in margin, reduced padding, buttons hidden — all 3 reports fit letter-size
- **2026-04-28 (s8):** Deep clean pricing fixed to $349 everywhere (est_onetime Python fn + all JS fallbacks + UI labels)
- **2026-04-28 (s8):** alert() → toast() — all email error alerts converted (no more blocking alerts)
- **2026-04-25:** Architecture rewrite — 5-tab nav, Pipeline tab, Clients/Service sub-tabs, Settings gear button
- **2026-04-25:** ATP Status Report — 📋 Report button in showCard, print-ready HTML
- **2026-04-25:** Bug fixes — Route ZIP, manual +Add buttons, remove call scripts, daily cron, soft followup warning
- **2026-04-25 (s2):** `localISO()` — all date storage uses local timezone (no UTC off-by-one)
- **2026-04-25 (s2):** sw.js daily date-stamp — eliminates stale PWA installs
- **2026-04-25 (s3):** Route +Add / Start buttons — inline `ontouchend` bypasses delegation, fires on iOS
- **2026-04-25 (s3):** Follow-up UX — replaced +Xd quick buttons (NaN bug) with `input[type=date]` pre-filled from existing follow-up; Save button enlarged and renamed "Save & Disposition Lead"
- **2026-04-25 (s3):** All fixes applied directly to `index.html` — live without waiting for daily CI
- **2026-04-27 (s7):** Email Inspection Reports — 📧 Email buttons on ATP report, service report, compliance summary, customer card; `sendEmailViaProxy()` central send function
- **2026-04-27 (s7):** Supabase Edge Function `send-email` — CORS-safe proxy for Resend API (browser cannot call Resend directly); deployed via GitHub Actions
- **2026-04-27 (s7):** Daily briefing reliability — decoupled from `rebuild.yml` into dedicated `send_briefing.yml` triggered on push to main (fixes silent cron failure on low-activity repos)
- **2026-04-27 (s7):** `deploy_edge_functions.yml` — auto-deploys Edge Functions from repo; eliminates need to copy-paste code into Supabase dashboard

## Next Session Priorities
1. Verify notes appear in compliance PDF/email after a live service visit
2. Confirm STATUS CHANGE banner renders correctly when ATP status changes between visits
3. Verify daily briefing email sends after next CI rebuild

## iOS PWA Rules (never violate these)
- **Buttons in injected HTML:** use inline `ontouchend="event.preventDefault();fn()"` + `onclick="fn()"` — NOT `addEventListener` on innerHTML-injected elements
- **Delegation modals (showCard):** `addEventListener` on the backdrop element AFTER `document.createElement` + `appendChild` — never on innerHTML content
- **`event.stopPropagation()`** on nested buttons inside delegated containers to prevent parent card handler from also firing
- **No** `addEventListener` on elements injected via `innerHTML` — attach AFTER `appendChild`
- **Dates:** always `localISO(d)` for storage, `parseLD(s)` for parsing — never `toISOString().slice(0,10)`
- **SW cache:** `build.py` auto-stamps `pic-YYYYMMDD`; after manual edits to sw.js, bump manually
- **iOS PWA cache refresh:** requires full app kill + reopen — sw update not immediate

## Key Files
| File | Purpose |
|------|---------|
| `build.py` | **Edit this** — generates prospecting_tool.html; also stamps sw.js cache date |
| `index.html` | Deployed output — keep in sync with build.py; overwritten by CI daily |
| `sw.js` | Service worker — auto date-stamped by build.py; bump manually after direct edits |
| `.github/workflows/rebuild.yml` | Daily CI: download data → build → commit → push |
| `.github/workflows/send_briefing.yml` | Daily briefing email — triggered on push to main + 11:30 UTC cron fallback |
| `.github/workflows/deploy_edge_functions.yml` | Deploys Supabase Edge Functions — triggers on changes to supabase/functions/ or manual dispatch |
| `.github/workflows/pages.yml` | GitHub Pages deploy — triggers on every push to main |
| `send_briefing.py` | Daily briefing email via Resend |
| `supabase/functions/send-email/index.ts` | Supabase Edge Function — CORS-safe Resend proxy for in-app email |
| `download_data.py` | Downloads FL DBPR inspection CSV files |
| `APP_STATUS.md` | This file — update at end of every session |
| `customers.json` | Seed customer data (used at build time) |
| `manifest.json` | PWA manifest |
