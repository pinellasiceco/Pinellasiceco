# Pinellas Ice Co — App Status
*Last updated: 2026-04-27 (session 7) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-27 (briefing fix + email functions in build.py)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- `index.html` and `build.py` are fully in sync as of session 7

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` sends daily briefing email via Resend
- sw.js cache auto date-stamped by `build.py` on each rebuild (`pic-YYYYMMDD`) — no stale PWA

### Daily Briefing Email
- Decoupled into `send_briefing.yml` — triggers on push to main + 11:30 UTC cron fallback
- `validate_secrets()` — exits with code 1 (red X in Actions) if RESEND_API_KEY missing/malformed or BRIEFING_EMAIL missing
- `.strip()` on all env vars — handles whitespace/newline padding from GitHub secrets
- `User-Agent: PIC-Briefing/1.0` header — prevents Cloudflare CF-1010 block on api.resend.com
- Full HTTP error body printed on failure — visible in Actions log
- `sys.exit(1)` on send failure — workflow shows red X instead of silent green
- Contacted prospects filtered from cold sections via Supabase `pic_briefing_export` table (fails open if table missing)

### Email System (in-app)
- **Proxy required**: Resend blocks browser-direct calls (CORS 403) — all email goes through Supabase Edge Function
- Edge Function: `supabase/functions/send-email/index.ts` — deployed via `deploy_edge_functions.yml`
- **Deploy**: any change to `supabase/functions/**` on main auto-triggers `deploy_edge_functions.yml`
- App setting: Email Proxy URL in Settings → Email Proxy (stored as `pic_email_fn_url` in localStorage)
- `sendEmailViaProxy(to, subject, html)` — central send function used by all email buttons
- Email buttons: ATP report overlay, service report preview, client card service row
- Customer email address stored in `customers[id].email` via `saveCustomerEmail()`
- `emailServiceReport(id)` — emails rendered report HTML from `#report-content`
- `emailComplianceReport(id)` — emails lightweight compliance summary (last service, ATP, machine, next due)
- `srSendEmail(p, atpVal, emailTo)` — emails ATP status report (text logo, email-safe)
- `exportToBriefing()` — pushes contacted prospect IDs to Supabase `pic_briefing_export` table

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
  - ATP Status Report button (📋 Report) opens print-ready leave-behind
  - Follow-up: standard `input[type=date]` pre-filled with existing date if set
  - Save button: large "Save & Disposition Lead" button, always saves (no blocking)
  - Missing follow-up on in_play/not_now shows soft toast tip, does not block

### Route Tab
- ZIP always syncs from Settings on load (no stale value)
- Manual mode: explicit green **➕ Add** / orange **✓ Added** toggle buttons per card with inline `ontouchend`
- Manual mode displays hint text explaining how to build route
- Card body tap opens Details; only the Add button adds to route (no accidental adds)
- Optimized build available (hours input triggers TSP routing)
- Anchor stop supported (`routeAnchor` / `clearAnchor()`)

### Pipeline Tab
- `renderPipeline()` groups in_play / intro_set / quoted prospects by follow-up urgency

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Service sub-tab: log service visits, track next service date, machine info
- Save Service Visit button: iOS-safe (`onclick` + `ontouchend`)

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard
- `srGenerate(p, atpVal)` generates print-ready letter-size HTML report
- `srSendEmail(p, atpVal, emailTo)` emails same report via proxy (text logo)
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL
- 3-button layout: Cancel / 📧 Email / Print (with email address input)

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All date storage uses `localISO()` — no UTC off-by-one after 8pm ET

## What's Broken / Watch List ⚠️

- **Supabase briefing filter**: `pic_briefing_export` table must be created in Supabase SQL Editor before `exportToBriefing()` works. The briefing script fails open (shows all prospects) if table missing — not a blocker.
- **iPad copy-paste**: copying code blocks from chat on iPad adds angle brackets around URLs. Never paste code directly into Supabase editor — use the GitHub Actions deploy workflow instead.

If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

## What's Missing 🔲
- `pic_briefing_export` Supabase table needs to be created manually (SQL in next section)
- `SUPABASE_URL` and `SUPABASE_KEY` GitHub secrets optional — add for contacted-ID filtering

## Supabase Setup (one-time)
Run in Supabase SQL Editor to enable briefing filter:
```sql
create table if not exists pic_briefing_export (
  id uuid default gen_random_uuid() primary key,
  device_id text not null,
  contacted_ids jsonb not null default '[]',
  exported_at timestamptz default now()
);
alter table pic_briefing_export enable row level security;
create policy "allow_all" on pic_briefing_export for all using (true) with check (true);
```

## Recent Changes
- **2026-04-25:** Architecture rewrite — 5-tab nav, Pipeline tab, Clients/Service sub-tabs, Settings gear button
- **2026-04-25:** ATP Status Report — 📋 Report button in showCard, print-ready HTML
- **2026-04-25:** Bug fixes — Route ZIP, manual +Add buttons, remove call scripts, daily cron, soft followup warning
- **2026-04-25 (s2):** `localISO()` — all date storage uses local timezone (no UTC off-by-one)
- **2026-04-25 (s2):** sw.js daily date-stamp — eliminates stale PWA installs
- **2026-04-25 (s3):** Route +Add / Start buttons — inline `ontouchend` bypasses delegation, fires on iOS
- **2026-04-25 (s3):** Follow-up UX — replaced +Xd quick buttons (NaN bug) with `input[type=date]`
- **2026-04-27 (s7):** Daily briefing fix — `validate_secrets()`, `sys.exit(1)` on failure, `.strip()` on secrets, User-Agent header, full error body in logs
- **2026-04-27 (s7):** Briefing: contacted-prospect filter via Supabase `pic_briefing_export` table; fails open if missing
- **2026-04-27 (s7):** Email functions restored to `build.py` — CI was wiping them daily (were only in index.html)
- **2026-04-27 (s7):** In-app email: sendEmailViaProxy, srSendEmail, emailServiceReport, emailComplianceReport, exportToBriefing all now survive CI rebuilds
- **2026-04-27 (s7):** `deploy_edge_functions.yml` — auto-deploys Supabase Edge Functions from repo (eliminates iPad copy-paste problem)
- **2026-04-27 (s7):** `send_briefing.yml` — decoupled from rebuild, triggers on push to main

## Next Session Priorities
1. Verify daily briefing now sends reliably (check Actions log tomorrow morning)
2. Test in-app email end-to-end: ATP report email, service report email, compliance summary
3. Create `pic_briefing_export` table in Supabase if contacted-ID filtering is desired
4. Add `SUPABASE_URL` and `SUPABASE_KEY` to GitHub secrets if using briefing filter

## iOS PWA Rules (never violate these)
- **Buttons in injected HTML:** use inline `ontouchend="event.preventDefault();fn()"` + `onclick="fn()"` — NOT `addEventListener` on innerHTML-injected elements
- **Delegation modals (showCard):** `addEventListener` on the backdrop element AFTER `document.createElement` + `appendChild` — never on innerHTML content
- **`event.stopPropagation()`** on nested buttons inside delegated containers
- **No** `addEventListener` on elements injected via `innerHTML` — attach AFTER `appendChild`
- **Dates:** always `localISO(d)` for storage, `parseLD(s)` for parsing — never `toISOString().slice(0,10)`
- **SW cache:** `build.py` auto-stamps `pic-YYYYMMDD`; after manual edits to sw.js, bump manually
- **iOS PWA cache refresh:** requires full app kill + reopen

## Key Files
| File | Purpose |
|------|---------|
| `build.py` | **Edit this** — generates prospecting_tool.html; email functions, settings UI all live here |
| `index.html` | Deployed output — overwritten by CI daily; do NOT edit directly |
| `sw.js` | Service worker — auto date-stamped by build.py |
| `.github/workflows/rebuild.yml` | Daily CI: download data → build → commit → push |
| `.github/workflows/send_briefing.yml` | Daily briefing email — triggers on push to main + 11:30 UTC cron |
| `.github/workflows/deploy_edge_functions.yml` | Deploys Supabase Edge Functions on push to main |
| `.github/workflows/pages.yml` | GitHub Pages deploy — triggers on every push to main |
| `send_briefing.py` | Daily briefing email via Resend |
| `supabase/functions/send-email/index.ts` | Supabase Edge Function — CORS-safe Resend proxy |
| `APP_STATUS.md` | This file — update at end of every session |
