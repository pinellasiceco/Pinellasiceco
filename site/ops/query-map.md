# Target query map — sales-first expansion (lane-tagged)

**Status: built as specified; operator sign-off requested (hard gate for the
expansion's SEO thesis, not for deploy mechanics).**
Sources: GSC export 2026-07-03 (last 3 months) + Tampa Bay SERP lane analysis.

Policy exclusions (no pages built, by design): local head terms
("commercial ice machine tampa" — 30-year incumbents), national
transactional ("buy commercial ice machine online"), anything requiring
inventory/e-commerce pretense. Head-term rankings are a 2027 dividend of
winning the lanes below, not a target.

## Lane 1 — Decision Library (primary build)

| Query (head + variants) | Assigned page | Status |
|---|---|---|
| what size ice machine does a restaurant need / restaurant ice machine size | `/what-size-ice-machine-does-a-restaurant-need/` | NEW |
| what size ice machine for a bar / bar ice machine sizing | `/what-size-ice-machine-does-a-bar-need/` | NEW |
| hotel ice machine size / what size ice machine per room | `/what-size-ice-machine-does-a-hotel-need/` | NEW |
| ice machine for medical office / healthcare ice machine requirements | `/ice-machine-for-healthcare-facilities/` | NEW |
| office ice machine / breakroom ice machine size / school | `/ice-machine-for-office-or-school/` | NEW |
| commercial ice machine cost / how much does a commercial ice machine cost | `/commercial-ice-machine-cost/` | NEW |
| ice machine lease cost / how much to lease an ice machine | `/ice-machine-lease-cost/` | NEW |
| used commercial ice machine / used vs new ice machine | `/used-vs-new-commercial-ice-machine/` | NEW |
| hoshizaki vs manitowoc | `/hoshizaki-vs-manitowoc/` | NEW |
| nugget vs cube ice / ice types for business / flake ice uses | `/nugget-vs-cube-vs-flake-ice/` | NEW |
| replacing a commercial ice machine / ice machine trade in value / old ice machine disposal | `/replacing-a-commercial-ice-machine/` | NEW (trade-in wedge) |
| (method/trust page — no query target; linked from every form) | `/how-we-work/` | NEW |
| ice machine size calculator / ice machine cost calculator | `/ice-machine-cost-calculator/` (upgraded to library hub) | UPGRADE |
| "ice machine sales st petersburg fl" (GSC: 87 imp, pos 14.7) | `/st-petersburg/` sales section + `/commercial-ice-machine-sales/` | UPGRADE |
| "restaurant ice machine st petersburg fl" (GSC: 54 imp) | `/st-petersburg/` + restaurant sizing guide | UPGRADE |

## Lane 2 — Leasing neutrality

| Query | Assigned page | Status |
|---|---|---|
| lease vs buy ice machine / ice machine subscription worth it / all-inclusive ice machine cost | `/lease-vs-buy-vs-subscription-ice-machine/` | NEW |
| ice machine leasing tampa (existing) | `/ice-machine-leasing/` | EXISTS |
| easy ice alternative / pinellas ice co vs easy ice (Tier A, 51 imp, pos 6.2) | `/pinellas-ice-co-vs-easy-ice/` | EXISTS — ledger-locked |

## Lane 3 — Map-pack support (site-side only; battlefield is GBP)

| Query family | Site-side support | Status |
|---|---|---|
| ice machine supplier near me / ice machine company near me | NAP + LocalBusiness schema coherence, sales-first Service schema, GBP landing = `/commercial-ice-machine-sales/` | AUDIT |
| ice machine repair near me | `/ice-machine-repair/` landing coherence | EXISTS |
| GBP playbook (categories, services, products, reviews, posts) | `ops/gbp-playbook.md` (operator actions) | NEW DOC |

## Lane 4 — Long-tail local (sections, not doorway pages)

| Query | Assigned home | Status |
|---|---|---|
| hoshizaki dealer st petersburg / manitowoc dealer tampa | Brand sections on `/commercial-ice-machine-sales/` + city pages + `/brands/`. Standalone dealer pages ONLY on [OPERATOR: confirm dealer status] | SECTIONS |
| nugget ice machine tampa | `/nugget-vs-cube-vs-flake-ice/` (Tampa framing) + sales page section | NEW |
| ice machine replacement largo (GSC: 1 imp) | `/pinellas-county/` + repair→replace bridge | EXISTS |
| "ice machine repair in pinellas park" (GSC: 58 imp, pos 84) | `/ice-machine-repair/` + `/pinellas-county/` | EXISTS |

## Existing cleaning-lane queries (preserved, not expanded)

All cleaning queries from the GSC export remain served by the ported Tier A
pages + guides (ledger-locked). The expansion adds sales/lease weight around
them without touching them.

**Coverage check:** every Lane 1–4 query above has exactly one assigned
home; zero pages exist targeting excluded lanes.
