# pinellasiceco.com migration — final output packet

Everything the operator needs to take this build live and watch it settle.
Companion docs: `preservation-ledger.md` (the constitution), `operator-flags.md`
(every [OPERATOR: confirm] item in one list), `../ops/prompts/triage.md`
(triage voice — tune freely).

---

## 1. Preservation ledger (as shipped)

See `site/ops/preservation-ledger.md`. Summary:

- **Tier A confirmed:** `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co`
  — slug preserved identically, title verbatim
  ("Ice Machine Cleaning Clearwater, FL | Pinellas Ice Co"), **body is an
  operator-fill region** (live HubSpot body was not fetchable from the build
  environment; per migration rules it was NOT regenerated). **This is the #1
  pre-cutover action.**
- **Tier A presumed:** `/` — rebuilt repair-first per the site-purpose
  hierarchy; record the old homepage title/meta/H1 at sign-off.
- **Ported verbatim:** `/ice-machine-data` (from repo `docs/data/index.html`;
  one embedded HubSpot meetings link swapped for `tel:`).
- **Gaps:** GSC export + HubSpot full page list — both operator-supplied,
  both required before DNS cutover.

## 2. Redirect map (old → new), as shipped in `netlify.toml`

| From | To | Status |
|------|----|--------|
| `/explore` | `/ice-machine-data/` | 301 |
| `/hs-fs/*`, `/hubfs/*`, `/_hcms/*`, `/cs/*` | `/` | 301 |
| slash-less URLs (e.g. `/tampa`) | slash form (`/tampa/`) | 301 (Netlify pretty-URLs, single hop) |
| `?hsLang=`, `?hs_amp=` variants | same path serves; self-canonical strips params | n/a (consolidation) |

Tier A + known URLs return **200 at their original paths** (no redirect):
`/`, `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co/`, `/terms/`,
`/ice-machine-data/`.

Any URL the GSC/HubSpot exports reveal gets added to this table before
cutover — closest intent, single hop, homepage only as last resort.

## 3. Page inventory + internal link map

18 Astro pages + 1 ported static page. Nav order encodes the purpose
hierarchy: **Repair → Sales → Leasing → Cleaning → Brands → Pricing → Get Help**.

| Page | Receives links from | Pushes links to |
|------|--------------------|-----------------|
| `/` home | every page (logo) | repair (hero CTA + card), sales, leasing, cleaning, all 4 area pages, troubleshooter, calculator, brands (FAQ) |
| `/ice-machine-repair/` **(money #1)** | nav, home hero, home card, all area pages, cleaning, brands FAQ, troubleshooter, Tier A page, footer | cleaning, brands, calculator, troubleshooter, 4 area pages |
| `/commercial-ice-machine-sales/` **(money #2)** | nav, home, all area pages, repair (replace math), leasing, troubleshooter, footer | leasing, calculator, brands, area pages |
| `/ice-machine-leasing/` **(money #2)** | nav, home, sales, repair, all area pages, footer | sales, cleaning, calculator, area pages |
| `/ice-machine-cleaning/` | nav, home, repair, leasing, area pages, Tier A page, footer | **Tier A Clearwater page**, ice-machine-data, repair, area pages |
| `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co/` **(Tier A)** | cleaning page, clearwater page, footer (never orphaned) | repair, cleaning, ice-machine-data, clearwater |
| `/brands/` | nav, home FAQ, repair, sales, footer | repair, cleaning, sales, leasing |
| `/tampa/` `/st-petersburg/` `/clearwater/` `/pinellas-county/` | home, footer, each other, money pages | **all three money pages** + cleaning (each) |
| `/ice-machine-cost-calculator/` | nav ("Pricing"), home, repair, sales, leasing, troubleshooter, footer | sales, leasing, repair |
| `/ice-machine-troubleshooting/` | nav ("Get Help"), home, repair, contact, thank-you, footer | repair, cleaning, calculator |
| `/ice-machine-data/` (static) | cleaning, pinellas-county, about, Tier A page, footer | (self-contained study) |
| `/about/` `/contact/` `/privacy/` `/terms/` `/thank-you/` | footer (+ forms → thank-you) | services, troubleshooter |

Every relevant new page links INTO the Tier A page; money pages receive
links from home, nav, and every service-area page. No orphans.

## 4. Triage prompt (for voice-tuning)

`site/ops/prompts/triage.md`. Segments: repair-urgent / repair-routine /
sales / lease / cleaning. Tiers: HOT / WARM / LOW / JUNK. Subject line
format: "🧊🔥 HOT — repair-urgent, restaurant, Clearwater". Edit the prompt
file directly; no code changes needed. Kill switch: `OPS_TRIAGE_ENABLED=false`.

## 5. DNS pre-flight findings (inspected 2026-07-03) + cutover steps

**Current records (via DNS resolution from the build environment):**

| Record | Value | Meaning |
|--------|-------|---------|
| NS | ns27/ns28.domaincontrol.com | DNS is managed at **GoDaddy** |
| MX | `pinellasiceco-com.mail.protection.outlook.com` (pri 0) | **Email is Microsoft 365 — MUST NOT be touched** |
| TXT | `v=spf1 include:secureserver.net -all` | SPF (GoDaddy-managed M365) — do not touch |
| TXT | `google-site-verification=ma5KCk…` | GSC domain verification — keep (re-verification safety) |
| TXT | `NETORG20557238.onmicrosoft.com` | M365 tenant verification — keep |
| www CNAME | `pinellasiceco-com.group45.sites.hubspot.net` | **HubSpot — this is what changes** |
| apex A | `34.102.136.180` | HubSpot apex redirect — this changes too |

**Cutover procedure (operator executes; ~15 min + propagation):**

1. **Netlify setup (before touching DNS):**
   - New site from `pinellasiceco/Pinellasiceco` repo, branch `main` (after
     merge) — build settings come from root `netlify.toml` (base `site`,
     publish `dist`, functions `site/netlify/functions`).
   - Set env vars per `site/.env.example`: `ANTHROPIC_API_KEY`,
     `RESEND_API_KEY`, `OPERATOR_EMAIL=john@pinellasiceco.com`.
   - Deploy; confirm the Netlify subdomain serves the site and Forms
     detection shows **lead-capture** under Site → Forms.
   - Send one test submission on the Netlify subdomain → expect operator
     email + lead in Blobs (`pic-leads`).
   - Add custom domain `www.pinellasiceco.com` (+ `pinellasiceco.com`
     redirect-to-www) in Netlify → Domain settings. Netlify shows the exact
     target values for the next step.
2. **At GoDaddy DNS (change ONLY these two records):**
   - `www` CNAME: `pinellasiceco-com.group45.sites.hubspot.net` → Netlify's
     target (e.g. `<site-name>.netlify.app`).
   - Apex `@` A `34.102.136.180` → Netlify's apex load balancer
     `75.2.60.5` (use the value Netlify's domain panel shows).
   - **Touch nothing else. No MX, no TXT, no NS changes.** Email keeps
     working because mail routing never involved HubSpot.
3. Let Netlify provision the TLS cert (automatic, minutes after DNS
   propagates). Verify `https://www.pinellasiceco.com/` serves the new site
   and `https://pinellasiceco.com` 301s to www.

## 6. Post-cutover verification (same day)

- [ ] `curl -sI https://www.pinellasiceco.com/ice-machine-cleaning-clearwater-fl-pinellas-ice-co/` → **200** (Tier A intact)
- [ ] GSC top-10 URLs (from the export): each returns 200, or 301-once-to-200 — no chains, no 302s
- [ ] `/explore` → 301 → `/ice-machine-data/` (single hop)
- [ ] `?hsLang=en` variant of any page → serves; canonical shows clean URL
- [ ] Form end-to-end on the live domain: submit → operator email arrives with tiered subject → lead in Blobs
- [ ] Schema: run home + repair + Tier A through Google Rich Results test (LocalBusiness, Service, FAQPage)
- [ ] Mobile spot-check + Lighthouse on `/`, `/ice-machine-repair/` (expect 95+ mobile: no JS, ~40KB page + fonts)

## 7. Post-cutover SEO protocol (within 1 hour of DNS)

1. GSC: property already verified via the domain TXT record (kept) — confirm
   access; add a URL-prefix property for `https://www.pinellasiceco.com/` if
   not present.
2. Submit sitemap: `https://www.pinellasiceco.com/sitemap-index.xml`.
3. Request indexing (URL Inspection) on: Tier A Clearwater URL, `/`,
   `/ice-machine-repair/`, `/commercial-ice-machine-sales/`,
   `/ice-machine-leasing/`.
4. **Watch (daily, first week only):** parameter-variant impressions should
   consolidate onto canonicals (position improvement expected); Tier A
   position holds within ±3; new pages enter within 2–3 weeks.
   **Escalation trigger:** any Tier A page losing >5 positions for >7 days →
   diff its redirect/title/content against the preservation ledger.

## 8. HubSpot dependencies discovered (attend to BEFORE the old site dies)

1. **HubSpot meetings link** (`meetings-na2.hubspot.com/stripe/ice-machine-on-site?uuid=9a40…`)
   was embedded in the ice-machine-data page — replaced with `tel:` in the
   ported copy, but the same link may live in emails, GBP, or printed
   material. Anywhere it survives, it dies when the HubSpot account closes.
2. **HubSpot forms/CRM**: any leads currently in HubSpot CRM should be
   exported before account closure (site forms now log to Netlify Blobs).
3. **HubSpot-hosted assets** (`/hs-fs/`, `/hubfs/` image URLs): if any are
   hotlinked from GBP posts, directories, or emails, they 404 after closure
   — the redirect map catches on-site paths only.
4. **The live page content itself** — the Tier A body must be copied out of
   HubSpot before the account closes (see #1 priority action).
5. `stripe-checkout` Supabase function references `pinellasiceco.com/terms`
   — new `/terms/` page preserves that path. ✅ No action.

## 9. Brand assets — path taken + gaps

**Path taken: repo assets** (option 1 — no live-site pull was possible; the
network policy blocks the domain).

- Logo: stacked variant (`5B2CEC02….png` → `images/pinellas-ice-co-logo.webp`,
  24KB). The horizontal `pic_logo.png` carries the tagline **"Ice Machine
  Cleaning & Sanitizing"** — cleaning-only framing that conflicts with
  repair-first positioning, so it was not used. **[OPERATOR: replace or
  approve]** — see flag #1 in `operator-flags.md`.
- Header/favicon: hand-coded SVG ice cube matching the brand mark (crisp at
  16px, ~500 bytes); `apple-touch-icon.png` from the cube mark.
- OG default: 1200×630 composed from the stacked logo.
- Photos: real field photos from the repo (before/after service composites,
  component shots) — **no stock imagery was used** (stock sites also blocked
  by network policy; net win: authentic proof-of-work photos + certification
  shield instead). All WebP, ≤47KB each, lazy-loaded below fold,
  keyword-relevant filenames + truthful alt text.

## 10. Deferred option (not a to-do)

The GRC booking system (calendar widget + Google Calendar integration) is
portable to this site later if callback-conversion proves insufficient. It
would need its own Google OAuth credentials against a pinellasiceco
calendar, a `/book` page, and booking-form triage wiring. Nothing in this
build blocks it; nothing in this build depends on it.

## 11. Conversion instrumentation (added in the conversion revamp)

Set `GA4_ID` in `src/config.ts` (flag #17) and every page reports:

| Event | Fires when | Parameters |
|-------|-----------|------------|
| `call_click` | any tel: link is tapped/clicked | `page_path`, `link_location` (sticky-bar / header / hero / form-card / footer / body) |
| `lead_form_submit` | any lead-capture form submits | `page_path`, `segment` (repair/sales/lease/cleaning/general), `urgency` when present |

Together these separate phone demand from form demand per page — the
phone-side half of the sensor. With `GA4_ID` empty the site ships zero
analytics JS. The sticky mobile call bar, header phone, and hero CTAs are
all tagged with `data-loc` so GA4 shows which surface converts.

## 12. Operator watch instructions

GSC daily for the first week (the one exception to the weekly-cadence rule),
then weekly. Leads arrive as tiered emails to `OPERATOR_EMAIL`
(john@pinellasiceco.com); the durable log lives in Netlify Blobs store
`pic-leads` (site-scoped, fully separate from any other business's data).
JUNK-tier submissions log silently — check the store occasionally for
misclassified leads while the prompt is young.
