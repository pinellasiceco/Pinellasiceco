#!/usr/bin/env python3
"""
DBPR Inspection Narrative Scraper
Fetches inspection detail pages for Pinellas V22 violations
and extracts observation text to identify ice machine citations.
"""

import csv
import json
import time
import random
import os
import re
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

# ── Config ────────────────────────────────────────────────────────────────
BASE_URL = "https://www.myfloridalicense.com/inspectionDetail.asp?InspVisitID={vid}"
TERMS_URL = "https://www.myfloridalicense.com/insptermsofuse.asp"
# Output at repo root — data/ is gitignored so results would never be committed
OUTPUT_CSV    = "pinellas_v22_narratives.csv"
PROGRESS_FILE = "scraper_progress.txt"
GENERATED_INPUT = "pinellas_v22_to_scrape.csv"  # auto-generated from fresh DBPR data

# Full violations mode (all Pinellas violations, not just V22)
ALL_VIOLATIONS_INPUT = "data/pinellas_all_violations_to_scrape.csv"
FULL_NARRATIVES_CACHE = "full_inspection_narratives.json"
FULL_PROGRESS_FILE = "full_scraper_progress.txt"

# Fallback: accept user-uploaded CSV wherever it was dropped
_CANDIDATE_INPUTS = [
    GENERATED_INPUT,
    "pinellas v22 to scrape.csv",
    "pinellas_v22_to_scrape.csv",
    "data/pinellas_v22_to_scrape.csv",
    "data/pinellas v22 to scrape.csv",
]

# Column order in the District 3 DBPR CSV (positional fallback if header absent)
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


def refresh_v22_list(data_dir='data/'):
    """
    Regenerate pinellas_v22_to_scrape.csv from the latest District 3
    inspection data. Only includes Visit IDs not already in PROGRESS_FILE.
    Returns number of new records written (0 = nothing to scrape today).
    """
    input_file = os.path.join(data_dir, '3fdinspi_current.csv')
    if not os.path.exists(input_file):
        print(f"  refresh_v22_list: {input_file} not found — skipping regeneration")
        return 0

    done = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            done = {line.strip() for line in f if line.strip()}

    new_records = []
    try:
        with open(input_file, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            raw_header = next(reader, None)
            # Use actual CSV header if present, else fall back to positional columns
            header = raw_header if raw_header and len(raw_header) > 20 else _DBPR_COLS

            for row in reader:
                if len(row) < 10:
                    continue
                rec = dict(zip(header, row))

                if rec.get('County Name', '').strip().lower() != 'pinellas':
                    continue

                v22 = rec.get('V22', '0').strip()
                try:
                    if float(v22 or 0) <= 0:
                        continue
                except (ValueError, TypeError):
                    continue

                vid = str(rec.get('Visit ID', '')).strip()
                if not vid or vid in done:
                    continue

                new_records.append({
                    'Business Name':          rec.get('Business Name', ''),
                    'Address':                rec.get('Address', ''),
                    'City':                   rec.get('City', ''),
                    'Zip':                    rec.get('Zip', ''),
                    'License Number':         rec.get('License Number', ''),
                    'Inspection Type':        rec.get('Inspection Type', ''),
                    'Inspection Disposition': rec.get('Inspection Disposition', ''),
                    'Inspection Date':        rec.get('Inspection Date', ''),
                    'License ID':             rec.get('License ID', ''),
                    'Visit ID':               vid,
                })
    except Exception as e:
        print(f"  refresh_v22_list error: {e}")
        return 0

    if new_records:
        with open(GENERATED_INPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(new_records[0].keys()))
            writer.writeheader()
            writer.writerows(new_records)
        print(f"  Found {len(new_records)} new V22 records to scrape")
    else:
        print("  No new V22 records to scrape today")

    return len(new_records)

# Delay between requests — be respectful to the server
MIN_DELAY = 2.5
MAX_DELAY = 4.5

# Ice machine keywords to search for in observation text
ICE_KEYWORDS = [
    'ice machine', 'ice maker', 'ice bin', 'ice storage',
    'ice scoop', 'ice dispenser', 'ice making', 'icemaker',
    'ice-machine', 'ice-maker', 'ice-bin',
    'interior of ice', 'inside of ice', 'ice unit',
    'slime in ice', 'mold in ice', 'build-up in ice',
    'pink slime', 'black mold', 'biofilm',  # common ice machine findings
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# ── HTML Parser ───────────────────────────────────────────────────────────
class InspectionParser(HTMLParser):
    """Extract violation observation text from DBPR inspection detail page."""

    def __init__(self):
        super().__init__()
        self.violations = []
        self.in_table = False
        self.in_violation_row = False
        self.current_cells = []
        self.current_cell_text = ''
        self.in_td = False
        self.business_name = ''
        self.in_title_area = False
        self.page_text = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'table':
            self.depth += 1
        if tag == 'tr':
            self.in_violation_row = True
            self.current_cells = []
        if tag == 'td':
            self.in_td = True
            self.current_cell_text = ''

    def handle_endtag(self, tag):
        if tag == 'table':
            self.depth -= 1
        if tag == 'td':
            self.in_td = False
            self.current_cells.append(self.current_cell_text.strip())
            self.current_cell_text = ''
        if tag == 'tr':
            self.in_violation_row = False
            # A violation row typically has 3 cells:
            # violation code | (blank) | observation text
            if len(self.current_cells) >= 2:
                # Look for rows with violation codes (like "22-XX-X")
                first = self.current_cells[0].strip()
                if re.match(r'^\d+[-\w]+', first) and len(self.current_cells) >= 2:
                    obs = self.current_cells[-1].strip() if self.current_cells else ''
                    if obs and len(obs) > 5:
                        self.violations.append({
                            'code': first,
                            'observation': obs
                        })

    def handle_data(self, data):
        text = data.strip()
        if self.in_td:
            self.current_cell_text += ' ' + text
        self.page_text.append(text)

    def get_page_text(self):
        return ' '.join(self.page_text)


# ── Fetch page ────────────────────────────────────────────────────────────
def fetch_page(url, session_cookie=None):
    """Fetch a URL and return HTML content."""
    headers = HEADERS.copy()
    if session_cookie:
        headers['Cookie'] = session_cookie

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as resp:
            raw = resp.read()

            # Try common encodings
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return raw.decode(enc), resp.headers.get('Set-Cookie', '')
                except UnicodeDecodeError:
                    continue
            return raw.decode('utf-8', errors='replace'), ''

    except (URLError, HTTPError) as e:
        print(f"  Fetch error: {e}")
        return None, ''


def init_session():
    """
    Visit the terms of use page to get a valid session.
    The DBPR portal requires this before individual inspection
    pages will load correctly.
    """
    print("Initializing session with DBPR portal...")
    html, cookie = fetch_page(TERMS_URL)
    if html:
        print("  Session initialized")
        return cookie
    print("  Session init failed — proceeding without cookie")
    return None


def is_valid_inspection(html, visit_id):
    """Check that the page actually loaded the right inspection."""
    # If it redirected to default (Tin Cow in Pensacola), skip
    if 'PENSACOLA' in html.upper() and 'TIN COW' in html.upper():
        return False
    if f'{visit_id}' not in html and 'InspVisitID' not in html:
        # Page may have loaded but check for violation content
        if 'Violation' not in html and 'violation' not in html:
            return False
    return True


def parse_inspection(html, visit_id, business_name):
    """Parse inspection HTML and extract violation observations."""
    parser = InspectionParser()
    parser.feed(html)

    results = []
    page_text = parser.get_page_text().lower()

    # Check each violation found
    for v in parser.violations:
        obs_lower = v['observation'].lower()

        # Check if observation mentions ice machine
        ice_match = any(kw in obs_lower for kw in ICE_KEYWORDS)

        results.append({
            'visit_id': visit_id,
            'business_name': business_name,
            'violation_code': v['code'],
            'observation': v['observation'],
            'ice_machine_mention': 'YES' if ice_match else 'NO',
            'ice_keyword_found': next(
                (kw for kw in ICE_KEYWORDS if kw in obs_lower), ''
            ),
        })

    # If parser found no violations, try raw text extraction
    if not results:
        # Look for observation text patterns in raw HTML
        obs_pattern = re.findall(
            r'(?:22-\d+[-\w]+)[^<]*<[^>]+>[^<]*<[^>]+>(.*?)(?:</td>|Warning|Repeat)',
            html, re.IGNORECASE | re.DOTALL
        )
        for obs in obs_pattern:
            obs_clean = re.sub(r'<[^>]+>', '', obs).strip()
            if len(obs_clean) > 10:
                obs_lower = obs_clean.lower()
                ice_match = any(kw in obs_lower for kw in ICE_KEYWORDS)
                results.append({
                    'visit_id': visit_id,
                    'business_name': business_name,
                    'violation_code': '22-xx-x',
                    'observation': obs_clean,
                    'ice_machine_mention': 'YES' if ice_match else 'NO',
                    'ice_keyword_found': next(
                        (kw for kw in ICE_KEYWORDS if kw in obs_lower), ''
                    ),
                })

    return results


def load_progress():
    """Load previously scraped visit IDs to allow resuming."""
    done = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            for line in f:
                done.add(line.strip())
    return done


def save_progress(visit_id):
    """Mark a visit ID as done."""
    with open(PROGRESS_FILE, 'a') as f:
        f.write(f"{visit_id}\n")


# ── Full violations mode helpers ──────────────────────────────────────────

def load_full_narratives_cache():
    if os.path.exists(FULL_NARRATIVES_CACHE):
        try:
            with open(FULL_NARRATIVES_CACHE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_full_narratives_cache(cache):
    with open(FULL_NARRATIVES_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)


def load_full_progress():
    done = set()
    if os.path.exists(FULL_PROGRESS_FILE):
        with open(FULL_PROGRESS_FILE) as f:
            done = {line.strip() for line in f if line.strip()}
    return done


def save_full_progress(lic):
    with open(FULL_PROGRESS_FILE, 'a') as f:
        f.write(f"{lic}\n")


def run_full_violations_scrape():
    """Scrape full inspection narratives for all Pinellas violations."""
    print("=== DBPR Full Violations Scraper ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    records = []
    with open(ALL_VIOLATIONS_INPUT, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    print(f"Loaded {len(records)} records from {ALL_VIOLATIONS_INPUT}")

    done = load_full_progress()
    remaining = [r for r in records if r['License Number'] not in done]
    print(f"Already scraped: {len(done)} | Remaining: {len(remaining)}")

    max_records = int(os.environ.get('MAX_RECORDS', '0') or 0)
    if max_records > 0:
        remaining = remaining[:max_records]
        print(f"Capped to {max_records} records (MAX_RECORDS env var)")

    if not remaining:
        print("All records already scraped!")
        return

    cache = load_full_narratives_cache()
    session_cookie = init_session()

    success_count = 0
    fail_count = 0

    for i, record in enumerate(remaining):
        vid = record['Visit ID'].strip()
        biz = record['Business Name'].strip()
        lic = record['License Number'].strip()

        if i % 25 == 0:
            print(f"\n[{i+1}/{len(remaining)}] Progress — "
                  f"Success: {success_count} | Failed: {fail_count}")

        print(f"  [{i+1}] {biz[:40]} | Lic {lic}", end='', flush=True)

        url = BASE_URL.format(vid=vid)
        html, new_cookie = fetch_page(url, session_cookie)
        if new_cookie:
            session_cookie = new_cookie

        if not html:
            print(" → FAILED")
            fail_count += 1
            save_full_progress(lic)
            time.sleep(MIN_DELAY)
            continue

        if not is_valid_inspection(html, vid):
            print(" → REDIRECT")
            fail_count += 1
            if fail_count % 10 == 0:
                session_cookie = init_session()
            save_full_progress(lic)
            time.sleep(MIN_DELAY)
            continue

        violations = parse_inspection(html, vid, biz)
        print(f" → {len(violations)} violations")

        if violations:
            cache[lic] = [
                {'code': v['violation_code'], 'observation': v['observation']}
                for v in violations
            ]
            success_count += 1

        save_full_narratives_cache(cache)
        save_full_progress(lic)

        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    print(f"\n=== FULL VIOLATIONS SCRAPE COMPLETE ===")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successfully scraped: {success_count} | Failed: {fail_count}")
    print(f"Cache size: {len(cache)} licenses")


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print(f"=== DBPR Ice Machine Citation Scraper ===")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Full violations mode: triggered when build_violations_list.py has run
    if os.path.exists(ALL_VIOLATIONS_INPUT):
        run_full_violations_scrape()
        return

    # V22 ice machine mode (legacy — runs when full violations list is absent)
    # Regenerate input list from fresh DBPR data (skips already-scraped Visit IDs)
    new_count = refresh_v22_list('data/')
    if new_count == 0:
        # Fall back to any existing user-uploaded input file
        existing = next((p for p in _CANDIDATE_INPUTS if os.path.exists(p)), None)
        if not existing:
            print("No new V22 records and no input CSV found — nothing to scrape")
            sys.exit(0)
        print(f"  Using existing input: {existing}")

    # Resolve input file (generated file takes priority)
    input_csv = next((p for p in _CANDIDATE_INPUTS if os.path.exists(p)), None)
    if not input_csv:
        print(f"ERROR: No input CSV found")
        sys.exit(1)

    records = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    print(f"Loaded {len(records)} V22 inspection records from {input_csv}")

    # Check progress
    done = load_progress()
    remaining = [r for r in records if r['Visit ID'] not in done]
    print(f"Already scraped: {len(done)}")
    print(f"Remaining: {len(remaining)}")

    # Optional cap for test runs — set MAX_RECORDS env var to limit
    max_records = int(os.environ.get('MAX_RECORDS', '0') or 0)
    if max_records > 0:
        remaining = remaining[:max_records]
        print(f"Capped to {max_records} records (MAX_RECORDS env var)")

    if not remaining:
        print("All records already scraped!")
        return

    # Init session
    session_cookie = init_session()

    # Prepare output
    output_exists = os.path.exists(OUTPUT_CSV)
    outfile = open(OUTPUT_CSV, 'a', newline='', encoding='utf-8')
    fieldnames = [
        'visit_id', 'business_name', 'city', 'inspection_date',
        'inspection_type', 'violation_code', 'observation',
        'ice_machine_mention', 'ice_keyword_found',
        'license_number', 'license_id',
    ]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    if not output_exists:
        writer.writeheader()

    # Scrape
    success_count = 0
    fail_count = 0
    ice_count = 0
    no_violations_count = 0

    for i, record in enumerate(remaining):
        vid = record['Visit ID'].strip()
        biz = record['Business Name'].strip()
        city = record.get('City', '').strip()
        date = record.get('Inspection Date', '').strip()
        itype = record.get('Inspection Type', '').strip()
        lic = record.get('License Number', '').strip()
        lid = record.get('License ID', '').strip()

        url = BASE_URL.format(vid=vid)

        if i % 50 == 0:
            print(f"\n[{i+1}/{len(remaining)}] Progress — "
                  f"Success: {success_count} | "
                  f"Ice mentions: {ice_count} | "
                  f"Failed: {fail_count}")

        print(f"  [{i+1}] {biz[:40]} | Visit {vid}", end='', flush=True)

        html, new_cookie = fetch_page(url, session_cookie)
        if new_cookie:
            session_cookie = new_cookie

        if not html:
            print(" → FAILED")
            fail_count += 1
            save_progress(vid)
            time.sleep(MIN_DELAY)
            continue

        if not is_valid_inspection(html, vid):
            print(" → REDIRECT (session issue)")
            fail_count += 1
            # Try re-initializing session
            if fail_count % 10 == 0:
                session_cookie = init_session()
            save_progress(vid)
            time.sleep(MIN_DELAY)
            continue

        violations = parse_inspection(html, vid, biz)

        if not violations:
            no_violations_count += 1
            print(" → no violations parsed")
            # Still save as scraped so we don't retry
            writer.writerow({
                'visit_id': vid,
                'business_name': biz,
                'city': city,
                'inspection_date': date,
                'inspection_type': itype,
                'violation_code': '',
                'observation': 'NO VIOLATIONS PARSED',
                'ice_machine_mention': 'UNKNOWN',
                'ice_keyword_found': '',
                'license_number': lic,
                'license_id': lid,
            })
        else:
            has_ice = False
            for v in violations:
                if v['ice_machine_mention'] == 'YES':
                    has_ice = True
                    ice_count += 1
                writer.writerow({
                    'visit_id': vid,
                    'business_name': biz,
                    'city': city,
                    'inspection_date': date,
                    'inspection_type': itype,
                    'violation_code': v['violation_code'],
                    'observation': v['observation'],
                    'ice_machine_mention': v['ice_machine_mention'],
                    'ice_keyword_found': v['ice_keyword_found'],
                    'license_number': lic,
                    'license_id': lid,
                })
            print(f" → {len(violations)} violations | "
                  f"{'🧊 ICE' if has_ice else 'no ice'}")
            success_count += 1

        outfile.flush()
        save_progress(vid)

        # Polite delay
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    outfile.close()

    print(f"\n=== COMPLETE ===")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successfully scraped: {success_count}")
    print(f"Failed/redirected:    {fail_count}")
    print(f"No violations parsed: {no_violations_count}")
    print(f"Ice machine mentions: {ice_count}")
    if success_count > 0:
        pct = ice_count / success_count * 100
        print(f"Ice mention rate:     {pct:.1f}%")
    print(f"Output: {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
