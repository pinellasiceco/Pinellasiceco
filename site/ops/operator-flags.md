# Operator flags — every [OPERATOR: confirm] item in one list

Ordered by priority. Nothing here blocks the *build*; items 1–3 block
*cutover*.

## Blocks cutover

1. **Tier A body paste** — copy the live HubSpot body of
   `/ice-machine-cleaning-clearwater-fl-pinellas-ice-co` into the marked
   region of `site/src/pages/ice-machine-cleaning-clearwater-fl-pinellas-ice-co.astro`
   (H1 too). The build ships an interim block that is NOT the ranking copy.
   Alternative: allowlist `pinellasiceco.com` (and ideally `web.archive.org`)
   in this environment's network policy and have the session port it.
2. **GSC export** (Performance → Pages + Queries, full history) — diff
   against `preservation-ledger.md`; classify any URL it reveals.
3. **HubSpot page list export** — same: any published page not in the ledger
   gets a 301 target before cutover.

## Trust strip + claims (shipped in conservative form — confirm or correct)

4. "Flat-rate pricing, no contracts" — shown sitewide (true per the cached
   cleaning page; confirm it holds for repair/sales/lease work too).
5. "Serving all of Tampa Bay" / Pinellas + Hillsborough + Pasco coverage —
   confirm you actually roll trucks to all three counties.
6. "Same-day" language — used ONLY on Clearwater cleaning surfaces
   ("same-day slots when available"). Confirm or tighten.
7. Response-time framing — forms say "usually the same business day."
   Confirm.
8. **NOT shipped** (need operator facts to exist): years in business,
   licenses/certifications, review counts/ratings, "X machines serviced"
   counters. Supply real numbers and they can be added to the trust strip.

## NAP / schema

9. LocalBusiness schema ships with locality **Clearwater, FL**, phone
   **(727) 855-6873**, email **service@pinellasiceco.com**, no street
   address (service-area business pattern). **Must match the Google Business
   Profile exactly** — confirm GBP shows the same phone/locality, add the
   street address to `BaseLayout.astro` if GBP displays one.
10. Business hours — omitted from schema (unknown). Add `openingHours` if
    you want them shown.

## Brand

11. Header uses an SVG cube + "Pinellas Ice Co" wordmark; the tagged logo
    ("Ice Machine Cleaning & Sanitizing") was avoided as cleaning-only
    framing. Replace `public/images/pinellas-ice-co-logo.webp` and the
    header SVG when a repair-inclusive logo exists — or approve as-is.

## Content

12. About page keeps biography thin on purpose (no invented history). Add
    founder name/story if wanted.
13. Privacy effective date says "July 2026" — confirm.
14. Calculator + leasing/sales price ranges are typical-market planning
    ranges — sanity-check them against your actual pricing so the site
    never quotes below what you'd charge.
