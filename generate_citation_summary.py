#!/usr/bin/env python3
"""
Generate ice_citation_by_business.csv from pinellas_v22_narratives.csv.

Reads the scraper output (one row per violation per inspection visit) and
aggregates to one row per license number — total citation count, ice-machine
citation count, date range, best observation excerpt, and violation codes.

Run automatically by the rebuild CI before build.py, or manually:
    python generate_citation_summary.py
"""

import csv
import os
import re
from collections import defaultdict

_INPUT_CANDIDATES = [
    'pinellas_v22_narratives.csv',
    'data/pinellas_v22_narratives.csv',
]
INPUT_CSV  = next((p for p in _INPUT_CANDIDATES if os.path.exists(p)), _INPUT_CANDIDATES[0])
OUTPUT_CSV = 'ice_citation_by_business.csv'


def clean_observation(text, max_len=200):
    """Return a clean excerpt of an observation string."""
    if not text or text == 'NO VIOLATIONS PARSED':
        return ''
    text = re.sub(r'\s+', ' ', str(text)).strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(' ', 1)[0]
    return cut + '…'


def main():
    if not os.path.exists(INPUT_CSV):
        print(f'No {INPUT_CSV} found — nothing to aggregate')
        return

    # Group rows by license_number
    by_license = defaultdict(list)
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lic = (row.get('license_number') or '').strip()
            if not lic:
                continue
            by_license[lic].append(row)

    if not by_license:
        print('No license numbers found in scraper output')
        return

    print(f'Aggregating {sum(len(v) for v in by_license.values())} rows across {len(by_license)} licenses...')

    fieldnames = [
        'license_number', 'business_name', 'city',
        'citation_count', 'ice_count',
        'latest_date', 'earliest_date',
        'best_observation', 'codes',
    ]

    rows_written = 0
    ice_licenses = 0

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for lic, rows in sorted(by_license.items()):
            # Collect all ice-positive rows
            ice_rows = [r for r in rows if r.get('ice_machine_mention') == 'YES']

            # Best observation = longest ice observation, falling back to any observation
            obs_candidates = [r.get('observation', '') for r in ice_rows if r.get('observation')]
            if not obs_candidates:
                obs_candidates = [r.get('observation', '') for r in rows if r.get('observation') and r.get('observation') != 'NO VIOLATIONS PARSED']
            best_obs = clean_observation(max(obs_candidates, key=len, default=''))

            # Dates
            dates = sorted(r.get('inspection_date', '') for r in rows if r.get('inspection_date'))

            # Violation codes from ice rows
            codes = sorted({r.get('violation_code', '') for r in ice_rows if r.get('violation_code')})

            # Business info from first row
            first = rows[0]

            writer.writerow({
                'license_number':  lic,
                'business_name':   first.get('business_name', ''),
                'city':            first.get('city', ''),
                'citation_count':  len(rows),
                'ice_count':       len(ice_rows),
                'latest_date':     dates[-1] if dates else '',
                'earliest_date':   dates[0] if dates else '',
                'best_observation': best_obs,
                'codes':           '|'.join(codes),
            })
            rows_written += 1
            if ice_rows:
                ice_licenses += 1

    print(f'Written {rows_written} license rows to {OUTPUT_CSV}')
    print(f'  Licenses with ice citations: {ice_licenses}')
    print(f'  Licenses with no ice citations: {rows_written - ice_licenses}')


if __name__ == '__main__':
    main()
