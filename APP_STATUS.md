# Pinellas Ice Co — App Status
*Last updated: 2026-04-26 (session 4) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-25 (all fixes applied directly to index.html — live now)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- `index.html` and `build.py` are fully in sync as of session 3

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
- **Route state persists across tab switches** via `sessionStorage` (`pic_route`); loaded in `init()`
- **showCard Route button**: reflects current state on open ("📍 Route" vs "✓ On Route"); toggles instantly with visual border change on tap
- **YOUR ROUTE bar** (`#manual-route-bar`): appears above candidate list when stops exist; numbered stop list with ✕ per stop, Maps ↗ and Clear ✕ buttons
- **Route badge** on prospect cards ("📍 ON ROUTE") when prospect is in route
- **openMaps()**: uses lat/lon waypoints (`?api=1` format) when available; falls back to address-based; home ZIP as origin; `clearRoute()` now confirms before clearing

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
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL
- Pop-up blocker fallback toast if `window.open` is blocked

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All 23 date storage sites use `localISO()` — no UTC off-by-one after 8pm ET
- Prospect follow-up dates: stored as local ISO string, compared correctly

## What's Broken / Watch List ⚠️

None known. If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

## What's Missing 🔲
- Nothing from the current feature roadmap is missing

## Recent Changes
- **2026-04-26 (s4):** Route+ button fixed — unified sessionStorage state, showCard toggle, YOUR ROUTE bar, route badge on cards, lat/lon openMaps
- **2026-04-26 (s4):** New Since Yesterday feature — daily diff alert system in Home tab, email, and card badges
- **2026-04-25:** Architecture rewrite — 5-tab nav, Pipeline tab, Clients/Service sub-tabs, Settings gear button
- **2026-04-25:** ATP Status Report — 📋 Report button in showCard, print-ready HTML
- **2026-04-25:** Bug fixes — Route ZIP, manual +Add buttons, remove call scripts, daily cron, soft followup warning
- **2026-04-25 (s2):** `localISO()` — all date storage uses local timezone (no UTC off-by-one)
- **2026-04-25 (s2):** sw.js daily date-stamp — eliminates stale PWA installs
- **2026-04-25 (s3):** Route +Add / Start buttons — inline `ontouchend` bypasses delegation, fires on iOS
- **2026-04-25 (s3):** Follow-up UX — replaced +Xd quick buttons (NaN bug) with `input[type=date]` pre-filled from existing follow-up; Save button enlarged and renamed "Save & Disposition Lead"
- **2026-04-25 (s3):** All fixes applied directly to `index.html` — live without waiting for daily CI

## Next Session Priorities
1. Verify Pipeline tab populates correctly with real data (need a CI rebuild with DBPR data)
2. Confirm ATP report prints cleanly on letter-size in iOS Safari
3. Test follow-up → pipeline flow end-to-end: log "In Play" with date → verify prospect appears in Pipeline tab
4. Consider "New Client" quick-add from Clients tab (currently requires showCard → Won button)

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
| `.github/workflows/rebuild.yml` | Daily CI: download data → build → email → commit → push |
| `.github/workflows/pages.yml` | GitHub Pages deploy — triggers on every push to main |
| `send_briefing.py` | Daily briefing email via Resend |
| `download_data.py` | Downloads FL DBPR inspection CSV files |
| `APP_STATUS.md` | This file — update at end of every session |
| `customers.json` | Seed customer data (used at build time) |
| `manifest.json` | PWA manifest |
