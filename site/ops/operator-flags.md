# Operator flags — every [OPERATOR: confirm] item in one list

Ordered by priority. Nothing here blocks the *build*; items 1–3 block
*cutover*. Per operator direction 2026-07-04: decisions are TABLED for the
next session unless they block deploy — none of the open items below block
deploy; conservative defaults ship in the meantime.

## Sales-first expansion confirmations (tabled — new)

20. **The independence claim** (`Neutrality.astro`, on every library page +
    sales hub): "not tied to any manufacturer, any leasing program, or any
    national chain… don't carry inventory we need to move." Confirm true as
    worded — it constrains future dealer deals. Contradiction scan of the
    whole site: clean.
21. **Market price ranges** on /commercial-ice-machine-cost/,
    /ice-machine-lease-cost/, /lease-vs-buy-vs-subscription-ice-machine/,
    /used-vs-new-commercial-ice-machine/ and the calculator — Tampa Bay
    planning bands, mid-2026. Sanity-check against real quotes.
22. **Dealer status** — brand+geo is built as SECTIONS (sales hub, city
    pages, brands page). Standalone "Hoshizaki dealer St. Pete"-type pages
    only if real dealer relationships exist to make them honest.
23. **~45-minute response-drive line** (ServiceAreaBlock, on money pages +
    /how-we-work/) — ships as "about a 45-minute drive"; confirm.
24. **Phone area code** — RESOLVED: (727) confirmed by operator 2026-07-04.



## Blocks cutover

1. ~~**Tier A body paste**~~ **DONE 2026-07-04** (operator paste, ported —
   including FAQ answers with FAQPage schema). The "frequency guide" URL is
   now known from GSC (`…/how-often-should-a-commercial-ice-machine-be-cleaned-in-floridas-humid-climate`)
   and covered by the redirect map; the Tier A page's guide links point at
   `/ice-machine-cleaning/` until that guide is ported (PORT #12).
2. ~~**GSC export**~~ **DONE 2026-07-04** — full classification in the
   ledger MASTER TABLE (37 URLs, 30 clicks / 1,405 impressions). Every URL
   has a shipped disposition: KEEP-200, final 301, or PORT (interim 301).
3. **Redirect-map + port-list sign-off** — review the MASTER TABLE
   dispositions and the PORT priority list (#1–#12). The map is complete
   and shipped; cutover can proceed on interim 301s, but every page ported
   BEFORE cutover preserves more equity (301s leak a little; a 200 at the
   same slug leaks none).
   **Fastest way to port the 12 candidates: allowlist `pinellasiceco.com`
   in this environment's network policy and say the word — the content gets
   fetched and ported at the original slugs in one pass. Manual
   alternative: paste pages one at a time like the Clearwater page.**
4. **HubSpot page list export** — one residual use: catching any page with
   ZERO impressions (not in GSC) that still exists and gets handed out in
   emails/GBP. Low stakes now; the GSC export covered everything that ranks.

## Conversion-revamp confirmations (new)

16. **Response-time promise** — every form now carries: "No obligation. We
    call back fast — usually within the hour during business hours." The
    header says "Fast callbacks · same-day service when available."
    Confirm both or edit `RESPONSE_LINE` in `src/config.ts` (one place).
17. **GA4 measurement ID** — set `GA4_ID` in `src/config.ts` to enable
    call-click + lead-form-submit tracking (ships with analytics OFF and
    zero analytics JS until set).
18. **Google reviews** — the review component is built and shipped EMPTY
    (`src/components/ui/Reviews.astro`). Paste real GBP reviews into its
    array to light it up on home + all four money pages. Fabrication
    forbidden; it renders nothing until real reviews exist.
19. **"Licensed & Insured"** now leads the trust strip — sourced from your
    own live-site footer. Confirm it's current.

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
15. **Pricing inconsistency ported from the live site**: the pricing page
    (`/ice-machine-cleaning-pricing-in-pinellas-county-from-149`) says
    **$129/month** ("Clean Ice Plan", deep clean $395) while the city pages
    (Clearwater/St. Pete/Dunedin) say **$149/Month Service**. Both ported
    verbatim per preservation rules. Decide the real number and say the
    word — it's a one-line edit per page. (Also note the pricing page's
    slug says "from-149" while its title says "From $129" — that's the
    live site's own history; the slug must stay.)
