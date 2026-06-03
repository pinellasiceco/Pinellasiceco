# Pinellas Ice Co — App Status
*Last updated: 2026-06-03 (session 59 — Segment conversion tracker, playbook nav updates, partner page fixes) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-05-28 (technician signature on ATP reports)
- Build script: `build.py` (repo root) → outputs `index.html` directly
- `index.html` regenerated from `build.py` using existing P[] data — fully in sync

## What's Working ✅

### Deployment
- Daily cron: `0 13 * * *` (9am ET) in `rebuild.yml` — runs ~2h after DBPR publishes (~6:48am ET confirmed via Last-Modified header)
- MAX_RECORDS=500 per daily scrape run (~14 min at 1.5s delay)
- Scraper delay: MIN_DELAY=1.5s, MAX_DELAY=3.0s (~40% faster than previous 2.5/4.5s)
- Commit uses `--allow-empty` — always pushes even if no data changes
- **Workflow revert loop permanently fixed**: CI commit step now does `git add -A` then `git restore --staged .github/` — Actions bot can never stage or push workflow files; prevents the daily rebuild from reverting workflow changes
- `pages.yml` deploys to GitHub Pages on every push to main (restored after erroneous deletion — was always needed)
- `send_briefing.py` runs as **final step in rebuild.yml** with `continue-on-error: true` — briefing failures never fail the build (session 54)
- Daily briefing fallback: `send_briefing.yml` cron at 13:00 UTC (9am ET) if rebuild fails
- sw.js cache bumped manually when patching index.html; `build.py` auto-stamps on CI rebuild
- **Concurrency group `rebuild`** in `rebuild.yml` — rapid-fire branch pushes cancel in-progress CI runs so only the latest commit builds; prevents parallel runs racing on `git push origin HEAD:main`
- **`atp/` copied in CI**: `rebuild.yml` now includes `git checkout origin/claude/... -- atp/` so the landing page folder is picked up from the feature branch and deployed to main automatically
- **`docs/protocol/` preserved in CI**: `rebuild.yml` `git checkout origin/main -- docs/protocol/` preserves static ATP protocol page through daily rebuilds
- **`assets/` preserved in CI**: `rebuild.yml` `git checkout origin/main -- assets/` preserves signature image and other assets through daily rebuilds
- **`build_violations_list.py` step**: `continue-on-error: true` — failure visible in Actions but non-blocking (session 54)

### Reports Tab: Segment Conversion Tracker (session 59)
- **`renderSegmentTracker()`** in `build.py` — new section injected into Reports tab, renders after the DBPR Citation to Client Conversion section
- **Goal Progress card**: active client count vs. 30-client goal with a color-coded progress bar (green ≥30, amber ≥21, red below)
- **Weekly Activity card**: unique prospects touched in the last 7 days vs. a goal of 20, with a progress bar
- **Five segment rows**: Gold ⭐ / Repeat 🔄 / DBPR 📋 / Premium ★ / Golf ⛳ — each shows Total / Contacted / Closed / Close Rate / Target Range / Status badge (✓ On Track / ○ Getting There / ● Below Target)
- **Target ranges**: Gold 20–28%, Repeat 10–15%, DBPR 5–10%, Premium 8–12%, Golf 15–20%
- **Helper functions added**: `safeRate(a,b)`, `segStatusStyle(rate,low,high)`, `calcWeeklyContacts()`, `calcSegmentStats()`
- **Data sources**: `P[]` array for segment filters, global `log[pid]` for contact history, `customers[pid].status` for closed status
- **Segment filter logic** mirrors `setPreset()` exactly: Gold = `ice_gold===true`; Repeat = `(cit_repeat≥1 or cit_ice_count≥2) and !ice_gold`; DBPR = `ice_confirmed_dbpr and !ice_gold and cit_ice_count<2`; Premium = `!ice_confirmed_dbpr and premium_score≥4`; Golf = `venue_type==='golf'`

### Sales Playbook Nav & Partner Page Fixes (session 59)
- **Three new nav pills** in `sales_playbook_v2.html`: Pinellas Operator Census (`pinellas-ice-census.html`), Full Census & Demand Analysis (`pinellas-ice-full-census.html`), Intelligence Update (`pinellas-intelligence-update.html`)
- **Email Templates nav pill** in `sales_playbook_v2.html`: links to `https://pinellasiceco.github.io/Pinellasiceco/email-templates.html`, opens `target="_blank"`
- **Back buttons** on all three new census/intelligence docs — `position:fixed; top:12px; left:16px; z-index:999`; each styled with the file's own CSS variables; links back to `sales_playbook_v2.html`
- **Logo URL fix** in `partner-coastline.html` and `partner-pelican.html`: 3 instances each corrected from `assets/pic_logo.png` to `pic_logo.png` in the raw GitHub URL

### Strategic & Gold Contact Research (session 58)
- **`research_contacts.yml`**: GitHub Actions `workflow_dispatch` workflow — checks out repo, runs `research_contacts.py`, commits `docs/data/strategic_contacts.json` to main. Timeout 90 min. Fetch+rebase before push prevents conflict if main was updated during the long script run.
- **`research_contacts.py`**: Searches Anthropic API (claude-haiku-4-5 + web_search tool) for Director of Engineering / F&B Director / GM at all Premium accounts (premium_score >= 4). Skip-if-exists skips only entries where `dm_name` is already set — null entries are re-researched on re-runs. Saves checkpoint every 50 accounts. Output: `docs/data/strategic_contacts.json`.
- **`research_gold_contacts.yml`**: Same structure, targets Gold leads — `workflow_dispatch`, 90-min timeout, commits `docs/data/gold_contacts.json`.
- **`research_gold_contacts.py`**: Searches for Owner / GM / Bar Manager at all `ice_gold == True` prospects (~538 accounts). Same skip-if-exists and checkpoint-every-50 patterns. Expected found rate 10-20% (independent restaurants have limited web presence). Output: `docs/data/gold_contacts.json`.
- **P[] extraction**: Both scripts use bracket-counting (not regex) to extract the P[] array from index.html — regex with large quantifiers fails on the 9000+ record array.
- **`dm_title` field in showCard**: DM panel now has a "Title or role" input above the phone field. Saved alongside `dm_name` and `dm_phone` in customer record. Displayed statically as a muted label next to the DM name when set.
- **`importStrategicContacts()`** in app: fetches `docs/data/strategic_contacts.json` from GitHub Pages; writes `dm_name` + `dm_title` to customer records; skips any account where user has already entered a different name. Toast shows count imported or "0 found — run workflow first" if file is empty.
- **`importGoldContacts()`** in app: same pattern, fetches `docs/data/gold_contacts.json`.
- **Settings buttons**: "Strategic Contacts" section has blue Import Strategic Contacts button; "Gold Lead Contacts" section has amber Import Gold Contacts button. Both in Settings overlay.
- **`docs/data/` preserved in CI**: `rebuild.yml` commit step includes `git checkout origin/main -- docs/data/` — JSON contact files survive daily rebuilds.
- **Known**: Gold workflow first run found 49/538 contacts (9.1%) — slightly below 10% warning threshold but results look legitimate. Re-run after push fix committed the file correctly.

### CI Build Fixes (session 57)
- **Emergency closure xlrd fallback**: `load_emergency_closures()` in `build.py` now falls back to `pandas`+`xlrd` when `openpyxl` fails — DBPR serves EOS weekly files as legacy XLS (not XLSX/ZIP), so `openpyxl` was silently returning an empty set; emergency-closed businesses are now correctly flagged
- **`fdinspi_2122.xlsx` removed from HISTORICAL**: DBPR took the 2021-22 statewide file offline — URL was returning an HTML page (0.2 MB). Entry removed from `HISTORICAL` in `download_data.py` so CI no longer attempts or caches it

### Security & CI Resilience (session 54)
- **Stripe discount cap**: `monthly_discount` capped at $100 in `stripe-checkout/index.ts` — prevents crafting a $0 subscription via oversized discount
- **JSON NaN/Inf sanitization**: `_nan_to_null()` helper in `build.py` replaces float NaN/Inf with `null` before `json.dumps` — prevents invalid JS in output
- **Atomic HTML write**: `prospecting_tool.html` and `index.html` written via temp + `os.replace()` — prevents torn output file on crash
- **Atomic CSV write**: `ice_citation_by_business.csv` written via temp + `os.replace()` — prevents torn file on crash
- **Scraper 429 retry**: `fetch_page()` retries up to 2 times on HTTP 429, sleeping `Retry-After` seconds between attempts (was sleep-once-then-return-None)
- **Data freshness gate**: `download_data.py` exits 1 if inspection data is >21 days old — stale-but-present data no longer passes silently
- **License CSV guard**: `download_data.py` logs explicit WARNING when `hrfood3_licenses.csv` download fails
- **Citation script fatal errors**: `generate_citation_summary.py` uses `sys.exit(1)` on all 4 fatal error paths (was bare `return` / exit 0)
- **Citation pipeline visibility**: citation summary step uses `continue-on-error: true` (was `|| echo` which swallowed failures silently)
- **Observation snippet pre-filter**: `generate_citation_summary.py` pre-filters narratives to ice-keyword rows before selecting best snippet — prevents unrelated violation text appearing in citation cards

### Navigation
- **7-tab layout**: Home / Prospects / Pipeline / Route / Clients / Partners / Reports
- Tab bar is horizontally scrollable on mobile (overflow-x, scroll-snap, hidden scrollbar)
- `REPORTS_TAB_ENABLED` Python flag in `build.py` — set False to hide tab entirely with no JS errors
- Gear button opens Settings overlay
- `sw('customers')` and `sw('service')` alias to Clients tab (backward compatible)
- Clients tab has inner sub-tabs: Clients / Service (via `setClientTab()`)

### Follow-Up Nudge System (session 32)
- **`NUDGE_TEMPLATES`** — 5 scenario templates baked into the JS: `interested_no_book` (3d), `noshow` (1d), `voicemail_only` (4d), `call_back_later` (21d), `sent_info` (3d). Each has a `build(p, cust)` function that merges DM name, sender name (`pic_sms_name`), and DBPR citation month into a ready-to-send text
- **`renderNudgeSection()`** — populates `<div id="nudge-section">` on the Home tab. Finds up to 5 Pinellas prospects that: have a log entry, are not clients, are past their template's `days_after` threshold, have not been dismissed, have not been nudged in the last 7 days, and have a phone number. Sorted by `nudgePriority()` (DBPR citations +40/+25, no-show +30, revenue, recency).
- **`buildNudgeCard(nudge)`** — renders each nudge card: business name + DBPR badge, template label + days-since label, business-line warning if no DM cell, 160-char italic preview, send Text button, + Cell button (opens showCard) if no DM phone, dismiss button. All buttons use `data-nudgepid` / `data-nudgetpl` attributes — no inline quoted string args.
- **`sendNudgeText(pid, templateId)`** — builds `sms:+1{phone}?body={encodeURIComponent(text)}` URI, opens native Messages app. Records `customers[pid].last_nudge_date` and resets `nudge_dismissed`. Toast "Messages opened — review and send" fires 800ms later.
- **`dismissNudge(pid)`** — sets `customers[pid].nudge_dismissed = true`, calls `custSave()`, re-renders nudge section, shows toast.
- **`getNudgeTemplate(pid)`** — maps last log outcome to template ID: `intro_set` → noshow; notes with "call back"/"few weeks"/"next month" → call_back_later; `voicemail` → voicemail_only; `in_play`/`no_contact` → interested_no_book.
- **Decision Maker fields in showCard** — sky-blue panel above Contacts & Intel: "First name" text input (`sc-dm-name`) + "Cell / direct line" tel input (`sc-dm-phone`) + Save button (`sc-save-dm`). Saves to `customers[pid].dm_name` / `customers[pid].dm_phone` via `custSave()`. Saving also resets `nudge_dismissed`.
- **Settings — sender name** — "Your name for text templates" input (`sms-name-input`) in App Settings section. Saved to `localStorage` key `pic_sms_name` on input/change. Pre-filled by `initSettings()`. Replaces `{your name}` placeholder in all templates.
- **No # badge** — amber badge on prospect cards in Prospects tab when the prospect has log entries but no phone (neither `p.phone` nor `customers[pid].dm_phone`). Disappears once a number is added.
- **String safety**: all template string literals contain no apostrophes; `p.name` is concatenated as a JS variable at runtime; `encodeURIComponent()` handles the full message body for the SMS URI

### Home Tab
- **TODAY'S PLAN** section at top: ranked action list (action score = urgency x revenue x recency x ice risk boost), max 8 stops
- **Add All to Route** button in TODAY'S PLAN adds all stops and switches to Route tab
- Strike Zone section shows top-scored prospects by city cluster
- In Play follow-ups grouped by urgency: Overdue / Today / This Week / This Month
- Cold targets grid loads on first open
- **New Since Yesterday** section: split into Urgent / Watch / Info tiers based on `change_severity` field baked at CI build time
- MRR/ARR KPI row, Weekly Funnel, Goal Pacing, and Loss Breakdown blocks **removed** — moved to Reports tab
- **One-time revenue flash card** on Home tab — shows when one-time revenue >$0 this month (intro fees + deep cleans)

### Prospects Tab
- Full prospect list with search/filter
- showCard detail overlay:
  - All buttons use `data-action` / `data-id` + event delegation on modal backdrop (iOS-safe)
  - Pitch/walkin/objection scripts removed
  - ATP Status Report button opens print-ready leave-behind
  - Follow-up: standard `input[type=date]` pre-filled with existing date if set
  - Save button: large "Save & Disposition Lead" button, always saves (no blocking)
  - Missing follow-up on in_play/not_now shows soft toast tip, does not block

### Route Tab
- ZIP always syncs from Settings on load (no stale value)
- **City cluster chips**: Tarpon / Palm Harbor / Dunedin / Clearwater / Largo / Safety Harbor / St. Pete / All — sets ZIP + triggers rRoute()
- Manual mode: explicit green Add / orange Added toggle buttons per card with inline `ontouchend` — fires reliably on iOS PWA
- Manual mode displays hint text explaining how to build route
- Card body tap opens Details; only the Add button adds to route (no accidental adds)
- Optimized build available (hours input triggers TSP routing)
- Anchor stop supported (`routeAnchor` / `clearAnchor()`)
- Start button also uses inline `ontouchend` for iOS reliability

### Pipeline Tab
- 4-stage tab UI: **In Play / Quoted / Won / Lost** (via `setPipeStage()` / `pipeStage` state)
- KPI bar removed — aggregate metrics moved to Reports tab
- `getProspectStage(p)` classifies each prospect by stage (checks p.status + last log outcome)
- In Play / Quoted: grouped by follow-up urgency (Overdue / Today / Week / Month / Later)
- Won / Lost: chronological list with outcome badge
- Ice risk badges (High/Med) shown on In Play / Quoted cards
- Lost `not_now` (Timing) auto-resurfaces after 90 days (not shown in Lost)
- Quoted outcome button in showCard logs `quoted` as first-class outcome; shows "Moved to Pipeline → Quoted" toast and navigates to Quoted stage
- Pipeline cards (`.dc`) have `data-id` + `ontouchend` for iOS tap reliability; also handled in global IIFE
- **Forward-only disposition rules** (`getBlockedOutcomes(p)`): outcome buttons grey out when move would regress stage; Lost prospects get Re-engage button to move back to In Play

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Client card service row: **Email Report only** (Log Visit + Set Next Due removed — use Service sub-tab)
- `churnClient(id)` marks prospect churned with confirm dialog; red Churn button on non-churned cards
- Service sub-tab: log service visits, track next service date, machine info
- Save Service Visit button: iOS-safe (`onclick` + `ontouchend`)
- **Recent Visits inline** (`buildRecentServiceHistory(p,c)`): last 3 visits shown on each service card — date, type (60-Day / Deep Clean), pre/post ATP with green/amber/red color coding, filter badge, photo count badge, 120-char notes preview; each row is tappable (`data-svcpid` / `data-svcvisit` attributes, `event.stopPropagation()`)
- **`openVisitReport(pid, visitIndex)`**: sorts history date-descending (same as display), picks visit by index, passes `_report_date_override` + `_visit_photo_urls` to `srGenerate()` so the report shows that visit's actual date and photos
- **`srGenerate()` date override**: respects `p._report_date_override` in the report header; photo block uses `p._visit_photo_urls` when set (falls back to most-recent visit)
- **Last RLU chip** in card header — green badge pulled from most recent `Service_history[].atp`
- **Escalation flow** — "Escalate" button on each service card opens `openEscalation(pid)` bottom-sheet modal:
  - 8 issue types: No Ice, Water Leak, Electrical, Refrigerant, Replace, Pest, Hood, Other
  - `ESCALATION_TREE` constant maps each issue to a partner type + recommended action string
  - `selectEscalation(pid, issueId)` drills in: shows action callout box + matching PARTNERS[] entries with tap-to-call phone links + escalation notes textarea
  - `logEscalation(pid, issueId)` saves timestamped record to `customers[pid].escalation_notes[]` via `custSave()`
  - `closeEscBg()` helper avoids quoting `getElementById` inside inline onclick strings

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard; persists entered ATP value + notes to `atp_history` before generating PDF/email
- `srGenerate(p, atpVal, notes)` generates print-ready letter-size HTML report; shows amber STATUS CHANGE banner if ATP label (PASS/MARGINAL/FAIL) differs from previous visit
- **Report navigation bar**: sticky dark bar at top of the report popup — Back to App (`window.opener.focus(); window.close()`) and Print (`window.print()`); hidden via `@media print` so never appears on paper
- **Auto-print gated on context**: `setTimeout(w.print(), 600)` only fires when `p._report_date_override` is NOT set — direct ATP overlay flow still auto-prints; opening a historical visit via `openVisitReport()` shows report without triggering print
- `srSendEmail(p, atpVal, emailTo, notes)` emails same report via proxy; same status change banner logic
- Scale: <=0 = PENDING, <=10 = PASS, 11-100 = MARGINAL, >100 = FAIL
- `atp_history` entries: `{date, pre, post, notes}` — notes field populated by both `submitServiceLog` and `scStatusReport`
- Pop-up blocker fallback toast if `window.open` is blocked
- 3-button layout: Cancel / Email / Print
- Print CSS: `@media print { @page { margin: 0.3in } }`, `zoom: 0.92`, padding reduced — guaranteed 1-page output on iOS and desktop
- **Technician signature block**: `%%SIG_BLOCK%%` baked into in-app preview and print popup; `%%SIG_BLOCK_EMAIL%%` baked into email version (data URI + block layout, no flex); displays John Serrantino / Lead Technician · Pinellas Ice Co. + ATP protocol link

### showCard Detail Overlay
- **WHY THIS PROSPECT MATTERS** navy intel panel (`buildIntelSummary(p)`) — shows ice violations, callback count, inspection timeline, machine count, risk level
- **Ice risk badges** (High Risk / Med Risk) in chips row
- **Quoted** outcome button (purple) added alongside In Play / Intro Set
- All buttons: iOS-safe inline `ontouchend` + `onclick`
- **Service History tappable** — each visit row has `data-svcpid`/`data-svcvisit` + `ontouchend`+`onclick` calling `openVisitReport()`; sorted date-descending; `event.stopPropagation()` prevents overlay close; chevron on right; shows up to 5 visits

### Ice Compliance Risk Score
- `calc_ice_risk(record)` Python function bakes `ice_risk_prob` (0-100), `ice_risk_level` (Low/Med/High), `ice_risk_reason` into every P[] record
- Factors: ice violations <6mo (+25), total ice violations (x8), callbacks (x15), chronic flag (+15), days since inspection (+5/10), machine count (+4/8), business type keywords (+6)
- High >= 65, Medium >= 35, Low < 35
- Ice risk boosts action score in TODAY'S PLAN: High=1.4x, Medium=1.2x

### Email System
- **Proxy required**: Resend blocks browser-direct calls (CORS 403) — all email goes through Supabase Edge Function
- Edge Function: `supabase/functions/send-email/index.ts` — deployed via GitHub Actions (`deploy_edge_functions.yml`)
- App setting: `pic_email_fn_url` (localStorage) = Edge Function URL; set in Settings → Cloud Sync
- App setting: `pic_supabase_key` (localStorage) = Supabase anon key (used as Bearer token)
- `sendEmailViaProxy(to, subject, html)` — central send function used by all email buttons; returns Promise<bool>
- `sendWithConfirmation(btn, sendFn)` — wraps any send operation: disables button, shows "Sending...", turns green "Sent" on success, restores after 3s
- Email buttons on: ATP report overlay, service report preview, customer card (compliance summary), service log row
- Customer email address stored in `customers[id].email` via `saveCustomerEmail()`
- `emailServiceReport(id)` — emails rendered report HTML from `#report-content`
- `emailComplianceReport(id, btn)` — emails compliance summary (last service, ATP, machine, next due) + technician notes
- `emailServiceSchedule(id)` — opens modal asking for recipient email (pre-fills `customers[id].email`); shows "Sending..." → "Sent"; saves email address to customer record on send
- **Deploy**: any change to `supabase/functions/**` on main auto-triggers `deploy_edge_functions.yml`

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All 23 date storage sites use `localISO()` — no UTC off-by-one after 8pm ET
- Prospect follow-up dates: stored as local ISO string, compared correctly

## What's Broken / Watch List ⚠️

- **Stripe redirect wipes in-memory state**: Any data set on `customers[pid]` in memory before `window.location.href = stripeUrl` is lost — Stripe navigates away and the app reloads from localStorage. Always call `custSave()` immediately after writing anything to `customers[pid]` that needs to survive the redirect.
- **iPad copy-paste**: copying code blocks from chat on iPad adds angle brackets around URLs. Never paste code directly into Supabase editor — use the GitHub Actions deploy workflow instead.
- **`\n` in build.py strings**: never use `\n` inside Python triple-quoted strings for JS string literals — the literal newline breaks JS parsing and silently disables all buttons. Always use `\\n`.
- **`\'` in Python triple-quoted strings**: produces a bare `'` in the output — does NOT produce `\'` in the JS source. To get an escaped single quote in JS, write `\\'` in Python. Use named helper functions (e.g. `closeEscBg()`) to avoid the quoting chain entirely.
- **Apostrophes/single quotes in JS strings**: any `'` character inside a single-quoted JS string literal in the HTML template breaks parsing — one broken string kills ALL buttons app-wide (silent failure). Common traps:
  - Contractions: `We'll`, `can't`, `don't`, `it's`, `you'll` — use `&#39;` or reword
  - Possessives: `client's`, `today's` — use `&#39;`
  - **`win.document.write('...')` trap**: any string with `'` inside a `document.write('...')` call breaks the outer JS string — use `&#39;` or avoid inline single-quoted strings inside document.write entirely
  - **Review rule**: after writing any new JS string content (especially email HTML, toast messages, button labels, document.write calls), scan for apostrophes and replace with `&#39;`

If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

To force a fresh PWA load after a push: open the URL directly in Safari (not the home screen icon), wait for page to load fully, then the home screen icon will serve the updated version.

### Reach-In Cooler Add-On Service (session 46)
- **Flag**: `REACH_IN_ENABLED = True` — live as of session 46
- **Pricing**: +$50/mo (monthly plan) or +$40/mo (quarterly plan) — baked at CI build time; Stripe line item uses `price_data` (works in both test and live mode)
- **Close Deal overlay**: Reach-In Cooler Service toggle (pre-checked if already enrolled); Year 1 Total updates live; `reach_in: true` sent to Edge Function on checkout
- **Edge Function** (`stripe-checkout/index.ts`): destructures `reach_in` boolean; adds reach-in `price_data` line item for subscription plans; `hasReachIn` in customer + session + subscription metadata
- **Service log**: reach-in ATP section shown only for enrolled clients (`reach_in_service === true`); pass/fail buttons + per-unit location + RLU inputs; state reset on every modal open
- **Reports tab**: `buildReportReachInSection()` injected into `loadReportClient()` — shows ATP table (with pre/post RLU with per unit) for enrolled clients with data; "not tested this visit" for enrolled with no data; upsell panel for non-subscribers
- **Stripe return**: `_pending_reach_in` + `_pending_reach_in_amount` persisted to localStorage before redirect; restored in `checkStripeReturn()` before `scMarkWon()` overwrites customer record
- **Service history badge**: RI checkmark/cross badge on visit rows when reach-in data present
- **Calendar badge**: Reach-In + Coolers badge on client service calendar cards for enrolled clients
- **showCard**: Reach-In Units count shown in fact rows when `reach_in_count` is set

### Sales Playbook v2 (`sales_playbook_v2.html`)
- **URL**: `sales_playbook_v2.html` in repo root — accessible from main index
- Complete rewrite with ATP-first philosophy (all old pitch/pricing sections removed)
- **Sections**: The Market, Walk-In, Phone Call, ATP Pitch, Objections, Buyer Personas, Know Your Prospect, Competitors, The Close, Follow-Up, Mindset, Core Philosophy, VM + Walk-In, Track A (no gatekeeper), Track B (gatekeeper), Cold Phone, Brush-Off, Can't Get There, Voicemail, Field Objections, Power Number
- **Pricing throughout**: $228 bundled close ($99 initial deep clean + $129 first month) / $129/month quarterly (service every 90 days)
- **Inspection Protection Guarantee**: cited within 30 days of service → full $228 refund
- Nav includes "Practice Scenarios" pill linking to `docs/sales_scenarios.html`
- **Preserved in CI**: `git checkout origin/main -- sales_playbook_v2.html` in `rebuild.yml`

### Sales Scenarios Page (`docs/sales_scenarios.html`)
- **URL**: `https://pinellasiceco.github.io/Pinellasiceco/docs/sales_scenarios.html`
- **16 fully-scripted simulated pitch conversations** — walk-in to outcome (expanded from 11 in session 57)
- Covers: Perfect Close, Gatekeeper, Commitment Objection, Existing Vendor (Polar), Corporate Account, Brush-Off (Ray), Clean Machine Objection, Timing/Access, Multi-Machine, Warm Follow-Up, Price Objection, Referral, Callback, Seasonal Surge, Inbound Lead, Tech Upsell
- Each scenario: difficulty badge, situation badge, character/setting context box (with DBPR record), full dialogue, ATP reading boxes (before/after RLU), outcome summary with dots, key lesson
- Every scenario reaching a close includes the Inspection Protection Guarantee
- Every scenario reaching the machine includes "[You photograph the interior...]" stage direction
- Linked from Sales Playbook v2 nav pill ("Practice Scenarios")
- **Preserved in CI**: `git checkout origin/main -- docs/sales_scenarios.html` in `rebuild.yml`

### Dirty Ice Map (`docs/map/`)
- **URL**: `https://pinellasiceco.github.io/Pinellasiceco/docs/map/`
- Public-facing Leaflet.js dark heatmap — DBPR ice machine citations across Pinellas County
- `data.json` generated by `build_map_export()` in `build.py` on every CI rebuild — coordinates fuzzed ±0.001° (~100m), no business names or exact addresses
- Red pulsing SVG markers for mold/biofilm citations (`ice_gold=true`); amber circles for standard ice citations
- Dot radius scaled by citation count: 6px (1), 8px (3+), 10px (5+)
- Stats bar: animated counters for total citations, mold/biofilm count, cities affected
- CTA bar: "Free ATP Test →" button linking to HubSpot booking
- CartoDB dark tile layer (no API key required)
- **Preserved in CI**: `git checkout origin/main -- docs/map/` in `rebuild.yml`
- Linked from `docs/explore/index.html` (6th card in path-cards section)

### Technician Field Manual
- **URL**: `https://pinellasiceco.github.io/Pinellasiceco/docs/fieldmanual/` — COMPLETE and deployed
- **Access**: Settings tab → "Open Technician Field Manual" button
- **Coverage**: Hoshizaki, Manitowoc, Ice-O-Matic, Scotsman, Follett + Reach-In Coolers add-on page
- **Per-brand pages**: 60-day maintenance checklist, deep clean steps, brand-specific failure modes, warranty codes, chemical concentrations
- **Reach-In page** (`reachin.html`): 8 sections — service overview, tools checklist, step-by-step protocol, ATP reference (color-coded table, 100 RLU threshold), gasket condition rating
