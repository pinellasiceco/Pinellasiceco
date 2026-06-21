#!/usr/bin/env python3
"""READ-ONLY: count bars in pic_prospects via PostgREST count=exact (no row pull)."""
import os, requests

URL = os.environ['SUPABASE_URL'].strip()
KEY = os.environ['SUPABASE_SERVICE_KEY'].strip()
UID = os.environ['SUPABASE_USER_ID'].strip()
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}',
     'Prefer': 'count=exact', 'Range': '0-0'}


def count(q):
    r = requests.get(f'{URL}/rest/v1/pic_prospects?user_id=eq.{UID}&{q}', headers=H, timeout=30)
    r.raise_for_status()
    cr = r.headers.get('Content-Range', '')   # e.g. "0-0/9612"
    return cr.split('/')[-1]


print('total prospects        :', count('select=prospect_id'))
print('venue_type = bar       :', count('select=prospect_id&data->>venue_type=eq.bar'))
print('is_bar = true          :', count('select=prospect_id&data->>is_bar=eq.true'))
print('venue_type = restaurant:', count('select=prospect_id&data->>venue_type=eq.restaurant'))
print('venue_type = golf      :', count('select=prospect_id&data->>venue_type=eq.golf'))
print('[done — zero writes]')
