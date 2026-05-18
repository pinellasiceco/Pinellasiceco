#!/usr/bin/env python3
"""
CleanScore data export — runs after build.py in CI.
Exports violation data and partner data to Supabase Storage.
Reads from built index.html (P[] array) and the
prospecting app's Supabase PARTNERS table.
"""

import os
import json
import re
import requests

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

VIOLATION_CATEGORIES = {
    'ice_machine': [
        'ice machine', 'ice maker', 'ice bin', 'evaporator',
        'water tray', 'spray bar', 'ice storage', 'ice chute',
        'ice dispenser', 'ice scoop'
    ],
    'temperature': [
        'temperature', 'hot holding', 'cold holding', 'cooling',
        'reheating', '135 degrees', '41 degrees', 'tcs food',
        'potentially hazardous', 'time/temperature', 'ambient'
    ],
    'hand_washing': [
        'handwash', 'hand washing', 'hand sink', 'hair restraint',
        'gloves', 'bare hand', 'employee hygiene',
        'improper handwashing', 'hand wash'
    ],
    'food_storage': [
        'stored on floor', 'raw animal food', 'ready-to-eat',
        'properly separated', 'cross contamination', 'date marking',
        'labeling', 'food storage', 'fifo'
    ],
    'food_contact': [
        'food contact surface', 'cutting board', 'can opener',
        'sanitized', 'utensils', 'slicer', 'food-contact'
    ],
    'pest': [
        'pest', 'rodent', 'mouse', 'rat', 'cockroach',
        'insect', 'fly', 'fruit fly', 'pest activity',
        'evidence of pest', 'vermin', 'roach'
    ],
    'hood': [
        'hood', 'grease accumulation', 'ventilation', 'exhaust filter',
        'grease trap', 'fire suppression', 'ductwork'
    ],
    'employee_training': [
        'certified food manager', 'food handler', 'employee training',
        'food safety certification', 'servsafe',
        'required employee training'
    ],
    'plumbing': [
        'plumbing', 'handwash sink', 'mop sink', 'sewage',
        'backflow', 'drain', 'running water', 'hot water'
    ],
    'equipment': [
        'reach-in', 'cooler', 'freezer', 'ice buildup',
        'in disrepair', 'not properly maintained',
        'refrigeration unit', 'door gasket'
    ],
    'premises': [
        'premises', 'ceiling', 'mold', 'non-food contact',
        'accumulated debris', 'general sanitation'
    ]
}

# DBPR violation code → CleanScore category
CODE_CATEGORIES = {
    'V14': 'food_contact',
    'V22': 'ice_machine',
    'V23': 'food_contact',
    'V36': 'premises',
    'V37': 'equipment',
    'V50': 'food_contact',
    'V51': 'premises',
}

# DBPR violation code → human-readable description
CODE_DESCRIPTIONS = {
    'V14': 'Food contact surfaces not clean or sanitized',
    'V22': 'Non-PHF food contact surfaces not clean (ice machine)',
    'V23': 'Utensils/containers not properly sanitized',
    'V36': 'Physical facilities not clean or maintained',
    'V37': 'Equipment not maintained in good repair',
    'V50': 'Food contact surfaces soiled',
    'V51': 'Non-food contact surfaces soiled',
}


def categorize_violation(text):
    t = text.lower()
    for cat, kws in VIOLATION_CATEGORIES.items():
        for kw in kws:
            if kw in t:
                return cat
    return 'other'


def load_prospects():
    if not os.path.exists('index.html'):
        print('  index.html not found')
        return []
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        start = html.find('const P=[')
        if start == -1:
            start = html.find('const P =')
            if start == -1:
                print('  P[] not found in index.html')
                return []
        bracket_start = html.find('[', start)
        depth = 0
        i = bracket_start
        while i < len(html):
            if html[i] == '[':
                depth += 1
            elif html[i] == ']':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        records = json.loads(html[bracket_start:i + 1])
        print(f'  Loaded {len(records):,} prospects from index.html')
        return records
    except Exception as e:
        print(f'  Prospects load error: {e}')
        return []


def load_partners():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print('  No Supabase credentials for partners')
        return []
    try:
        url = f'{SUPABASE_URL}/rest/v1/pic_partners?select=*'
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            rows = r.json()
            print(f'  Loaded {len(rows)} partners from Supabase')
            return rows
        else:
            print(f'  Partners load failed: {r.status_code}')
            return []
    except Exception as e:
        print(f'  Partners error: {e}')
        return []


def upload_to_storage(filename, data):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(f'  No credentials — skipping upload of {filename}')
        return False
    try:
        url = f'{SUPABASE_URL}/storage/v1/object/cleanscore/{filename}'
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'x-upsert': 'true',
        }
        payload = json.dumps(data, ensure_ascii=False)
        r = requests.post(url, headers=headers,
                          data=payload.encode('utf-8'), timeout=30)
        if r.status_code in (200, 201):
            print(f'  Uploaded {filename} ({len(payload) / 1024:.1f} KB)')
            return True
        else:
            print(f'  Upload failed {filename}: {r.status_code} {r.text[:100]}')
            return False
    except Exception as e:
        print(f'  Upload error {filename}: {e}')
        return False


def parse_violations_from_observation(obs_text, codes):
    """Parse cit_observation text into individual violation records."""
    violations = []
    lines = []
    for line in re.split(r'\n|;|\d+\.\s', obs_text):
        line = line.strip()
        if len(line) > 20:
            lines.append(line)
    if not lines:
        lines = [obs_text[:300]]

    for line in lines:
        line_lower = line.lower()
        corrected = ('corrected on-site' in line_lower or
                     'corrected on site' in line_lower)
        repeat = 'repeat violation' in line_lower

        # Determine severity from text markers
        if 'high priority' in line_lower:
            severity = 'high'
        elif 'intermediate' in line_lower:
            severity = 'major'
        elif 'basic' in line_lower:
            severity = 'basic'
        else:
            severity = 'major'

        violations.append({
            'text': line[:300],
            'severity': severity,
            'corrected_on_site': corrected,
            'repeat': repeat,
            'category': categorize_violation(line),
        })
    return violations


def synthesize_violations_from_codes(codes, total_viol, high_viol):
    """Build violation records from DBPR codes when no observation text exists."""
    violations = []
    used_codes = [c for c in (codes or []) if c in CODE_DESCRIPTIONS]

    if used_codes:
        for code in used_codes:
            violations.append({
                'text': CODE_DESCRIPTIONS[code],
                'severity': 'high' if high_viol > 0 and code in ('V14', 'V22') else 'basic',
                'corrected_on_site': False,
                'repeat': False,
                'category': CODE_CATEGORIES.get(code, 'other'),
            })
    else:
        # Fallback: generic entry using violation counts
        severity = 'high' if high_viol > 0 else 'basic'
        violations.append({
            'text': f'{total_viol} violation(s) cited at most recent inspection',
            'severity': severity,
            'corrected_on_site': False,
            'repeat': False,
            'category': 'other',
        })

    return violations


def build_violations_export(records):
    pinellas = [
        r for r in records
        if str(r.get('county', '')).lower() == 'pinellas'
    ]

    # County stats over all Pinellas records
    total_businesses = len(pinellas)
    if total_businesses == 0:
        print('  No Pinellas records found')
        return []

    viol_counts = [(r.get('total_viol') or 0) for r in pinellas]
    avg_viol = round(sum(viol_counts) / total_businesses, 2)
    pct_with_viol = round(
        sum(1 for v in viol_counts if v > 0) / total_businesses, 4
    )
    county_stats = {
        'total_businesses_in_county': total_businesses,
        'avg_violations_county': avg_viol,
        'pct_with_any_violation': pct_with_viol,
    }

    export = []
    for r in pinellas:
        total_viol = int(r.get('total_viol') or 0)
        if total_viol == 0:
            continue

        high_viol = int(r.get('high_viol') or 0)
        codes = r.get('codes') or []
        obs = (r.get('cit_observation') or '').strip()

        if obs:
            violations = parse_violations_from_observation(obs, codes)
        else:
            violations = synthesize_violations_from_codes(codes, total_viol, high_viol)

        insp_date = str(r.get('last_insp') or '')[:10]
        disposition = str(r.get('last_disp') or '')

        history = []
        if insp_date:
            history.append({
                'date': insp_date,
                'disposition': disposition,
                'violation_count': total_viol,
            })

        export.append({
            'id': str(r.get('id', '')),
            'license': str(r.get('id', '')),
            'name': str(r.get('name', '')),
            'address': str(r.get('address', '')),
            'city': str(r.get('city', '')),
            'phone': str(r.get('phone', '')),
            'last_inspection_date': insp_date,
            'last_inspection_disposition': disposition,
            'violations': violations,
            'violation_count': total_viol,
            'inspection_history': history,
            'county_stats': county_stats,
        })

    print(f'  Built {len(export)} Pinellas violation records')
    return export


def build_partners_export(partner_rows):
    export = []
    for row in partner_rows:
        data = row.get('data') or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}

        ptype = str(data.get('type', '') or row.get('type', '')).lower()
        name = str(data.get('name', '') or row.get('name', ''))
        phone = str(data.get('phone', '') or row.get('phone', ''))
        city = str(data.get('city', '') or row.get('city', ''))

        if not name or not ptype:
            continue

        export.append({
            'id': str(row.get('id', '') or row.get('prospect_id', '')),
            'name': name,
            'type': ptype,
            'phone': phone,
            'city': city,
            'fit_score': int(data.get('fit_score', 50) or 50),
        })

    print(f'  Built {len(export)} partner records')
    return export


def main():
    print('Exporting CleanScore data...')

    records = load_prospects()
    if not records:
        print('  No prospects — aborting export')
        return

    partner_rows = load_partners()

    violations = build_violations_export(records)
    if violations:
        upload_to_storage('cleanscore_violations.json', violations)

    partners = build_partners_export(partner_rows)
    if partners:
        upload_to_storage('cleanscore_partners.json', partners)

    os.makedirs('data', exist_ok=True)
    with open('data/cleanscore_violations.json', 'w') as f:
        json.dump(violations[:5], f, indent=2)
    print('  Sample written to data/cleanscore_violations.json')

    print(f'CleanScore export complete: '
          f'{len(violations)} businesses, '
          f'{len(partners)} partners')


if __name__ == '__main__':
    main()
