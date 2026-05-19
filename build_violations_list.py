#!/usr/bin/env python3
"""
build_violations_list.py
Generates data/pinellas_all_violations_to_scrape.csv from the current
DBPR inspection extract — all Pinellas businesses with violations in
the last 180 days, one row per most-recent inspection per license.
Runs in CI before scrape_dbpr.py to feed the full violations scraper.
"""

import csv
import os
from datetime import date, datetime, timedelta

_DBPR_COLS = (
    ['District', 'County Number', 'County Name', 'License Type Code',
     'License Number', 'Business Name', 'Address', 'City', 'Zip',
     'Inspection Number', 'Visit Number', 'Inspection Class',
     'Inspection Type', 'Inspection Disposition', 'Inspection Date',
     'Num Critical', 'Num Noncritical', 'Num Total', 'Num High Priority',
     'Num Intermediate', 'Num Basic', 'PDA Status']
    + [f'V{i:02d}' for i in range(1, 59)]
    + ['License ID', 'Visit ID']
)

OUTPUT = 'data/pinellas_all_violations_to_scrape.csv'
CUTOFF_DAYS = 180


def main():
    input_file = 'data/3fdinspi_current.csv'
    if not os.path.exists(input_file):
        print(f'  {input_file} not found — skipping')
        return

    cutoff = date.today() - timedelta(days=CUTOFF_DAYS)

    by_license = {}

    try:
        with open(input_file, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = _DBPR_COLS  # CSV has no header row — first row is data
            print(f'  Reading {input_file}...')
            print(f'  Using column headers: {", ".join(header[:5])}...')

            pinellas_count = 0
            for row in reader:
                if len(row) < 10:
                    continue
                rec = dict(zip(header, row))

                county_name = rec.get('County Name', '').strip().lower()
                county_num = rec.get('County Number', '').strip()
                if county_name != 'pinellas' and county_num != '62':
                    continue
                pinellas_count += 1

                try:
                    num_total = int(rec.get('Num Total', '0').strip() or '0')
                except (ValueError, TypeError):
                    num_total = 0
                if num_total == 0:
                    continue

                insp_date_str = rec.get('Inspection Date', '').strip()
                try:
                    insp_date = date.fromisoformat(insp_date_str[:10])
                except (ValueError, TypeError):
                    try:
                        insp_date = datetime.strptime(insp_date_str.strip(), '%m/%d/%Y').date()
                    except (ValueError, TypeError):
                        continue
                if insp_date < cutoff:
                    continue

                vid = str(rec.get('Visit ID', '')).strip()
                lic = str(rec.get('License Number', '')).strip()
                if not vid or not lic:
                    continue

                existing = by_license.get(lic)
                if existing is None or insp_date > existing['_date']:
                    by_license[lic] = {
                        '_date': insp_date,
                        'Business Name': rec.get('Business Name', ''),
                        'Address': rec.get('Address', ''),
                        'City': rec.get('City', ''),
                        'Zip': rec.get('Zip', ''),
                        'License Number': lic,
                        'License ID': rec.get('License ID', ''),
                        'Visit ID': vid,
                        'Inspection Date': insp_date_str,
                        'Inspection Disposition': rec.get('Inspection Disposition', ''),
                        'Num Total': str(num_total),
                        'Num High Priority': rec.get('Num High Priority', '0'),
                    }
    except Exception as e:
        print(f'  build_violations_list error: {e}')
        return

    print(f'  Pinellas rows found: {pinellas_count}')
    print(f'  Unique licenses with violations: {len(by_license)}')

    if not by_license:
        print('  No Pinellas violation records found within cutoff')
        return

    os.makedirs('data', exist_ok=True)
    fieldnames = [
        'Business Name', 'Address', 'City', 'Zip',
        'License Number', 'License ID', 'Visit ID',
        'Inspection Date', 'Inspection Disposition',
        'Num Total', 'Num High Priority',
    ]

    rows = sorted(by_license.values(), key=lambda r: r['_date'], reverse=True)

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})

    print(f'  Built {len(rows)} Pinellas violation records → {OUTPUT}')


if __name__ == '__main__':
    main()
