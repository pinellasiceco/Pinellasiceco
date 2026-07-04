# Operator flags — every [OPERATOR: confirm] item in one list

Ordered by priority. Nothing here blocks the *build*; items 1–3 block
*cutover*.

## Blocks cutover

1. ~~**Tier A body paste**~~ **DONE 2026-07-04** (operator paste, ported).
   Two follow-ups remain:
   - **1a. FAQ answers** — the live page's three FAQ accordions were
     collapsed in the paste. Open each on the live page and paste the
     answers into the marked comment in
     `site/src/pages/ice-machine-cleaning-clearwater-fl-pinellas-ice-co.astro`.
     Questions: "Is this service required for health inspections?" /
     "Do you work with high-volume commercial machines?" /
     "Does cleaning improve ice quality?"
   - **1b. "Florida cleaning frequency guide" URL** — the Tier A page links
     to it twice (also the "Cleaning Tips" nav item?). Supply its URL: it
     needs a redirect-map entry and, if it has impressions in GSC, a Tier B
     port of its own.
2. **GSC export** (Performance → Pages + Queries, full history) — diff
   against `preservation-ledger.md`; classify any URL it reveals.
3. **HubSpot page list export** — now known to include at least: Services,
   Pricing, FAQ, About Us, Contact Us, Service Area, Cleaning Tips, Terms.
   Slugs needed to finalize the 301 map (provisional targets in the ledger).

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
