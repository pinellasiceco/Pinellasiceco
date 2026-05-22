#!/usr/bin/env python3
"""
One-time migration: rekey full_inspection_narratives.json and
full_scraper_progress.txt from License Number (e.g. "SEA6213532")
to numeric License ID (e.g. "6737473").

Safe to run multiple times — skips entries already under numeric keys.
Reads the License Number → License ID mapping from
data/pinellas_all_violations_to_scrape.csv.
"""

import csv
import json
import os

CACHE_FILE    = 'full_inspection_narratives.json'
PROGRESS_FILE = 'full_scraper_progress.txt'
VIOLATIONS_CSV = 'data/pinellas_all_violations_to_scrape.csv'


def build_lic_map():
    """Return {license_number: license_id} from the violations CSV."""
    if not os.path.exists(VIOLATIONS_CSV):
        print(f'  {VIOLATIONS_CSV} not found — skipping migration')
        return {}
    mapping = {}
    with open(VIOLATIONS_CSV, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lic_num = str(row.get('License Number', '')).strip()
            lic_id  = str(row.get('License ID', '')).strip()
            if lic_num and lic_id:
                mapping[lic_num] = lic_id
    return mapping


def migrate_cache(lic_map):
    if not os.path.exists(CACHE_FILE):
        print('  Cache file not found — nothing to migrate')
        return 0

    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    migrated = 0
    new_cache = {}
    for key, value in cache.items():
        # Already a numeric ID — keep as-is
        if key.isdigit():
            new_cache[key] = value
        else:
            numeric = lic_map.get(key)
            if numeric:
                new_cache[numeric] = value
                migrated += 1
            else:
                # No mapping found — keep original key
                new_cache[key] = value

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_cache, f)

    print(f'  Cache: {migrated} entries rekeyed to numeric License ID '
          f'({len(new_cache)} total entries)')
    return migrated


def migrate_progress(lic_map):
    if not os.path.exists(PROGRESS_FILE):
        return

    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]

    new_lines = []
    migrated = 0
    for line in lines:
        if line.isdigit():
            new_lines.append(line)
        else:
            numeric = lic_map.get(line)
            if numeric:
                new_lines.append(numeric)
                migrated += 1
            else:
                new_lines.append(line)

    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + ('\n' if new_lines else ''))

    print(f'  Progress: {migrated} entries rekeyed ({len(new_lines)} total)')


if __name__ == '__main__':
    print('Migrating scraper cache to numeric License ID keys...')
    lic_map = build_lic_map()
    if not lic_map:
        print('  No mapping available — exiting')
    else:
        print(f'  Loaded {len(lic_map)} License Number → License ID mappings')
        migrate_cache(lic_map)
        migrate_progress(lic_map)
        print('  Migration complete')
