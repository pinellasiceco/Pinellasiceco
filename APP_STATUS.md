# Pinellas Ice Co — App Status
*Last updated: 2026-05-15 (session 24 — playbook moved to correct file) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-05-15 (session 21 — data pipeline refresh)
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
- **Concurrency group `rebuild`** in `rebuild.yml` — rapid-fire branch pushes cancel in-progress CI runs so only the latest commit builds; prevents parallel runs racing on `git push origin HEAD:main`
- **`atp/` copied in CI**: `rebuild.yml` now includes `git checkout origin/claude/... -- atp/` so the landing page folder is picked up from the feature branch and deployed to main automatically

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
- **New Since Yesterday** section: split into 🚨 Urgent / ⚠️ Watch / ℹ️ Info tiers based on `change_severity` field baked at CI build time

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
- Quoted outcome button in showCard logs `quoted` as first-class outcome; shows "📄 Moved to Pipeline → Quoted" toast and navigates to Quoted stage
- Pipeline cards (`.dc`) have `data-id` + `ontouchend` for iOS tap reliability; also handled in global IIFE
- **Forward-only disposition rules** (`getBlockedOutcomes(p)`): outcome buttons grey out with 🔒 when move would regress stage; Lost prospects get 🔄 Re-engage button to move back to In Play

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
- `sendEmailViaProxy(to, subject, html)` — central send function used by all email buttons; returns Promise<bool>
- `sendWithConfirmation(btn, sendFn)` — wraps any send operation: disables button, shows "Sending…", turns green "✓ Sent" on success, restores after 3s
- Email buttons on: ATP report overlay, service report preview, customer card (compliance summary), service log row
- Customer email address stored in `customers[id].email` via `saveCustomerEmail()`
- `emailServiceReport(id)` — emails rendered report HTML from `#report-content`
- `emailComplianceReport(id, btn)` — emails compliance summary (last service, ATP, machine, next due) + technician notes; accepts optional `btn` param for `sendWithConfirmation` UX
- `emailServiceSchedule(id)` — opens modal asking for recipient email (pre-fills `customers[id].email`); shows "Sending…" → "✓ Sent"; saves email address to customer record on send
- **Deploy**: any change to `supabase/functions/**` on main auto-triggers `deploy_edge_functions.yml`

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All 23 date storage sites use `localISO()` — no UTC off-by-one after 8pm ET
- Prospect follow-up dates: stored as local ISO string, compared correctly

## What's Broken / Watch List ⚠️

- **iPad copy-paste**: copying code blocks from chat on iPad adds angle brackets around URLs. Never paste code directly into Supabase editor — use the GitHub Actions deploy workflow instead.
- **`\n` in build.py strings**: never use `\n` inside Python triple-quoted strings for JS string literals — the literal newline breaks JS parsing and silently disables all buttons. Always use `\\n`.
- **Apostrophes/single quotes in JS strings**: any `'` character inside a single-quoted JS string literal in the HTML template breaks parsing — one broken string kills ALL buttons app-wide (silent failure). Common traps:
  - Contractions: `We'll`, `can't`, `don't`, `it's`, `you'll` — use `&#39;` or reword
  - Possessives: `client's`, `today's` — use `&#39;`
  - `\'` in Python triple-quoted strings outputs a bare `'` in JS — does NOT escape it in JS context
  - **`win.document.write('...')` trap**: any `alert('...')`, `toast('...')`, or string with `'` inside a `document.write('...')` call breaks the outer JS string — use `&#39;` or avoid inline single-quoted strings inside document.write entirely
  - **Review rule**: after writing any new JS string content (especially email HTML, toast messages, button labels, document.write calls), scan for apostrophes and replace with `&#39;`

If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

To force a fresh PWA load after a push: open the URL directly in Safari (not the home screen icon), wait for page to load fully, then the home screen icon will serve the updated version.

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
- **Per-customer report history**: Service → Reports shows one visit at a time (via dropdown). A full "Reports" sub-tab inside each customer card showing all past visits is the right long-term solution — backlogged.
- `build_date` in P[] records will appear after next CI rebuild; existing records have no `build_date` so freshness indicator shows nothing until rebuilt

## Recent Changes
- **2026-05-15 (s24 — move playbook to correct file):** Sales Playbook accordion removed from `build.py` Partners tab (271 lines gone — that content belongs in `sales_playbook_v2.html`). Five new sections added to `sales_playbook_v2.html`: Section 12 (Field Priority — core philosophy, 17 ATP target, DBPR intelligence framing), Section 13 (VM + Walk-In Sequence — 8am voicemail script + 2-hour follow-up walk-in), Section 14 (DBPR Field Scripts — Track A with 4 response variants + Track B no-citation energy-cost pitch), Section 15 (The Brush-Off — one-more-line rule, permission-to-return, same-day follow-up text + phone variant), Section 16 (Channel Partners — referral tier table, Cold Phone Call script, In-Person Encounter, Follow-Up Email, 5 objection cards). Five nav pills added to match. Partners tab in prospecting app is now just KPI bar → type filter chips → status filter chips → payout/sort → partner cards.
- **2026-05-15 (s23 — sales playbook rework):** Replaced Partner Talk Track with 8-section field-ready Sales Playbook in the Partners tab accordion. Section 1: Core Philosophy (compliance intelligence framing, ATP test as sole goal, 17-test June target). Section 2: VM + Walk-In Sequence (8am voicemail script + 2-hour walk-in follow-up). Section 3: Track A — DBPR Cited walk-in (citation count/date opener, open/defensive/skeptical/hesitate variants). Section 4: Track B — No Citation walk-in (energy cost hook → compliance pivot → 457 vs 10 close). Section 5: Cold Phone Call (gatekeeper line, DBPR-cited vs non-cited variants, book/info/busy-handling). Section 6: The Brush-Off (one-more-line rule, permission-to-return ask, same-day follow-up text, phone variant). Section 7: The ATP Test Visit (fail/pass/marginal reading scripts, close, not-today, think-about-it, price objection). Section 8: Objection Handling (6 objections: already-have-someone, cost, need-manager, just-inspected, no-time, send-info). Stage directions italic gray; spoken lines bold in blue-bordered panels. Apostrophe audit: 272 lines, 0 issues.
- **2026-05-15 (s22 — citation intelligence + partner talk track):**
  - **`extract_ice_snippet()`**: new Python function in `build.py` and `generate_citation_summary.py` — splits inspection text into sentences, returns ice-keyword sentences first (ice machine/mold/biofilm/scale/evaporator etc.) instead of blindly truncating at char limit; falls back to full text if no ice keywords found. Applied to `cit_observation` in `load_ice_citations()` and to `best_observation` in `generate_citation_summary.py`.
  - **DBPR filter chips**: two new Prospects tab preset buttons — "🕵️ DBPR (N)" (filters `ice_confirmed_dbpr`, sorts by citation count desc then days-since asc) and "🔁 Repeat (N)" (filters `cit_repeat >= 1 || cit_ice_count >= 2`). Live counts computed from P[] on each render via `updateDbprChipCounts()`.
  - **Partner Talk Track**: collapsible accordion section added to Partners tab in `build.py` — purple bordered `<details>` element sits between the KPI bar and filter chips. Six sub-sections (all collapsible): Program Overview, Cold Phone Call script (opening/qualify/offer/ask/close), In-Person Encounter + follow-up text, Follow-Up Email template, Handling Common Responses (5 objections), Referral Tiers (Bronze $99 / Silver $125 / Gold $150 + quarterly dinner). All apostrophes `&#39;`.


- **2026-05-14 (s20 — ATP landing page):** Created `atp/index.html` — single self-contained HTML marketing page served at `https://pinellasiceco.github.io/Pinellasiceco/atp/`. Zero external images; inline SVG logo with 3D isometric ice cube (three clearly distinct face fills: `#a8d4f0` top, `#5b9fd4` left, `#2e6aa0` right). Sections: hero with ATP number cards (457 RLU vs 10 RLU FDA standard), What We Do (3 icon cards), Why It Matters (copy + ATP scale bar), Inspection Protection Guarantee (gold-bordered card), Pricing ($129/mo feature list), second CTA, footer. Gold CTA button links to HubSpot booking URL (3 instances: hero, second CTA, sticky bar). Phone `(727) 855-6873` is a `tel:` link; `pinellasiceco.com` is an `https:` link. Sticky bottom bar with `env(safe-area-inset-bottom)` for iPhone home bar. IntersectionObserver scroll-reveal on all below-fold sections. Mobile-first; icon cards go single-column → row at 600px. `rebuild.yml` updated to copy `atp/` from feature branch to main so the file deploys automatically with every CI build.
- **2026-05-14 (s19/20):** Nine fixes across data integrity, UX, filters, and CI — (1) **Status guard in `loadCloudData()`**: null/undefined `row.data.status` no longer overwrites `p.status`; self-repair logic restores missing status from service evidence (`service_history` or `won_date`) and re-saves to Supabase with a "Restored N clients" toast. (2) **Same guard in `subscribeRealtime()`**: real-time payloads with null status can't corrupt live session state. (3) **P[] validation in `loadCloudData()`**: cloud data only replaces the embedded `P[]` array if records have a `name` field — prevents malformed Supabase data from producing a blank Prospects grid. (4) **`logServiceFromCal()` + `submitServiceLog()`**: both now preserve `p.status` when creating a new `customers[id]` object so every Supabase write includes status. (5) **`_renderApp()` re-renders active tab** after cloud load — Clients/Prospects/Pipeline no longer stay stale after data syncs. (6) **CSS `.panel.on{height:100%}`** + **`sw('all')` reflow trigger** (`void el.offsetHeight`) — fixes iOS Safari collapsing panel to 0 height when switching from `display:none` to `display:block`. (7) **Photo input `position:fixed`** — removes `overflow:hidden` container constraint that prevented iOS gallery picker from appearing (was camera-only). (8) **Follow-up filter fixed**: `followups` preset and `allFollowups` in `renderBriefing()` were using `!isC(p.id)` (no log entries) which always returned empty because you must log a contact to set a follow-up date — changed to `status==='prospect'` check. (9) **`send_briefing.py` Pinellas/recency filters**: all daily briefing sections (callbacks, strike zone, cold targets, NSY) now filter to Pinellas-only prospects with contact recency thresholds (7-day for urgent callbacks, 30-day for others) matching the in-app Home tab behavior. **Email UX**: `emailServiceSchedule(id)` now shows an address input modal (pre-fills saved email, confirms send with "Sending…" → "✓ Sent"); `emailComplianceReport` and ATP Email button now use `sendWithConfirmation()` helper for same UX; `srSendEmail` returns the proxy Promise. **CI**: added `concurrency: group: rebuild` to `rebuild.yml` — concurrent CI runs triggered by rapid commits now cancel in-progress builds instead of racing to push main (fixes the `! [rejected] HEAD -> main (fetch first)` error). **JS syntax errors fixed**: `We'll` apostrophe in emailServiceSchedule broke all buttons — replaced with `&#39;`; `alert('...')` inside `win.document.write('...')` broke outer JS string — removed entirely; both patterns documented in APP_STATUS.md watch list.
- **2026-05-14 (s18):** Eight fixes across data persistence, email, and report UX — (1) **Root cause of data loss fixed**: Supabase tables `pic_log`, `pic_customers`, `pic_phones`, `pic_settings`, `pic_partner_data` have BOTH `device_id` (NOT NULL original column) AND `user_id` (nullable, added later); all inserts now include both columns; reads/filters use `device_id`; `pic_prospects` and `pic_partners` use `user_id` only. (2) **Status guard in `loadCloudData`**: null/undefined `row.data.status` no longer overwrites `p.status`; self-repair restores missing status from service evidence and re-saves to Supabase. (3) **Same guard in `subscribeRealtime`**: real-time payloads with null status can't corrupt live session. (4) **`_renderApp()` re-renders active tab** after cloud load so Clients/Prospects/Pipeline don't stay stale. (5) **Pages CI fixed**: GITHUB_TOKEN pushes to main don't trigger other workflows; `pages.yml` now has a `workflow_run` trigger on "Rebuild Prospect Tool" completion so Pages deploys after every bot-pushed rebuild. (6) **Email proxy auto-derives URL**: `sendEmailViaProxy` now constructs `pic_email_fn_url` from the baked-in `_SUPABASE_URL` + `/functions/v1/send-email` if not already set — no manual Settings entry needed. Toast z-index raised to 9999 so it's always visible above modals. (7) **Service report email uses customer version**: `srSendEmail` (post-service-log ATP modal) now shows "Next Scheduled Service" date block instead of `$99 First Visit` prospect pitch. (8) **Service → Reports improvements**: photos now included in report HTML; visit dropdown appears when client has multiple visits (most recent first, date + ATP RLU label) — selecting a past visit regenerates the full report for that date including its ATP, photos, filter info, and report number; scroll fixed by removing inner overflow container (buttons now always reachable); Send button disables + shows "Sending…" on tap, turns green "✓ Sent" on success. **Storage**: `service-photos` bucket created with `own_photos` policy (SELECT/INSERT/UPDATE/DELETE, `bucket_id = 'service-photos'`). **RESEND_API_KEY** confirmed present in Supabase Edge Function secrets.
- **2026-05-12 (s17):** Two features — (1) **Data Freshness Indicator**: `build_date` field baked into every prospect record at CI build time (`str(TODAY)`); header subtitle shows `Data: today` (green) / `Data: yesterday` / `Data: Xd old` (red if >3 days) via `updateDataFreshness()`; yellow warning banner injected below header if data is 3+ days old via `checkDataStaleness()`; both called after every `_renderApp()` in all three `init()` branches; daily briefing email now shows "Data updated: Month Day, Year · N prospects · N CALLBACK" bar between header and stats. (2) **Before/After Photos on Service Visits**: photo section added to service log modal (📷 Add Photos button + hidden `<input type=file multiple>`); `addEventListener` wired after `appendChild` per iOS PWA rules; `_handlePhotoSelection()` shows thumbnails with ✕ remove; `_compressImage()` canvas-compresses to 800px/0.7 quality JPEG; `_uploadServicePhotos()` uploads to Supabase Storage bucket `service-photos` with signed 1-year URLs; `submitServiceLog()` made async — uploads first, passes `photo_urls` array to `logServiceFromCal()`; photos included inline in compliance email via IIFE in `srSendEmail()`; service history rows show 📷 N count with tap-to-view fullscreen overlay via `viewServicePhotos()`; requires user to create `service-photos` bucket in Supabase Storage (private, 5MB limit) + RLS policy (see brief).
- **2026-05-12 (s16e):** Fix JS syntax errors from Python triple-quoted string escaping — `Can\'t` → `Can't` (typographic apostrophe), `sw(\'data\')` in onclick → `sw(&#39;data&#39;)`, `lines.join('\r\n')` → `\\r\\n` (iCal), `svcNote+'\n\n'` → `\\n\\n`; any one of these caused entire script block to fail parsing, silently breaking all buttons.
- **2026-05-07 (s16d):** Two fixes — (1) **Account section in Settings**: new `#acct-section` `.dc` block at bottom of `#p-data` panel shows "Signed in as: [email]" + red **Sign Out** button (`doSettingsSignOut()`); shown/hidden by `initSettings()` based on `_userId`; confirms before signing out + calls `_sb.auth.signOut()` + shows login screen; hidden in demo/offline mode. (2) **Header/tab bar CSS**: added `viewport-fit=cover` to viewport meta so `env(safe-area-inset-*)` is populated on iPhone PWA; `header` uses `padding-top:max(0px,env(safe-area-inset-top))` + `flex-wrap:nowrap` so status bar is never covered and chips never wrap to a clipped second row; `.hchips` changed to `flex-wrap:nowrap;overflow-x:auto` so filter chips scroll horizontally rather than wrapping; fixed `.panels` typo → `.panel` in mobile `@media(max-width:480px)` block (was targeting nonexistent class) so `padding-bottom:calc(80px + env(safe-area-inset-bottom))` now actually clears the fixed bottom tab bar.
- **2026-05-07 (s16c):** Two fixes — (1) **Connect & Login button** added to Settings → Cloud Sync section (sky-blue button below "Save Credentials"): saves URL + anon key to localStorage then calls `location.reload()` so `init()` re-runs, picks up credentials, and shows the magic link login screen — fixes "no login screen after clearing Safari history" when CI hasn't baked credentials yet; (2) **Magic link redirect** verified correct — `emailRedirectTo` is already `https://pinellasiceco.github.io/Pinellasiceco/` in `signInWithMagicLink()`; no `localhost` references found in `build.py` or `index.html`; Supabase dashboard Site URL fix by user is the complete solution.
- **2026-05-07 (s16b):** Fix login screen not appearing. Root cause: `build_html()` replaces ALL `%%SUPABASE_URL%%` occurrences in the HTML template, including the guard checks inside `initSupabase()` like `_SUPABASE_URL!=='%%SUPABASE_URL%%'`. After replacement this became `_SUPABASE_URL!=='https://actual-url'` — always false — so `url` always fell through to localStorage (empty), `initSupabase()` returned null, and the app silently entered demo mode with no login screen. Fixed all 7 occurrences across `initSupabase()`, `updateSyncDot()`, `sendEmailViaProxy()`, `exportToBriefing()` in both `build.py` and `index.html`. Simple truthy check now: `var url=_SUPABASE_URL||localStorage.getItem('pic_supabase_url')||''`. Added `console.log('Supabase initialized: <url>')`, `console.log('No session found — showing login screen')`, `console.warn('Running without Supabase — demo mode')` for diagnostics.
- **2026-05-07 (s16):** Full cloud migration — Supabase Auth + magic link login + real-time sync. `initSupabase()` bootstraps from baked-in credentials (replaced by `build_html()` at CI time). `init()` is now async: checks auth session, shows `showLoginScreen()` if none, listens for `onAuthStateChange`. `loadCloudData()` loads all data from Supabase tables with localStorage fallback as offline cache. `subscribeRealtime()` subscribes to `pic_log` + `pic_customers` postgres_changes for live cross-device sync. `lSave()` / `custSave()` / `phSave()` now write to Supabase via `sbUpsert()` in addition to localStorage. Python `push_to_supabase()` pushes P[] and PARTNERS[] to Supabase at CI build time. `rebuild.yml` passes new secrets to build step. Settings overlay shows logged-in email + Sign Out button. Offline/demo mode preserved: if Supabase not configured, login screen skipped and app uses localStorage. 75/75 tests passing. sw.js bumped to `pic-20260507c`. **Requires Supabase SQL setup + 4 GitHub Secrets before login flow works** — see Next Session Priorities.
- **2026-05-07 (s15 patch):** Fix button in churn-risk widget now calls `navigateToClientService(id)` — switches to Clients tab, opens Service sub-tab, smooth-scrolls to `#svc-card-{id}` with 2s red outline highlight. Each `.svc-card` now has `id="svc-card-{p.id}"`. iOS `ontouchend` on Fix button. sw.js bumped to `pic-20260507b`.
- **2026-05-07 (s15):** Four fixes — (1) FIX 1: `normO()` was mapping `'quoted'` → `'in_play'`, breaking `getProspectStage()` so prospects never appeared in Pipeline → Quoted. Removed that mapping; `quoted` is now a first-class outcome with its own OI label ("Quote Sent ✓") and colour. Logging Quoted shows "📄 Moved to Pipeline → Quoted" toast and navigates to that stage. (2) FIX 2: `getBlockedOutcomes(p)` enforces forward-only stage progression — outcome buttons grey with 🔒 when a move would regress stage; Lost prospects get a dedicated 🔄 Re-engage button. (3) FIX 3: Pipeline `.dc` cards get `data-id` + `ontouchend`; Route "Details"/"Remove" buttons and Client "Details" button get `ontouchend`; global IIFE extended to handle `.dc[data-id]` taps — all reliable on iOS Safari. (4) FIX 4: Python `classify_change()` adds `change_severity` field (urgent/warning/info) to every P[] record. Home tab New Since Yesterday splits into 🚨 Urgent / ⚠️ Watch / ℹ️ Info sub-sections. `send_briefing.py` email restructured identically, subject line leads with urgent count. sw.js bumped to `pic-20260507a`; 75/75 tests passing.
- **2026-05-06 (s14):** Three bug fixes — (1) FIX 1: `emailComplianceReport` now reads technician notes from `service_history` (primary) with `atp_history.notes` fallback, so notes logged during visits appear in compliance PDF and email body; (2) FIX 2: `renderServiceCal` now shows all active customer statuses (`customer_recurring`, `customer_quarterly`, `customer_once`, `customer_intro`) — new clients appear in Service tab immediately after Close Deal, with plan type badge (Monthly/Quarterly/One-Time/Intro) in card subtitle; (3) FIX 3: Partner seed list expanded from 5 to 43 Pinellas County businesses across all 5 categories (10 hood cleaning, 9 pest control, 8 refrigeration, 7 beverage equipment, 7 HVAC) with real phone numbers and addresses; session-13 JS fixes backported to `build.py` so CI rebuilds don't regress them; sw.js bumped to `pic-20260506b`
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

## Cloud / Auth Architecture (session 16)

### Login Flow
- `initSupabase()` — creates Supabase client from baked-in `_SUPABASE_URL` / `_SUPABASE_ANON_KEY` (replaced at CI build time); falls back to localStorage `pic_supabase_url` / `pic_supabase_key`
- `init()` — async, auth-first: checks session → shows login screen if none → listens for `onAuthStateChange` → on SIGNED_IN loads cloud data + subscribes realtime
- `showLoginScreen()` — full-screen navy overlay with ice cube emoji, email input, "Send Magic Link" button; `addEventListener` pattern (iOS-safe)
- `hideLoginScreen()` — removes overlay, restores `#app` display
- `showLoadingScreen(msg)` / `hideLoadingScreen()` — navy loading overlay shown during `loadCloudData()`
- Magic link redirect: `access_token` in URL hash handled automatically by Supabase JS client; URL cleaned with `history.replaceState`
- Settings overlay shows "✓ Logged in as email@..." + **Sign Out** button when `_userId` is set

### Data Loading (`loadCloudData()`)
- Loads in order: pic_prospects → pic_partners → pic_log → pic_customers → pic_phones → pic_settings → pic_partner_data
- Prospects: if Supabase row exists, replaces embedded `P[]` array; otherwise falls back to embedded data from build
- All loaded data also written to localStorage as offline cache

### Real-time Sync (`subscribeRealtime()`)
- Channel: `pic-changes-{userId}` with `postgres_changes` listeners on `pic_log` and `pic_customers`
- On change: updates in-memory `log`/`customers`, re-renders active tab, flashes `sync-dot`, writes to localStorage cache
- `sync-dot` turns green when realtime `SUBSCRIBED`, amber on reconnect

### Save Functions
- `lSave()` — writes to localStorage + calls `sbUpsert('pic_log', pid, data)` for each pid if logged in
- `custSave()` — writes to localStorage + calls `sbUpsert('pic_customers', pid, data)` if logged in
- `phSave()` — writes to localStorage + calls `sbUpsert('pic_phones', id, data)` if logged in
- `sbUpsert(table, prospectId, data)` — upserts with `{user_id, prospect_id, data, updated_at}` using `onConflict:'user_id,prospect_id'`

### Build Pipeline (CI)
- `push_to_supabase(table, data)` Python function at end of `main()` pushes `records` → `pic_prospects` and `partners` → `pic_partners`
- `build_html()` replaces `%%SUPABASE_URL%%` and `%%SUPABASE_ANON_KEY%%` from env vars
- `rebuild.yml` passes `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_USER_ID` to build step

### GitHub Secrets Required
| Secret | Where to find |
|--------|--------------|
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_ANON_KEY` | Supabase → Settings → API (public anon key) |
| `SUPABASE_SERVICE_KEY` | Supabase → Settings → API (service_role key) |
| `SUPABASE_USER_ID` | `select id from auth.users` after first login |

### Supabase SQL to Run (one-time setup)
See the SQL in the prompt — creates `pic_prospects`, `pic_partners`, adds `user_id` column to existing tables, enables RLS, creates `own_*` policies. Enable realtime on `pic_log` and `pic_customers` in Supabase dashboard → Database → Replication.

### Offline / Demo Mode
- If Supabase is not configured (no URL/key in env or localStorage), app runs in local-only mode — login screen is skipped, localStorage data used directly. Zero regression for existing usage.

## Next Session Priorities
1. **Verify s19/20 fixes**: (a) Toscana Island Clubhouse appears in Clients tab and has correct MRR/ARR after reload; (b) "Follow-Ups" filter on Prospects tab shows prospects with scheduled follow-up dates; (c) Home tab Strike Zone / Cold Targets / Today's Plan only show Pinellas prospects not contacted recently; (d) Email Schedule modal asks for email, pre-fills saved address, shows Sending → ✓ Sent; (e) Compliance Email button shows same send confirmation UX
2. **Per-customer report history**: Add a "Reports" sub-tab inside each customer card showing all past service visits with ability to view/print/email any individual report — the visit dropdown in Service → Reports is the interim solution
3. **Verify photos end-to-end**: Log a service visit with photos → confirm upload toast → go to Service → Reports → confirm photos appear in preview and in the emailed report

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
| `atp/index.html` | ATP landing page — `https://pinellasiceco.github.io/Pinellasiceco/atp/` — single self-contained HTML file, no external images, inline SVG logo |
| `customers.json` | Seed customer data (used at build time) |
| `manifest.json` | PWA manifest |
