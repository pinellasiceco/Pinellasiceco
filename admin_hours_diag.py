#!/usr/bin/env python3
"""
READ-ONLY diagnostic: sample the real `hours` field values from Supabase.

Two origins, cleanly separated:
  - pic_prospects.data.hours  -> OSM opening_hours (baked at build time)
  - pic_phones.data.hours     -> manual free-text entry (ph-hrs field)

Prints counts + verbatim samples of each so we can judge parseability.
Makes ZERO writes.
"""
import json, os, sys, requests, re

URL = os.environ['SUPABASE_URL'].strip()
KEY = os.environ['SUPABASE_SERVICE_KEY'].strip()
UID = os.environ['SUPABASE_USER_ID'].strip()
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}


def get(path):
    r = requests.get(f'{URL}/rest/v1/{path}', headers={**H, 'Range': '0-49999'}, timeout=60)
    r.raise_for_status()
    return r.json()


def line():
    print('-' * 72)


# ── OSM-sourced hours (pic_prospects) ────────────────────────────────
print('=' * 72)
print('OSM-SOURCED HOURS  (pic_prospects.data.hours)')
print('=' * 72)
prospects = get(f'pic_prospects?user_id=eq.{UID}&select=prospect_id,nm:data->>name,hours:data->>hours')
total_p = len(prospects)
osm = [(r['prospect_id'], r.get('nm') or '?', r['hours']) for r in prospects
       if r.get('hours') and str(r['hours']).strip()]
print(f'Total prospect rows: {total_p}')
print(f'With non-empty hours: {len(osm)} ({100*len(osm)/total_p:.1f}%)' if total_p else 'no rows')
print()
print('First 20 verbatim:')
for i, (pid, nm, h) in enumerate(osm[:20]):
    print(f'{i+1:2}. [{pid}] {nm[:30]:30} | {h!r}')

# crude format check against OSM opening_hours grammar (Mo-Fr 11:00-21:00 ...)
osm_re = re.compile(r'^[A-Za-z;,\s\d:+\-–—]+$')
day_tok = re.compile(r'\b(Mo|Tu|We|Th|Fr|Sa|Su|PH)\b')
time_tok = re.compile(r'\b([01]?\d|2[0-3]):[0-5]\d\b')
follows = sum(1 for _, _, h in osm if day_tok.search(h) and time_tok.search(h))
has_24 = sum(1 for _, _, h in osm if '24/7' in h)
print()
print(f'Look like real OSM syntax (has day token + HH:MM): {follows}/{len(osm)}')
print(f'Contain "24/7": {has_24}')

# ── Manual-entry hours (pic_phones) ──────────────────────────────────
print()
print('=' * 72)
print('MANUAL-ENTRY HOURS  (pic_phones.data.hours)')
print('=' * 72)
phones = get(f'pic_phones?device_id=eq.{UID}&select=prospect_id,data')
total_ph = len(phones)
man = [(r['prospect_id'], (r.get('data') or {}).get('hours', '')) for r in phones]
man_nonempty = [(pid, h) for pid, h in man if h and str(h).strip()]
print(f'Total pic_phones rows: {total_ph}')
print(f'With non-empty hours: {len(man_nonempty)}')
print()
print('ALL manual hours verbatim (up to 30):')
for i, (pid, h) in enumerate(man_nonempty[:30]):
    print(f'{i+1:2}. [{pid}] {h!r}')

print()
print('[diagnostic complete — zero writes]')
