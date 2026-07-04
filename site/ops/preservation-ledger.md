# Preservation Ledger — pinellasiceco.com migration (HubSpot CMS → Astro/Netlify)

**Status: PROVISIONAL — operator sign-off required before DNS cutover (the hard gate).**
Date compiled: 2026-07-03

## How this ledger was built (and what it could not see)

The build environment's network policy blocks direct access to `pinellasiceco.com`
(and to archive.org), and no GSC export was found in the session workspace or the
operator's Google Drive. This ledger is therefore built from:

1. **Google's live index** (queried via web search) — confirmed indexed URLs, their
   title tags, and content substance as Google has cached it.
2. **Internal references** in the `pinellasiceco/Pinellasiceco` repo (partner pages,
   Stripe checkout, briefing emails) — URLs the business actively hands out.
3. **Domain registration data** — `pinellasiceco.com` appears in a daily-registration
   listing dated **2026-03-30**: the domain is ~3 months old. The realistic ranking
   surface is small and concentrated, which the index evidence confirms.

**GAPS the operator must close before DNS cutover (sign-off checklist at bottom):**
- Export **GSC Performance → Pages + Queries** (full 3-month history) and diff against
  this ledger. Any URL with impressions not listed here gets classified before cutover.
- Export the **full page list from HubSpot CMS** (Marketing → Website Pages +
  Landing Pages + Blog) — the index shows one page, but unindexed/low-traffic pages
  may still exist and need 301s.
- Confirm the exact title/meta/H1/body of the Tier A page below against the live
  HubSpot page (this ledger carries the substance Google has cached, which is what
  ranks, but a visual diff against the live page is the final check).

---

## URL inventory + classification

### TIER A — has confirmed index presence. Path, title, H1, substance preserved.

| # | URL | Evidence | Treatment |
|---|-----|----------|-----------|
| A1 | `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co` | **Confirmed indexed & ranking** (appears for "ice machine cleaning" queries; the site's only indexed page). Title as indexed: **"Ice Machine Cleaning Clearwater, FL \| Pinellas Ice Co"** | Path preserved **identically** (same slug, no redirect). Title verbatim. H1 preserved (see A1 content record). Body substance ported; may be extended below the ranking copy. |
| A2 | `/` (homepage) | Root domain indexed (site: query resolves); content not retrievable from this environment | New homepage at same URL. Meta description built from the same service language Google associates with the site. **Operator: paste current homepage title/meta/H1 into the sign-off checklist for the verbatim-preservation decision.** |

#### A1 content record (substance as cached by Google — this is the ranking copy)

- Same-day ice machine cleaning in Clearwater, FL — flat-rate pricing, no contracts,
  fast service for restaurants and bars.
- Service area: Clearwater and nearby — Dunedin, Palm Harbor, Largo, and surrounding
  Pinellas County.
- **$99** initial clean and test; most Clearwater clients switch to **monthly service**
  after their first visit.
- Ongoing offering: cleaning, filtration, **ATP testing**, certification.
- Verification language: measured sanitation levels **before and after** cleaning;
  verification you can show inspectors or ownership; clear records for compliance and
  internal accountability.
- Routine cleaning helps meet sanitation standards and reduces the risk of inspection
  issues; machines in busy restaurant/hospitality environments.

Head queries this page serves (inferred from index behavior; GSC export will confirm):
"ice machine cleaning clearwater", "ice machine cleaning clearwater fl",
"ice machine cleaning near me" (Clearwater-local), "commercial ice machine cleaning
pinellas".

#### Tier A live-content extraction status (per-page)

| Page | Extracted from live? | Word count (fetched vs. expected) | Notes |
|------|---------------------|-----------------------------------|-------|
| A1 `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co` | **YES — operator paste, 2026-07-04** | ~430 words fetched / 400–800 expected ✓ | Body supplied by operator (live-site copy/paste; direct fetch remains blocked by egress policy). Ported verbatim substance + heading structure into the page. Booking CTAs reconciled to callback/form (conversion surface, not ranking copy). **Two gaps remain:** (1) the three FAQ accordion ANSWERS were collapsed in the paste — questions preserved in a marked comment, answers must be pasted, never invented; (2) the page links twice to a "Florida cleaning frequency guide" — URL unknown, links point at `/ice-machine-cleaning/` until the slug is supplied. |
| A2 `/` | **NO — OPERATOR FLAG** | 0 fetched | Blocked host. New homepage is built new (operator to record live title/meta/H1 in checklist and confirm the rewrite decision, since homepage content was not retrievable to preserve). |

#### Live-site structure discovered via the A1 paste (2026-07-04)

The live page's navigation reveals pages not visible in the search index —
slugs unknown until the HubSpot export. Provisional closest-intent 301
targets (finalize with real slugs before cutover):

| Live page (nav label) | Provisional 301 target | Note |
|----------------------|------------------------|------|
| Services | `/ice-machine-cleaning/` | live site is cleaning-centric |
| Pricing | `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co/` | the $99/$149 pricing copy lives there now |
| FAQ | `/ice-machine-cleaning/` | FAQ block on the new page |
| About Us | `/about/` | |
| Contact Us | `/contact/` | |
| Service Area | `/pinellas-county/` | |
| Cleaning Tips / "Florida cleaning frequency guide" | **evaluate before redirecting** | linked twice from the Tier A page — may have its own queries; port as Tier B if the GSC export shows impressions |
| Terms & Conditions | `/terms/` | |

### TIER A-ADJACENT — real URLs the business hands out (not ranking assets, but must not break)

| # | URL | Evidence | Treatment |
|---|-----|----------|-----------|
| B1 | `/ice-machine-data` | Full static page exists in repo (`docs/data/index.html`) with self-canonical to this URL. Title: "Pinellas County Ice Machine Compliance Data \| Pinellas Ice Co". Linkable research asset (7 years of DBPR inspection data). | **Ported verbatim** as a static page at the same path. Zero-risk, preserves any backlinks. |
| B2 | `/terms` | Referenced by live Stripe checkout (`stripe-checkout/index.ts`) and pricing page | New `/terms` page at same path (adapted from GRC legal pages, lighter). |
| B3 | `/explore` | Handed out in partner one-pagers (Pelican, Coastline) as the compliance explorer | 301 → `/ice-machine-data` (closest intent: same compliance-data content family). |

### TIER B — everything else

No other URLs surfaced in the index or in business materials. Unknown HubSpot pages
(if the HubSpot export reveals any) get classified at sign-off: anything with
impressions → closest-intent 301; dead pages → 301 to closest intent, homepage last
resort.

### PARAMETER VARIANTS

| Pattern | Treatment |
|---------|-----------|
| `?hsLang=en` (HubSpot language param) | Same path serves on Netlify (params ignored for routing); every page carries a **self-referencing canonical with params stripped** — consolidation is automatic and expected net-positive. |
| `?hs_amp=true` / AMP variants | Same: canonical consolidates. No AMP pages on the new site. |
| HubSpot system paths (`/hs-fs/*`, `/hubfs/*`, `/_hcms/*`, `/cs/c/*`) | 301 → `/` (asset URLs die with HubSpot; no ranking value; redirect prevents 404 noise in GSC). |

---

## Redirect map (as shipped in `netlify.toml`)

| From | To | Type |
|------|----|------|
| `/explore` | `/ice-machine-data/` | 301 |
| `/hs-fs/*`, `/hubfs/*`, `/_hcms/*`, `/cs/*` | `/` | 301 |
| `http://` + apex/www variants | `https://www.pinellasiceco.com` | 301 (Netlify domain settings, single hop) |

**Deliberately NOT redirected:** `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co`
(Tier A — same path returns 200 on the new site), `/`, `/terms`, `/ice-machine-data`
(same paths, 200).

No redirect chains: every entry lands directly on a 200. New-site pages are all
new paths (`/ice-machine-repair` etc.) — they collide with nothing.

---

## Positioning conflicts flagged at the gate (per site-purpose hierarchy)

The new site leads with REPAIR, then SALES/LEASING; cleaning is a supporting service.
Conflicts between preserved assets and that positioning, for operator decision:

1. **Logo tagline**: the repo's primary logo (`pic_logo.png`) carries a banner reading
   "Ice Machine Cleaning & Sanitizing" — cleaning-only framing. The build uses the
   **untagged stacked variant** (same brand, no tagline) in header/OG. Operator:
   confirm, or supply a logo with repair/sales-inclusive framing.
2. **Homepage (A2)**: live homepage content could not be retrieved; if the GSC export
   shows homepage queries that are cleaning-specific, the repair-first homepage may
   shift those. Review at sign-off with the export in hand.
3. **Only ranking page is a cleaning page (A1)**: preserved intact at its URL with its
   title verbatim — no conflict; noted so the repair-first nav order (which links to
   it from the Cleaning nav item and service pages, not the hero) is a recognized,
   deliberate choice.

## Operator sign-off checklist (hard gate — complete before DNS cutover)

- [ ] GSC Performance export (Pages + Queries, full history) pulled and diffed against
      this ledger — no impression-bearing URL unaccounted for.
- [ ] HubSpot full page list exported — every published page classified above or added.
- [ ] Tier A page A1: live title/meta/H1/body visually diffed against the built page.
- [ ] Homepage title/meta/H1 from HubSpot recorded and either preserved verbatim or
      explicitly approved as rewritten.
- [ ] Redirect map above approved.
- [ ] MX/email DNS records inventoried (see cutover doc) — cutover must not break email.
