# Pinellas Ice Co — App Status
*Last updated: 2026-04-27 (session 7) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-27 (email buttons + proxy deployed)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- `index.html` and `build.py` are fully in sync as of session 7

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` sends daily briefing email via Resend
- sw.js cache auto date-stamped by `build.py` on each rebuild (`pic-YYYYMMDD`) — no stale PWA

### Navigation
- 5-tab layout: Home / Prospects / Pipeline / Route / Clients
- Gear ⚙️ button opens Settings overlay
- `sw('customers')` and `sw('service')` alias to Clients tab (backward compatible)
- Clients tab has inner sub-tabs: Clients / Service (via `setClientTab()`)

### Home Tab
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
- Manual mode: explicit green **➕ Add** / orange **✓ Added** toggle buttons per card with inline `ontouchend` — fires reliably on iOS PWA
- Manual mode displays hint text explaining how to build route
- Card body tap opens Details; only the Add button adds to route (no accidental adds)
- Optimized build available (hours input triggers TSP routing)
- Anchor stop supported (`routeAnchor` / `clearAnchor()`)
- Start 📍 button also uses inline `ontouchend` for iOS reliability

### Pipeline Tab
- `renderPipeline()` groups in_play / intro_set / quoted prospects by follow-up urgency
- Shown in `p-pipeline` panel

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Service sub-tab: log service visits, track next service date, machine info
- Save Service Visit button: iOS-safe (`onclick` + `ontouchend`)

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard
- `srGenerate(p, atpVal)` generates print-ready letter-size HTML report
- `srSendEmail(p, atpVal, emailTo)` emails same report via proxy (text logo instead of image)
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL
- Pop-up blocker fallback toast if `window.open` is blocked
- 3-button layout: Cancel / 📧 Email / Print

### Email System
- **Proxy required**: Resend blocks browser-direct calls (CORS 403) — all email goes through Supabase Edge Function
- Edge Function: `supabase/functions/send-email/index.ts` — deployed via GitHub Actions (`deploy_edge_functions.yml`)
- App setting: `pic_email_fn_url` (localStorage) = Edge Function URL; set in Settings → Cloud Sync
- App setting: `pic_supabase_key` (localStorage) = Supabase anon key (used as Bearer token)
- `sendEmailViaProxy(to, subject, html)` — central send function used by all email buttons
- Email buttons on: ATP report overlay, service report preview, customer card (compliance summary), service log row
- Customer email address stored in `customers[id].email` via `saveCustomerEmail()`
- `emailServiceReport(id)` — emails rendered report HTML from `#report-content`
- `emailComplianceReport(id)` — emails lightweight compliance summary (last service, ATP, machine, next due)
- **Deploy**: any change to `supabase/functions/**` on main auto-triggers `deploy_edge_functions.yml`

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All 23 date storage sites use `localISO()` — no UTC off-by-one after 8pm ET
- Prospect follow-up dates: stored as local ISO string, compared correctly

## What's Broken / Watch List ⚠️

- **Email error alerts**: temporarily using `alert()` instead of `toast()` for email failures (aids debugging). Switch back to `toast()` once email is confirmed stable.
- **iPad copy-paste**: copying code blocks from chat on iPad adds angle brackets around URLs. Never paste code directly into Supabase editor — use the GitHub Actions deploy workflow instead.

If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

## What's Missing 🔲
- Nothing from the current feature roadmap is missing

## Recent Changes
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
1. Confirm email sending works end-to-end (ATP report email, service report email, compliance summary)
2. Switch email error `alert()` back to `toast()` once email is confirmed stable
3. Verify daily briefing now sends reliably via `send_briefing.yml` push trigger
4. Verify Pipeline tab populates correctly with real data (need a CI rebuild with DBPR data)
5. Confirm ATP report prints cleanly on letter-size in iOS Safari

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
