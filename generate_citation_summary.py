#!/usr/bin/env python3
"""
Generate ice_citation_by_business.csv from pinellas_v22_narratives.csv.

Aggregates scraper output to one row per license_id with rich citation signals:
citation count, ice count, date range, repeat violations, mold/scoop flags,
and best observation excerpt.

Run automatically by rebuild CI before build.py, or manually:
    python generate_citation_summary.py
"""

import csv
import os
import re
from collections import defaultdict
from datetime import date, datetime

_INPUT_CANDIDATES = [
    'pinellas_v22_narratives.csv',        # repo root (scraper default)
    'data/pinellas_v22_narratives.csv',   # data folder fallback
]
INPUT_CSV  = next((p for p in _INPUT_CANDIDATES if os.path.exists(p)), _INPUT_CANDIDATES[0])
OUTPUT_CSV = 'ice_citation_by_business.csv'


def clean_observation(text, max_len=200):
    """Strip DBPR formatting markers and return a clean excerpt."""
    if not text or text == 'NO VIOLATIONS PARSED':
        return ''
    text = re.sub(r'\*\*[^*]+\*\*', '', str(text))  # remove **bold** markers
    text = re.sub(r'^\s*(Basic|Intermediate|High Priority)\s*[-–]\s*', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(' ', 1)[0]
    return cut + '…'


_ICE_KEYWORDS = re.compile(
    r'\b(ice\s+machine|ice\s+maker|ice\s+bin|ice\s+scoop|evaporator|condenser|'
    r'mold|slime|biofilm|pink|black|green|sanitize|sanitizer|soiled|dirty|'
    r'buildup|scale|residue|deposit|film|growth|discoloration)\b',
    re.IGNORECASE,
)


def extract_ice_snippet(text, max_chars=300):
    """Return the most relevant ice-related sentence(s) from an observation.

    Strips DBPR formatting, finds sentences containing ice keywords,
    returns those first; falls back to the full text if none match.
    """
    if not text or text == 'NO VIOLATIONS PARSED':
        return ''
    text = re.sub(r'\*\*[^*]+\*\*', '', str(text))
    text = re.sub(r'^\s*(Basic|Intermediate|High Priority)\s*[-–]\s*', '', text, flags=re.I | re.M)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text)
    ice_sents = [s for s in sentences if _ICE_KEYWORDS.search(s)]
    snippet = ' '.join(ice_sents) if ice_sents else text
    if len(snippet) <= max_chars:
        return snippet
    cut = snippet[:max_chars].rsplit(' ', 1)[0]
    return cut + '…'


def main():
    if not os.path.exists(INPUT_CSV):
        print(f'No {INPUT_CSV} found — nothing to aggregate')
        return

    today = date.today()

    # Keyed by license_id (numeric string) to match rec['id'] in build.py
    by_license = defaultdict(lambda: {
        'license_number':   '',
        'business_name':    '',
        'city':             '',
        'citation_count':   0,
        'ice_count':        0,
        'latest_date':      None,
        'earliest_date':    None,
        'best_observation': '',
        'codes':            set(),
        'visit_ids':        set(),
        'repeat_violations': 0,
        'warnings_issued':  0,
        'corrected_onsite': 0,
        'mold_black':       0,
        'mold_pink':        0,
        'scoop_issue':      0,
        'bin_soiled':       0,
    })

    total_rows = 0
    ice_rows   = 0

    with open(INPUT_CSV, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1

            lid = (row.get('license_id') or '').strip()
            if not lid:
                lid = (row.get('license_number') or '').strip()
            if not lid:
                continue

            b = by_license[lid]
            b['license_number'] = b['license_number'] or (row.get('license_number') or '').strip()
            b['business_name']  = b['business_name']  or (row.get('business_name') or '').strip()
            b['city']           = b['city']           or (row.get('city') or '').strip()
            b['citation_count'] += 1

            # Dates
            date_str = (row.get('inspection_date') or '')[:10]
            if date_str:
                try:
                    d = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if b['earliest_date'] is None or d < b['earliest_date']:
                        b['earliest_date'] = d
                    if b['latest_date'] is None or d > b['latest_date']:
                        b['latest_date'] = d
                except ValueError:
                    pass

            if row.get('ice_machine_mention') != 'YES':
                continue

            ice_rows += 1
            vid = (row.get('visit_id') or '').strip()
            if vid and vid not in b['visit_ids']:
                b['visit_ids'].add(vid)
                b['ice_count'] += 1

            obs = row.get('observation', '') or ''
            obs_lower = obs.lower()

            vc = (row.get('violation_code') or '').strip()
            if vc:
                b['codes'].add(vc)

            if 'repeat violation' in obs_lower:
                b['repeat_violations'] += 1
            if 'warning' in obs_lower:
                b['warnings_issued'] += 1
            if 'corrected on-site' in obs_lower or 'corrected on site' in obs_lower:
                b['corrected_onsite'] += 1
            if 'black' in obs_lower or 'green mold' in obs_lower:
                b['mold_black'] += 1
            if 'pink' in obs_lower:
                b['mold_pink'] += 1
            if 'scoop' in obs_lower:
                b['scoop_issue'] += 1
            if 'bin' in obs_lower:
                b['bin_soiled'] += 1

            obs_clean = extract_ice_snippet(obs)
            if len(obs_clean) > len(b['best_observation']):
                b['best_observation'] = obs_clean

    print(f'Processed {total_rows:,} rows, {ice_rows:,} ice citation rows')
    print(f'Unique licenses with any V22 record: {len(by_license):,}')

    fieldnames = [
        'license_id', 'license_number', 'business_name', 'city',
        'citation_count', 'ice_count',
        'latest_date', 'earliest_date', 'days_since_citation',
        'best_observation', 'codes',
        'repeat_violations', 'warnings_issued', 'corrected_onsite',
        'mold_black', 'mold_pink', 'scoop_issue', 'bin_soiled',
    ]

    ice_licenses = 0
    rows_written = 0

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for lid, b in sorted(by_license.items(),
                              key=lambda x: -(x[1]['ice_count'])):
            last = b['latest_date']
            days_since = (today - last).days if last else 9999

            writer.writerow({
                'license_id':        lid,
                'license_number':    b['license_number'],
                'business_name':     b['business_name'],
                'city':              b['city'],
                'citation_count':    b['citation_count'],
                'ice_count':         b['ice_count'],
                'latest_date':       last.isoformat() if last else '',
                'earliest_date':     b['earliest_date'].isoformat() if b['earliest_date'] else '',
                'days_since_citation': days_since,
                'best_observation':  b['best_observation'],
                'codes':             '|'.join(sorted(b['codes'])),
                'repeat_violations': b['repeat_violations'],
                'warnings_issued':   b['warnings_issued'],
                'corrected_onsite':  b['corrected_onsite'],
                'mold_black':        b['mold_black'],
                'mold_pink':         b['mold_pink'],
                'scoop_issue':       b['scoop_issue'],
                'bin_soiled':        b['bin_soiled'],
            })
            rows_written += 1
            if b['ice_count'] > 0:
                ice_licenses += 1

    print(f'Written {rows_written} rows to {OUTPUT_CSV}')
    print(f'  With ice citations: {ice_licenses}')
    print(f'  No ice citations:   {rows_written - ice_licenses}')


if __name__ == '__main__':
    main()
