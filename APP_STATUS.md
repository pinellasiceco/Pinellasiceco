# Pinellas Ice Co — App Status
*Last updated: 2026-04-26 (session 5) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-26 (session 5 — referral system, route fixes, CI fix)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- `index.html` and `build.py` are fully in sync as of session 5

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` sends daily briefing email via Resend — reads from `prospecting_tool.html` (fresh) first
- sw.js cache auto date-stamped by `build.py` on each rebuild (`pic-YYYYMMDD`) — no stale PWA
- CI pip deps: `pandas scikit-learn numpy requests openpyxl` (fixed s5 — was missing pandas/sklearn/numpy)

### Navigation
- 5-tab layout: Home / Prospects / Pipeline / Route / Clients
- Gear ⚙️ button opens Settings overlay
- `sw('customers')` and `sw('service')` alias to Clients tab (backward compatible)
- Clients tab has inner sub-tabs: Clients / Service (via `setClientTab()`)
- Service tab has sub-tabs: Calendar / Route / Reports / Tutorials / Referrals

### Home Tab
- Strike Zone section shows top-scored prospects by city cluster
- In Play follow-ups grouped by urgency: Overdue / Today / This Week / This Month
- Cold targets grid loads on first open
- **New Since Yesterday** strip — yellow badges on escalated/new prospects
- **Ask for a Referral** section — surfaces clients 30+ days old, 1+ service visit, not asked in 60d

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
- Manual mode: explicit green **➕ Add** / orange **✓ Added** toggle buttons per card
- **Double-fire fix**: per-id 400ms debounce on `addToRoute()` — ghost-click safe on iOS
- **showCard Route button**: inline `ontouchend`/`onclick` → `scAddRoute()` with 400ms debounce; larger tap target (8×14px padding)
- **Route state persists** across tab switches via `sessionStorage` (`pic_route`); loaded in `init()`
- **YOUR ROUTE bar** (`#manual-route-bar`): numbered stops with ✕, Maps ↗, Clear ✕
- **Route badge** on prospect cards ("📍 ON ROUTE")
- **openMaps()**: lat/lon waypoints when available; falls back to address-based

### Pipeline Tab
- `renderPipeline()` groups in_play / intro_set / quoted prospects by follow-up urgency

### Clients Tab
- MRR/ARR calculated from recurring customers (`kpi-mrr`, `kpi-arr`)
- Filter by account status: Recurring / One-Time / Intro / Quoted / Churned
- Service sub-tab: log service visits, track next service date, machine info
- **Referral badges**: "🤝 Ref by [Name]" on referred client; "💜 N referrals" + pill badges on referring client

### Referrals Tab (inside Service)
- Lists all clients with referral counts; dropdown to manually set `referred_by`

### Referral Capture System (new s5)
- **At won time**: Intro/Won tap → "🎉 Great close!" overlay before customer record is created
  - Search box filters active clients; tap row to select (green highlight)
  - "Save with referral" → sets `referred_by`, `referred_by_name`, pushes to referrer's `referrals[]`
  - "Skip" → creates customer with `referred_by: null`
  - Overlay: `createElement` + `addEventListener` after `appendChild` — fully iOS-safe
- **Home tab reminder**: `#referral-remind` section with ask script + "✓ Asked" / "View Client" buttons
  - `markReferralAsked()` sets `last_referral_ask`; client disappears for 60 days
- **Data model** (all optional, backward-compatible):
  - `referred_by` — prospect id of referring client
  - `referred_by_name` — display name
  - `referrals[]` — `[{id, name, date, status}]` entries on referring client
  - `last_referral_ask` — ISO date of last ask (for 60-day cooldown)

### ATP Status Report
- `scStatusReport(p)` opens ATP input overlay from showCard
- Scale: ≤0 = PENDING, ≤10 = PASS, 11–100 = MARGINAL, >100 = FAIL

### Date Handling
- `localISO(d)` helper returns `YYYY-MM-DD` in device local timezone
- All date storage uses `localISO()` — no UTC off-by-one after 8pm ET

## What's Broken / Watch List ⚠️

None known. If something appears broken, first try force-closing the PWA and reopening — the sw.js cache bust (`pic-YYYYMMDD`) requires a full app restart on iOS to take effect.

## What's Missing 🔲
- Referral email stats (Feature 4) need `customers.json` export from browser — wired but no data yet

## Recent Changes
- **2026-04-26 (s5):** CI fix — `pandas scikit-learn numpy` added to `rebuild.yml` pip install (build was failing)
- **2026-04-26 (s5):** Referral capture system — 4 features: won overlay, client badges, Home reminder, email stats
- **2026-04-26 (s5):** Route+ double-fire fix — per-id debounce on `addToRoute()`; sw.js bumped to force PWA refresh
- **2026-04-26 (s5):** `send_briefing.py` now reads fresh `prospecting_tool.html` instead of stale `index.html`
- **2026-04-26 (s4):** Route+ button — sessionStorage state, showCard toggle, YOUR ROUTE bar, route badge, lat/lon openMaps
- **2026-04-26 (s4):** New Since Yesterday — daily diff alert in Home tab, email, card badges
- **2026-04-25:** Architecture rewrite — 5-tab nav, Pipeline tab, Clients/Service sub-tabs, Settings gear button
- **2026-04-25:** ATP Status Report — 📋 Report button in showCard, print-ready HTML
- **2026-04-25:** Bug fixes — Route ZIP, manual +Add buttons, remove call scripts, daily cron, soft followup warning
- **2026-04-25 (s2):** `localISO()` — all date storage uses local timezone
- **2026-04-25 (s2):** sw.js daily date-stamp — eliminates stale PWA installs
- **2026-04-25 (s3):** Follow-up UX — `input[type=date]` pre-filled; "Save & Disposition Lead" button

## Next Session Priorities
1. Trigger manual CI rebuild (`workflow_dispatch`) to confirm build succeeds with new deps
2. Verify email sends with fresh data (check for "Loaded N prospects from prospecting_tool.html" in logs)
3. Test referral capture: tap Won → overlay appears → select client → badges show on Clients tab
4. Consider customers.json export button so email referral stats work

## iOS PWA Rules (never violate these)
- **Buttons in injected HTML:** use inline `ontouchend="event.stopPropagation();event.preventDefault();fn()"` + `onclick="event.stopPropagation();fn()"` — NOT `addEventListener` on innerHTML-injected elements
- **Delegation modals (showCard):** `addEventListener` on the backdrop element AFTER `document.createElement` + `appendChild` — never on innerHTML content
- **`event.stopPropagation()`** on nested buttons inside delegated containers to prevent parent handler from also firing
- **No** `addEventListener` on elements injected via `innerHTML` — attach AFTER `appendChild`
- **Dates:** always `localISO(d)` for storage, `parseLD(s)` for parsing — never `toISOString().slice(0,10)`
- **SW cache:** `build.py` auto-stamps `pic-YYYYMMDD`; after manual edits to sw.js, bump manually
- **iOS PWA cache refresh:** requires full app kill + reopen — sw update not immediate
- **Debounce:** `addToRoute(id)` has per-id 400ms debounce; `scAddRoute()` has 400ms global debounce — both needed to prevent ghost-click double-fire

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
