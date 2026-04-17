#!/usr/bin/env python3
"""
download_data.py -- runs automatically in GitHub Actions every Monday.
Downloads fresh FL DBPR inspection data + license extract before build.py runs.
"""
import sys, requests
from pathlib import Path
from datetime import date

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# District 3 = Pinellas, Hillsborough, Pasco, Citrus, Hernando, Polk, Sumter
CURRENT_URL = 'https://www2.myfloridalicense.com/sto/file_download/extracts/3fdinspi.csv'

# All available historical files -- downloaded once, then cached forever
# Mix of District 3 only (smaller) and statewide (build.py filters to District 3)
HISTORICAL = [
    # District 3 specific -- smaller files
    ('3fdinspi_2021.csv',   'https://www2.myfloridalicense.com/sto/file_download/hr/3fdinspi_2021.csv'),
    # Statewide -- larger, build.py filters to District 3 counties
    ('fdinspi_2122.xlsx',   'https://www2.myfloridalicense.com/hr/inspections/fdinspi_2122.xlsx'),
    ('fdinspi_2223.xlsx',   'https://www2.myfloridalicense.com/sto/file_download/hr/fdinspi_2223.xlsx'),
    ('fdinspi_2324.xlsx',   'https://www2.myfloridalicense.com/hr/inspections/fdinspi_2324.xlsx'),
    ('fdinspi_2425.xlsx',   'https://www2.myfloridalicense.com/hr/inspections/fdinspi_2425.xlsx'),
]

# Active license extract -- phones + seats + rank code
LICENSE_URL = 'https://www2.myfloridalicense.com/sto/file_download/extracts/hrfood3.csv'

def download(url, dest, label):
    print(f'  Downloading {label}...', flush=True)
    try:
        r = requests.get(url, timeout=180, stream=True)
        r.raise_for_status()
        size = 0
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
                size += len(chunk)
        print(f'    OK: {dest.name} ({size/1024/1024:.1f} MB)')
        return True
    except Exception as e:
        print(f'    WARNING: {label} failed -- {e}')
        return False

print(f'\nDownloading FL DBPR data -- {date.today()}\n')

# Always refresh current fiscal year
download(CURRENT_URL, DATA_DIR / '3fdinspi_current.csv', 'District 3 current FY')

# Always refresh license extract (phones + seats change as businesses update)
download(LICENSE_URL, DATA_DIR / 'hrfood3_licenses.csv', 'District 3 license extract')

# Emergency closures -- last 4 weeks (inspector always returns to these)
print('  Downloading recent emergency closures...')
from datetime import timedelta
today = date.today()
for weeks_back in range(5):
    # Find the most recent Monday
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_back)
    sunday = monday + timedelta(days=6)
    fname = f'EOS_Weekly_Extract_{sunday.isoformat()}.xlsx'
    url = f'https://www2.myfloridalicense.com/hr/inspections/documents/{fname}'
    dest = DATA_DIR / fname
    if not dest.exists():
        if download(url, dest, f'Emergency closures week of {sunday}'):
            break  # got the most recent one

# Historical: download once, skip if already cached
print()
for fname, url in HISTORICAL:
    dest = DATA_DIR / fname
    if dest.exists():
        print(f'  {fname}: cached ({dest.stat().st_size/1024/1024:.1f} MB), skipping')
    else:
        download(url, dest, fname)

# Summary
print()
files = sorted(DATA_DIR.iterdir())
print(f'Data folder: {len(files)} file(s)')
for f in files:
    print(f'  {f.name} ({f.stat().st_size/1024/1024:.1f} MB)')


# ── OSM PHONE LOOKUP ──────────────────────────────────────────────────────────
# Queries OpenStreetMap Overpass API for phone numbers and hours
# Completely free, no API key required
# Cached in data/osm_phones.json - only re-fetches missing businesses

import json, time, math

OSM_CACHE = DATA_DIR / 'osm_phones.json'

def load_osm_cache():
    try:
        return json.loads(OSM_CACHE.read_text()) if OSM_CACHE.exists() else {}
    except:
        return {}

def save_osm_cache(cache):
    OSM_CACHE.write_text(json.dumps(cache, indent=2))

def overpass_query(bbox_str, amenity_types):
    """Query Overpass for businesses with phones in a bounding box."""
    amenity_filter = '|'.join(amenity_types)
    query = f"""[out:json][timeout:30];
(
  node["amenity"~"{amenity_filter}"]["phone"]{bbox_str};
  way["amenity"~"{amenity_filter}"]["phone"]{bbox_str};
);
out body;"""
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({'data': query}).encode()
        req = urllib.request.Request(
            'https://overpass-api.de/api/interpreter',
            data=data, method='POST'
        )
        req.add_header('User-Agent', 'PinellasIceCo/1.0 (business tool)')
        resp = urllib.request.urlopen(req, timeout=35)
        result = json.loads(resp.read())
        return result.get('elements', [])
    except Exception as e:
        print(f'    Overpass error: {e}')
        return []

def normalize_name(name):
    """Normalize business name for fuzzy matching."""
    import re
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9 ]', ' ', name)
    name = re.sub(r'\b(llc|inc|corp|restaurant|rest|bar|grill|cafe|the)\b', '', name)
    return re.sub(r'\s+', ' ', name).strip()

def name_similarity(a, b):
    """Simple word overlap similarity 0-1."""
    wa = set(normalize_name(a).split())
    wb = set(normalize_name(b).split())
    if not wa or not wb:
        return 0
    return len(wa & wb) / max(len(wa), len(wb))

def fetch_osm_phones():
    """Fetch phone numbers from OSM for target counties."""
    print('\n  Fetching phone numbers from OpenStreetMap...')
    
    cache = load_osm_cache()
    
    # Target bounding boxes for our counties
    # Format: (south, west, north, east)
    COUNTY_BOXES = {
        'Pinellas':     (27.60, -82.85, 28.10, -82.45),
        'Hillsborough': (27.60, -82.65, 28.15, -82.10),
        'Pasco':        (28.10, -82.75, 28.55, -82.00),
        'Citrus':       (28.65, -82.75, 29.10, -82.15),
        'Hernando':     (28.25, -82.60, 28.70, -82.00),
    }
    
    AMENITY_TYPES = ['restaurant', 'bar', 'cafe', 'fast_food', 'pub',
                     'food_court', 'ice_cream', 'biergarten']
    
    total_found = 0
    
    for county, (s, w, n, e) in COUNTY_BOXES.items():
        cache_key = f'county_{county}'
        # Re-fetch if older than 30 days or missing
        import time as time_mod
        cached = cache.get(cache_key, {})
        age_days = (time_mod.time() - cached.get('fetched_at', 0)) / 86400
        
        if age_days < 30 and cached.get('businesses'):
            print(f'    {county}: cached ({len(cached["businesses"])} businesses)')
            total_found += len(cached['businesses'])
            continue
        
        print(f'    {county}: querying OSM...', end=' ', flush=True)
        bbox = f'({s},{w},{n},{e})'
        elements = overpass_query(bbox, AMENITY_TYPES)
        
        businesses = []
        for el in elements:
            tags = el.get('tags', {})
            phone = tags.get('phone', tags.get('contact:phone', ''))
            name = tags.get('name', '')
            if not phone or not name:
                continue
            
            # Normalize phone to US format
            import re
            phone_clean = re.sub(r'[^\d+]', '', phone)
            if phone_clean.startswith('+1'):
                phone_clean = phone_clean[2:]
            if len(phone_clean) == 10:
                phone_clean = f'({phone_clean[:3]}) {phone_clean[3:6]}-{phone_clean[6:]}'
            
            businesses.append({
                'name': name,
                'phone': phone_clean,
                'hours': tags.get('opening_hours', ''),
                'lat': el.get('lat', tags.get('lat')),
                'lon': el.get('lon', tags.get('lon')),
                'addr': tags.get('addr:street', ''),
                'city': tags.get('addr:city', ''),
            })
        
        cache[cache_key] = {
            'fetched_at': time_mod.time(),
            'businesses': businesses,
        }
        save_osm_cache(cache)
        total_found += len(businesses)
        print(f'{len(businesses)} businesses with phones')
        time.sleep(2)  # Be polite to Overpass
    
    print(f'  OSM total: {total_found} businesses with phone numbers cached')
    return cache

try:
    fetch_osm_phones()
except Exception as e:
    print(f'  OSM lookup skipped: {e}')

print('\nAll downloads complete.')
