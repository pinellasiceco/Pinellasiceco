# Pinellas Ice Co — App Status
*Last updated: 2026-04-25 (session 2) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-25 (Architecture rewrite + ATP Report + 4 bug fixes merged to main)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- **Note:** `index.html` on main reflects code through the 5-tab rewrite and ATP report. The 4 bug fixes (route manual mode, remove scripts, daily builds, soft followup) are in `build.py` and will appear in `index.html` after the next daily CI rebuild at 7am ET.

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` sends daily briefing email via Resend

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
  - All buttons use `data-action` / `data-id` attributes (no string args in onclick)
  - Event delegation via `scHandle` with `addEventListener` on modal backdrop (iOS-safe)
  - Calendar widget for follow-up dates (no `input type="date"`)
  - Pitch/walkin/objection scripts removed
  - ATP Status Report button (📋 Report) opens print-ready leave-behind
  - Save log: missing follow-up date shows soft toast warning, does NOT block save

### Route Tab
- ZIP always syncs from Settings on load (no stale value)
- Manual mode shows explicit green "+Add" / orange "✓ Added" toggle buttons per card
- Manual mode displays hint text explaining how to build route
- Optimized build available (hours input triggers TSP routing)
- Anchor stop supported (`routeAnchor` / `clearAnchor()`)

### Pipeline Tab
- `renderPipeline()` groups in_play / intro_set / quoted prospects by follow-up urgency
- Shown in `p-pipeline` panel

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Service sub-tab: log service visits, track next service date, machine info
- Save Service Visit button: iOS-safe (`onclick` + `ontouchend` with `event.preventDefault()`)

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard
- `srGenerate(p, atpVal)` generates print-ready letter-size HTML report
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL
- Pop-up blocker fallback toast if `window.open` is blocked

## What's Broken / Watch List ⚠️

None known.

## What's Missing 🔲
- Nothing from the current feature roadmap is missing — all requested features are implemented

## Recent Changes
- **2026-04-25:** Architecture rewrite — 5-tab nav (Home/Prospects/Pipeline/Route/Clients), Pipeline tab, Clients/Service inner sub-tabs, Settings moved to gear button
- **2026-04-25:** ATP Status Report leave-behind — 📋 Report button in showCard, generates print-ready HTML with ATP status bar and FL inspection record
- **2026-04-25:** Bug fix — Route: ZIP from settings, manual mode +Add buttons, hint text
- **2026-04-25:** Bug fix — Removed pitch/walkin/objection call scripts from showCard and queue cards
- **2026-04-25:** Bug fix — Rebuild changed to daily cron; commit uses `--allow-empty`; briefing email updated to "Daily"
- **2026-04-25:** Bug fix — Follow-up date missing on in_play/not_now shows soft toast instead of blocking save
- **2026-04-25 (session 2):** Fix all date storage to use `localISO()` (local YYYY-MM-DD) instead of `toISOString()` (UTC); eliminates off-by-one dates after 8pm ET
- **2026-04-25 (session 2):** sw.js cache now date-stamped daily by build.py (`pic-20260425`, etc.); eliminates stale PWA installs

## Next Session Priorities
1. Verify Pipeline tab `renderPipeline()` displays correctly in production with real data (sorting, empty states)
2. Confirm ATP report prints cleanly on letter-size in iOS Safari (check margin/page-break behavior)
3. Consider adding a "New Client" quick-add flow from the Clients tab (currently requires going through showCard)

## iOS PWA Rules (never violate these)
- **Buttons:** `onclick="fn()"` + `ontouchend="event.preventDefault();fn()"` on every interactive element
- **OR:** `data-action`/`data-id` attributes + event delegation via `addEventListener` on a container
- **No** `addEventListener` on elements injected via `innerHTML` — attach AFTER `appendChild`
- **No** `input type="date"` in overlays — use button-based calendar widget only
- **Modals:** event delegation on the backdrop/container, not on each button
- **Dates:** parse as local noon (`new Date(y, m-1, d, 12, 0, 0)`), never `toISOString()` for display
- **SW cache:** bump `CACHE_NAME` in `sw.js` after significant code changes

## Key Files
| File | Purpose |
|------|---------|
| `build.py` | **Edit this** — generates prospecting_tool.html (never edit index.html directly) |
| `index.html` | Deployed output — overwritten by CI daily |
| `sw.js` | Service worker — bump `CACHE_NAME` after major updates |
| `.github/workflows/rebuild.yml` | Daily CI: download data → build → email → push |
| `.github/workflows/pages.yml` | GitHub Pages deploy — triggers on push to main |
| `send_briefing.py` | Daily briefing email via Resend |
| `download_data.py` | Downloads FL DBPR inspection CSV files |
| `APP_STATUS.md` | This file — update at end of every session |
| `customers.json` | Seed customer data (used at build time) |
| `manifest.json` | PWA manifest |
