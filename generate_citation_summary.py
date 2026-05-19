#!/usr/bin/env python3
"""
generate_citation_summary.py
Reads ALL DBPR CSV/xlsx files, finds every Pinellas business with a
V22 ice machine violation, and calculates the most recent citation date
directly from the live CSV data.

cit_latest_date comes from the CSV — NEVER from scraper cache.
This ensures Fresh Citations on the Home tab reflects current data.

Output: ice_citation_by_business.csv (repo root, read by build.py)
"""

import os
import re
import warnings
from datetime import date, timedelta

import pandas as pd

DATA_DIR = 'data'
OUTPUT   = 'ice_citation_by_business.csv'

_DBPR_COLS = (
    ['District', 'County Number', 'County Name',
     'License Type Code', 'License Number',
     'Business Name', 'Address', 'City', 'Zip',
     'Inspection Number', 'Visit Number',
     'Inspection Class', 'Inspection Type',
     'Inspection Disposition', 'Inspection Date',
     'Num Critical', 'Num Noncritical', 'Num Total',
     'Num High Priority', 'Num Intermediate',
     'Num Basic', 'PDA Status']
    + [f'V{i:02d}' for i in range(1, 60)]
    + ['License ID', 'Visit ID']
)

CSV_FILES = [
    ('data/3fdinspi_current.csv', 'csv'),
    ('data/3fdinspi_2021.csv',    'csv'),
    ('data/fdinspi_2122.xlsx',    'xlsx'),
    ('data/fdinspi_2223.xlsx',    'xlsx'),
    ('data/fdinspi_2324.xlsx',    'xlsx'),
    ('data/fdinspi_2425.xlsx',    'xlsx'),
]

_ICE_KEYWORDS = re.compile(
    r'\b(ice\s+machine|ice\s+maker|ice\s+bin|ice\s+scoop|evaporator|condenser|'
    r'mold|slime|biofilm|pink|black|green|sanitize|sanitizer|soiled|dirty|'
    r'buildup|scale|residue|deposit|film|growth|discoloration)\b',
    re.IGNORECASE,
)


def extract_ice_snippet(text, max_chars=300):
    if not text or str(text).strip() in ('', 'nan', 'NO VIOLATIONS PARSED'):
        return ''
    text = re.sub(r'\*\*[^*]+\*\*', '', str(text))
    text = re.sub(r'^\s*(Basic|Intermediate|High Priority)\s*[-–]\s*', '', text,
                  flags=re.I | re.M)
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    ice_sents = [s for s in sentences if _ICE_KEYWORDS.search(s)]
    snippet = ' '.join(ice_sents) if ice_sents else text
    if len(snippet) <= max_chars:
        return snippet
    return snippet[:max_chars].rsplit(' ', 1)[0] + '…'


def load_file(path, fmt):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if fmt == 'csv':
                # 'errors' was never a valid read_csv kwarg; use encoding_errors (pandas>=1.3)
                try:
                    df = pd.read_csv(
                        path, header=None, names=_DBPR_COLS,
                        low_memory=False, encoding='utf-8',
                        encoding_errors='replace',
                    )
                except TypeError:
                    df = pd.read_csv(
                        path, header=None, names=_DBPR_COLS,
                        low_memory=False, encoding='utf-8',
                    )
            else:
                # Try openpyxl (xlsx), then xlrd (old .xls format)
                try:
                    raw = pd.read_excel(path, header=None, engine='openpyxl')
                except Exception:
                    raw = pd.read_excel(path, header=None, engine='xlrd')
                ncols = raw.shape[1]
                # Pad column list if file has more columns than our spec
                cols = list(_DBPR_COLS[:ncols])
                if ncols > len(_DBPR_COLS):
                    cols += [f'Extra{i}' for i in range(ncols - len(_DBPR_COLS))]
                raw.columns = cols
                df = raw
        print(f'  Loaded {path}: {len(df):,} rows')
        return df
    except Exception as e:
        print(f'  Skip {path}: {e}')
        return None


def load_all_data():
    dfs = []
    for path, fmt in CSV_FILES:
        if not os.path.exists(path):
            print(f'  Skip (not found): {path}')
            continue
        df = load_file(path, fmt)
        if df is not None:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    combined = pd.concat(dfs, ignore_index=True)
    print(f'  Total rows combined: {len(combined):,}')
    return combined


def main():
    print('Generating ice citation summary from live CSV data...')

    df = load_all_data()
    if df.empty:
        print('  No data loaded — aborting')
        return

    # Filter to Pinellas County
    county      = df['County Number'].astype(str).str.strip()
    county_name = df['County Name'].astype(str).str.lower().str.strip()
    pinellas = df[(county == '62') | (county_name == 'pinellas')].copy()
    print(f'  Pinellas rows: {len(pinellas):,}')

    if pinellas.empty:
        print('  No Pinellas rows found — check county column')
        return

    # Parse inspection dates from live CSV — THIS IS THE KEY FIX
    # cit_latest_date is always derived from CSV data, never from scraper cache
    pinellas['insp_date'] = pd.to_datetime(
        pinellas['Inspection Date'], errors='coerce', dayfirst=False,
    )

    # V22 flag: non-empty, non-zero, non-null value means ice machine violation
    if 'V22' not in pinellas.columns:
        print('  WARNING: V22 column not found — check _DBPR_COLS mapping')
        return

    v22_str = pinellas['V22'].astype(str).str.strip()
    pinellas['v22_flag'] = (
        v22_str.ne('') & v22_str.ne('0') &
        v22_str.ne('nan') & v22_str.ne('NaN') & v22_str.ne('None')
    )

    v22_rows = pinellas[pinellas['v22_flag']].copy()
    print(f'  V22 violation rows: {len(v22_rows):,}')

    if v22_rows.empty:
        print('  No V22 violations found — check column mapping')
        print(f'  V22 sample values: {pinellas["V22"].dropna().unique()[:10]}')
        return

    v22_rows['license_str'] = v22_rows['License ID'].astype(str).str.strip()

    # Per-license aggregation — one row per business
    summary = v22_rows.groupby('license_str').agg(
        business_name=('Business Name',
                       lambda x: x.mode().iloc[0] if len(x) else ''),
        address=('Address',
                 lambda x: x.mode().iloc[0] if len(x) else ''),
        city=('City',
              lambda x: x.mode().iloc[0] if len(x) else ''),
        cit_latest_date=('insp_date', 'max'),   # most recent V22 date from live CSV
        cit_ice_count=('insp_date', 'count'),    # total V22 inspection rows
        last_disposition=('Inspection Disposition',
                          lambda x: x.dropna().iloc[-1] if len(x.dropna()) else ''),
    ).reset_index()

    summary.rename(columns={'license_str': 'license'}, inplace=True)

    # ISO date string
    summary['cit_latest_date'] = summary['cit_latest_date'].dt.strftime('%Y-%m-%d')

    # Repeat: cited more than once
    summary['cit_repeat'] = summary['cit_ice_count'] > 1

    # Corrected on site
    lic_col = v22_rows['License ID'].astype(str).str.strip()
    corrected = (
        v22_rows.groupby(lic_col)
        .apply(lambda x: x['Inspection Disposition'].astype(str)
               .str.lower().str.contains('corrected on site', na=False).any())
        .reset_index()
    )
    corrected.columns = ['license', 'cit_corrected_on_site']
    summary = summary.merge(corrected, on='license', how='left')

    # Best-effort: merge observation text from scraper narratives if available
    narratives_path = next(
        (p for p in ['pinellas_v22_narratives.csv', 'data/pinellas_v22_narratives.csv']
         if os.path.exists(p)), None,
    )
    if narratives_path:
        try:
            nar = pd.read_csv(narratives_path, low_memory=False, dtype=str)
            key_col = next((c for c in ['license_id', 'license_number']
                            if c in nar.columns), nar.columns[0])
            nar['_key'] = nar[key_col].astype(str).str.strip()
            obs_col = next((c for c in ['observation', 'best_observation']
                            if c in nar.columns), None)
            if obs_col:
                obs_map = (
                    nar.groupby('_key')[obs_col]
                    .apply(lambda x: max(
                        (extract_ice_snippet(v) for v in x),
                        key=len, default='',
                    ))
                )
                summary['best_observation'] = (
                    summary['license'].map(obs_map).fillna('')
                )
                n_matched = int((summary['best_observation'] != '').sum())
                n_nar = int(nar['_key'].nunique())
                print(f'  Narratives: {n_nar} unique licenses, {n_matched}/{len(summary)} businesses matched (key: {key_col})')
            else:
                summary['best_observation'] = ''
        except Exception as e:
            print(f'  Narratives merge skipped: {e}')
            summary['best_observation'] = ''
    else:
        summary['best_observation'] = ''

    today     = date.today()
    week_ago  = str(today - timedelta(days=7))
    month_ago = str(today - timedelta(days=30))
    print(f'  Unique licenses with V22: {len(summary):,}')
    print(f'  Most recent citation date in data: {summary["cit_latest_date"].max()}')
    print(f'  Citations in last 7 days:  '
          f'{(summary["cit_latest_date"] >= week_ago).sum()}')
    print(f'  Citations in last 30 days: '
          f'{(summary["cit_latest_date"] >= month_ago).sum()}')

    summary.to_csv(OUTPUT, index=False)
    print(f'  Written: {OUTPUT} ({len(summary)} records)')


if __name__ == '__main__':
    main()
