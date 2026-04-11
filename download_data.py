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
