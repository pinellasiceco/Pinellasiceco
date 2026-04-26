# Pinellas Ice Co — App Status
*Last updated: 2026-04-26 (session 6) by Claude Code*

## Live App
- URL: https://pinellasiceco.github.io/Pinellasiceco
- Last deployed: 2026-04-26 (session 6 — Supabase sync, email fixed, recurring JS bug fixed)
- Build script: `build.py` (repo root) → outputs `prospecting_tool.html` → copied to `index.html` by CI
- `index.html` and `build.py` are fully in sync as of session 6

## What's Working ✅

### Deployment
- Daily cron: `0 11 * * *` (7am ET) in `rebuild.yml`
- Commit uses `--allow-empty` — always pushes even if no data changes
- `pages.yml` deploys to GitHub Pages on every push to main
- `send_briefing.py` sends daily briefing email via Resend — reads from `prospecting_tool.html` (fresh) first
- sw.js cache auto date-stamped by `build.py` on each rebuild (`pic-YYYYMMDD`) — no stale PWA
- CI pip deps: `pandas scikit-learn numpy requests openpyxl`

### Daily Briefing Email
- FROM: `briefing@pinellasiceco.com` (verified domain on Resend via GoDaddy auto-configure)
- TO: `BRIEFING_EMAIL` GitHub secret
- API key: `RESEND_API_KEY` GitHub secret (format `re_...`)
- Cloudflare CF-1010 fix: `User-Agent: PIC-Briefing/1.0` header on all Resend API requests
- All tables now include **Last Insp.** date column (e.g. "Feb 11")
- Referral stats section wired; shows zeros until customers.json export exists

### Navigation
- 5-tab layout: Home / Prospects / Pipeline / Route / Clients
- Gear ⚙️ button opens Settings overlay (Data tab)
- Sync dot (💾/☁/⚠) in header nav — tapping opens Settings
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
- **showCard Route button**: inline `ontouchend`/`onclick` → `scAddRoute()` with 400ms debounce
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

### Referral Capture System
- **At won time**: Intro/Won tap → "🎉 Great close!" overlay before customer record is created
  - Search box filters active clients; tap row to select (green highlight)
  - "Save with referral" → sets `referred_by`, `referred_by_name`, pushes to referrer's `referrals[]`
  - "Skip" → creates customer with `referred_by: null`
  - Overlay: `createElement` + `addEventListener` after `appendChild` — fully iOS-safe
- **Home tab reminder**: `#referral-remind` section with ask script + "✓ Asked" / "View Client" buttons
  - "What to say" button uses `toggleRefScript(this)` + `data-sid` — no inline quote escaping
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

### Supabase Cloud Sync (new s6)
- Settings → ☁️ Cloud Sync: URL + Anon Key fields, Test Connection button, Restore from Cloud
- Sync dot in header nav: 💾 = local only, ☁ = synced, ⚠ = sync error
- Credentials stored in `localStorage` only — never committed to repo
- Supabase project: `kbyqatbkqqhuasbjlcwe.supabase.co` (pinellasiceco workspace)
- Tables: `pic_log`, `pic_customers`, `pic_phones`, `pic_contacts`, `pic_settings`
- Row isolation via `device_id` (stored in `localStorage` as `pic_device_id`)
- All sync is fire-and-forget async — app stays fast, localStorage is source of truth
- **Hooked into:** `lSave()`, `phSave()`, `custSave()`, `contactsSave()`, `goalsSave()`, `saveSettings()`
- **Restore from Cloud**: pulls all tables, merges into localStorage, reloads app
- Credentials persist across sessions — no reconnect needed after first setup

## What's Broken / Watch List ⚠️

None known. If something appears broken, first try force-closing the PWA and reopening.

## What's Missing 🔲
- Referral email stats need `customers.json` export from browser — wired but no data yet (customers live in localStorage/Supabase, not the repo)
- Supabase SQL tables must be created manually once in Supabase SQL Editor (see setup instructions)

## Recent Changes
- **2026-04-26 (s6):** Supabase cloud sync — full implementation, credentials in Settings, sync dot in header
- **2026-04-26 (s6):** JS syntax fix (permanent) — `toggleRefScript(btn)` named function replaces inline onclick with unescapable single quotes; CI can no longer regenerate the broken version
- **2026-04-26 (s6):** Email FROM fixed — `briefing@pinellasiceco.com` (pinellasiceco.com verified in Resend via GoDaddy auto-configure)
- **2026-04-26 (s6):** Email CF-1010 fix — `User-Agent: PIC-Briefing/1.0` header bypasses Cloudflare browser integrity check on api.resend.com
- **2026-04-26 (s6):** Email tables — Last Insp. date column added to all prospect tables in briefing
- **2026-04-26 (s6):** Email diagnostics — strips whitespace from secrets, shows TO prefix + raw error body
- **2026-04-26 (s5):** CI fix — `pandas scikit-learn numpy` added to `rebuild.yml` pip install
- **2026-04-26 (s5):** Referral capture system — 4 features: won overlay, client badges, Home reminder, email stats
- **2026-04-26 (s5):** Route+ double-fire fix — per-id debounce on `addToRoute()`
- **2026-04-26 (s5):** `send_briefing.py` now reads fresh `prospecting_tool.html` instead of stale `index.html`
- **2026-04-26 (s4):** Route+ button — sessionStorage state, YOUR ROUTE bar, route badge, lat/lon openMaps
- **2026-04-26 (s4):** New Since Yesterday — daily diff alert in Home tab, email, card badges
- **2026-04-25:** Architecture rewrite — 5-tab nav, Pipeline tab, Clients/Service sub-tabs, Settings gear
- **2026-04-25:** ATP Status Report — 📋 Report button in showCard, print-ready HTML
- **2026-04-25 (s2):** `localISO()` — all date storage uses local timezone
- **2026-04-25 (s2):** sw.js daily date-stamp — eliminates stale PWA installs
- **2026-04-25 (s3):** Follow-up UX — `input[type=date]` pre-filled; "Save & Disposition Lead" button

## Next Session Priorities
1. Verify Supabase sync is writing rows (check Supabase dashboard → Table Editor → pic_log after logging a prospect outcome)
2. Test Restore from Cloud: clear localStorage in Dev Tools → tap Restore → confirm data comes back
3. Consider customers.json export button so referral email stats have data
4. Playbook / Tutorials tab — still has placeholder content (brief was written, not yet implemented)

## iOS PWA Rules (never violate these)
- **Buttons in injected HTML:** use inline `ontouchend="event.stopPropagation();event.preventDefault();fn()"` + `onclick="event.stopPropagation();fn()"` — NOT `addEventListener` on innerHTML-injected elements
- **Delegation modals (showCard):** `addEventListener` on the backdrop element AFTER `document.createElement` + `appendChild` — never on innerHTML content
- **`event.stopPropagation()`** on nested buttons inside delegated containers to prevent parent handler from also firing
- **No** `addEventListener` on elements injected via `innerHTML` — attach AFTER `appendChild`
- **Dates:** always `localISO(d)` for storage, `parseLD(s)` for parsing — never `toISOString().slice(0,10)`
- **SW cache:** `build.py` auto-stamps `pic-YYYYMMDD`; after manual edits to sw.js, bump manually
- **iOS PWA cache refresh:** requires full app kill + reopen — sw update not immediate
- **Debounce:** `addToRoute(id)` has per-id 400ms debounce; `scAddRoute()` has 400ms global debounce — both needed to prevent ghost-click double-fire
- **Quote escaping in build.py:** NEVER use `\'` inside the HTML_TEMPLATE triple-quoted string for JS string escaping — Python outputs `'` not `\'`. Use named functions + `data-*` attributes instead. See `toggleRefScript` as the pattern.

## Key Files
| File | Purpose |
|------|---------|
| `build.py` | **Edit this** — generates prospecting_tool.html; also stamps sw.js cache date |
| `index.html` | Deployed output — keep in sync with build.py; overwritten by CI daily |
| `sw.js` | Service worker — auto date-stamped by build.py; bump manually after direct edits |
| `.github/workflows/rebuild.yml` | Daily CI: download data → build → email → commit → push |
| `.github/workflows/pages.yml` | GitHub Pages deploy — triggers on every push to main |
| `send_briefing.py` | Daily briefing email via Resend (`briefing@pinellasiceco.com`) |
| `download_data.py` | Downloads FL DBPR inspection CSV files |
| `APP_STATUS.md` | This file — update at end of every session |
| `customers.json` | Seed customer data (used at build time) |
| `manifest.json` | PWA manifest |
