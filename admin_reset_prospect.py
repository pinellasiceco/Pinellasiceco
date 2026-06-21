#!/usr/bin/env python3
"""
One-time admin: Part 1 + Part 2 of the Novu At Ponce reset task.

Part 1 — Reset prospect id 7847841 (Novu At Ponce, confirmed test data):
  - Print full BEFORE state from pic_customers + pic_log
  - DELETE both rows
  - Print AFTER confirmation
  - Guard: only this one prospect_id is touched

Part 2 — Read-only diagnostic of all churned records:
  - List every status='churned' record with full field state
  - No changes made

Requires: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_USER_ID env vars.
The service key bypasses RLS so it can read all rows for the configured user.
"""

import json
import os
import sys
import requests

RESET_PID = '7847841'

SUPA_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPA_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
USER_ID  = os.environ.get('SUPABASE_USER_ID', '').strip()

if not SUPA_URL or not SUPA_KEY or not USER_ID:
    print('ERROR: SUPABASE_URL, SUPABASE_SERVICE_KEY, and SUPABASE_USER_ID must all be set.')
    sys.exit(1)

BASE_HDR = {
    'apikey': SUPA_KEY,
    'Authorization': f'Bearer {SUPA_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}


def sb_get(table, filters='', select='prospect_id,data,updated_at'):
    url = f'{SUPA_URL}/rest/v1/{table}?device_id=eq.{USER_ID}&select={select}'
    if filters:
        url += '&' + filters
    r = requests.get(url, headers={**BASE_HDR, 'Range': '0-9999'}, timeout=30)
    r.raise_for_status()
    return r.json()


def sb_get_one(table, pid):
    url = f'{SUPA_URL}/rest/v1/{table}?device_id=eq.{USER_ID}&prospect_id=eq.{pid}'
    r = requests.get(url, headers=BASE_HDR, timeout=15)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def sb_delete(table, pid):
    url = f'{SUPA_URL}/rest/v1/{table}?device_id=eq.{USER_ID}&prospect_id=eq.{pid}'
    r = requests.delete(url, headers=BASE_HDR, timeout=15)
    r.raise_for_status()
    return r


def sep(title='', width=70):
    print()
    if title:
        bar = '=' * width
        print(bar)
        print(title)
        print(bar)
    else:
        print('-' * width)


# ─────────────────────────────────────────────────────────────
# PART 2: Churned records (read-only, no changes)
# ─────────────────────────────────────────────────────────────
sep('PART 2 — CHURNED RECORDS DIAGNOSTIC (READ-ONLY, ZERO CHANGES)')

all_customers = sb_get('pic_customers')
all_logs_raw  = sb_get('pic_log')

log_map = {}
for r in all_logs_raw:
    log_map[r['prospect_id']] = r.get('data', [])

churned_rows = [
    (r['prospect_id'], r.get('data') or {}, r.get('updated_at', '?'))
    for r in all_customers
    if (r.get('data') or {}).get('status') == 'churned'
]

if not churned_rows:
    print('\nNo churned records found in pic_customers.')
else:
    print(f'\nFound {len(churned_rows)} churned record(s):\n')
    for pid, data, updated_at in churned_rows:
        sep()
        print(f'prospect_id : {pid}')
        print(f'updated_at  : {updated_at}')
        print(f'data:')
        print(json.dumps(data, indent=2))
        plog = log_map.get(pid, [])
        if plog:
            print(f'\npic_log ({len(plog)} entries):')
            for i, e in enumerate(plog):
                print(f'  [{i}] {json.dumps(e)}')
        else:
            print('\npic_log: (no entries)')

print('\n[Part 2 complete — no changes made]')


# ─────────────────────────────────────────────────────────────
# PART 1: Reset Novu At Ponce (id 7847841)
# ─────────────────────────────────────────────────────────────
sep('PART 1 — NOVU AT PONCE (prospect_id=7847841) — BEFORE STATE')

cust_before = sb_get_one('pic_customers', RESET_PID)
log_before  = sb_get_one('pic_log', RESET_PID)

if cust_before:
    print(f'\npic_customers row:')
    print(f'  prospect_id : {cust_before.get("prospect_id")}')
    print(f'  device_id   : {cust_before.get("device_id","?")}')
    print(f'  updated_at  : {cust_before.get("updated_at","?")}')
    print(f'  data:')
    print(json.dumps(cust_before.get('data', {}), indent=4))
else:
    print(f'\n[No pic_customers row found for prospect_id={RESET_PID}]')

if log_before:
    log_entries = log_before.get('data', [])
    print(f'\npic_log row:')
    print(f'  prospect_id : {log_before.get("prospect_id")}')
    print(f'  updated_at  : {log_before.get("updated_at","?")}')
    print(f'  entries ({len(log_entries)}):')
    for i, e in enumerate(log_entries):
        print(f'    [{i}] {json.dumps(e)}')
else:
    print(f'\n[No pic_log row found for prospect_id={RESET_PID}]')


sep('PART 1 — PERFORMING RESET')

deleted_cust = False
deleted_log  = False

if cust_before:
    r = sb_delete('pic_customers', RESET_PID)
    if r.status_code in (200, 204):
        print(f'DELETE pic_customers [{RESET_PID}]: OK (HTTP {r.status_code})')
        deleted_cust = True
    else:
        print(f'DELETE pic_customers [{RESET_PID}]: FAILED (HTTP {r.status_code}): {r.text[:200]}')
        sys.exit(1)
else:
    print(f'DELETE pic_customers [{RESET_PID}]: skipped (no row existed)')

if log_before:
    r2 = sb_delete('pic_log', RESET_PID)
    if r2.status_code in (200, 204):
        print(f'DELETE pic_log [{RESET_PID}]: OK (HTTP {r2.status_code})')
        deleted_log = True
    else:
        print(f'DELETE pic_log [{RESET_PID}]: FAILED (HTTP {r2.status_code}): {r2.text[:200]}')
        sys.exit(1)
else:
    print(f'DELETE pic_log [{RESET_PID}]: skipped (no row existed)')


sep('PART 1 — AFTER STATE (VERIFICATION)')

cust_after = sb_get_one('pic_customers', RESET_PID)
log_after  = sb_get_one('pic_log', RESET_PID)

if cust_after is None:
    print(f'pic_customers[{RESET_PID}]: CONFIRMED ABSENT')
else:
    print(f'WARNING: pic_customers still has a row for {RESET_PID}!')
    print(json.dumps(cust_after, indent=2))

if log_after is None:
    print(f'pic_log[{RESET_PID}]:      CONFIRMED ABSENT')
else:
    print(f'WARNING: pic_log still has a row for {RESET_PID}!')
    print(json.dumps(log_after, indent=2))

print()
print('EFFECT ON AGGREGATIONS:')
print('  - status is no longer "customer_*" → excluded from MRR totals')
print('  - excluded from client count in all views (Customers, Pipeline, Reports)')
print('  - Sales-Reports new-client-in-period check: won_date field gone → not counted')
print()
print('NOTE: Browser localStorage may still cache this record until the user')
print('      clears local data (Settings → Clear local data) or re-opens the app')
print('      fresh. Supabase is the authoritative source and is now clean.')
print()
print('GUARD: Only prospect_id=7847841 was targeted. Zero other records were')
print('       read with intent to modify, and zero other deletes/updates ran.')
print()
print('DONE')
