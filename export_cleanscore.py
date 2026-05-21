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
from collections import defaultdict
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

FULL_NARRATIVES_CACHE = 'full_inspection_narratives.json'

VIOLATION_CATEGORIES = {
    'ice_machine': {
        'primary': [
            'evaporator', 'spray bar', 'water tray', 'ice bin',
            'ice dispenser', 'ice scoop', 'ice maker interior',
            'ice machine interior', 'ice machine not maintained',
            'ice machine soiled', 'ice machine observed',
        ],
        'secondary': ['ice machine', 'ice maker'],
        'negative': [
            'floor outside', 'standing water', 'near ice',
            'beside ice', 'next to ice', 'floor near', 'dripping',
            'outside of ice', 'exterior of ice',
        ],
    },
    'temperature': {
        'primary': [
            'temperature', 'hot holding', 'cold holding', 'tcs food',
            'potentially hazardous', '135', '41 degrees', '41°',
        ],
        'secondary': ['cooling', 'reheating', 'ambient', 'time/temperature'],
        'negative': [],
    },
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


def infer_business_type(name):
    n = (name or '').lower()
    if re.search(r'\bbar\b|\btavern\b|\blounge\b|\bnightclub\b|\bbrewery\b|\bsaloon\b', n):
        return 'bar'
    if re.search(r'\bcafe\b|\bcoffee\b|\bbakery\b|\bdeli\b|\bbagel\b|\bpastry\b|\bdonut\b', n):
        return 'cafe'
    if re.search(r'\bhotel\b|\binn\b|\bresort\b|\bsuites\b|\bmotel\b', n):
        return 'hotel'
    if re.search(r'\bschool\b|\belementary\b|\buniversity\b|\bcollege\b|\bcafeteria\b', n):
        return 'institutional'
    if re.search(r'\bpizza\b|\bsubway\b|\bmcdonald|\bwendy\b|\bdomino\b', n):
        return 'fast_food'
    return 'restaurant'


def load_full_narratives():
    if not os.path.exists(FULL_NARRATIVES_CACHE):
        return {}
    try:
        with open(FULL_NARRATIVES_CACHE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'  Loaded full narratives for {len(data)} licenses')
        return data
    except Exception as e:
        print(f'  Full narratives load error: {e}')
        return {}


def categorize_violation(text):
    t = text.lower()
    best_cat = 'other'
    best_score = 0

    for cat, rules in VIOLATION_CATEGORIES.items():
        if isinstance(rules, list):
            # Simple keyword list — match gets score 1
            for kw in rules:
                if kw in t and best_score < 1:
                    best_cat = cat
                    best_score = 1
            continue

        # Scored format with primary/secondary/negative
        score = 0
        for neg in rules.get('negative', []):
            if neg in t:
                score = -99
                break
        if score < 0:
            continue
        for kw in rules.get('primary', []):
            if kw in t:
                score += 3
        for kw in rules.get('secondary', []):
            if kw in t:
                score += 1
        if score > best_score:
            best_score = score
            best_cat = cat

    return best_cat


def extract_violation_codes(record):
    """Extract DBPR violation codes (V01-V58) from a prospect record."""
    codes = record.get('codes') or record.get('violation_codes', [])
    if codes:
        return list(codes) if isinstance(codes, list) else [codes]
    # Fall back to scanning observation text for V## patterns
    obs = str(record.get('cit_observation', '') or '')
    found = re.findall(r'\bV\d{2}\b', obs.upper())
    if found:
        return list(dict.fromkeys(found))  # deduplicated, order preserved
    if record.get('ice_confirmed'):
        return ['V22']
    return []


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

        # Try to find a code that matches this specific line
        line_cat = categorize_violation(line)
        line_code = next(
            (c for c in (codes or []) if CODE_CATEGORIES.get(c) == line_cat),
            codes[0] if codes else None
        )
        violations.append({
            'text': line[:300],
            'severity': severity,
            'corrected_on_site': corrected,
            'repeat': repeat,
            'category': line_cat,
            'code': line_code,
            'all_codes': list(codes) if codes else [],
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
                'code': code,
                'all_codes': used_codes,
            })
    else:
        severity = 'high' if high_viol > 0 else 'basic'
        violations.append({
            'text': f'{total_viol} violation(s) cited at most recent inspection',
            'severity': severity,
            'corrected_on_site': False,
            'repeat': False,
            'category': 'other',
            'code': None,
            'all_codes': [],
        })

    return violations


def get_best_narrative(r, full_narratives):
    """Return (violations, source) using best available narrative source."""
    lic = str(r.get('id', ''))
    codes = extract_violation_codes(r)
    total_viol = int(r.get('total_viol') or 0)
    high_viol = int(r.get('high_viol') or 0)

    # Priority 1: cit_observation (V22 ice machine text already embedded in P[])
    obs = (r.get('cit_observation') or '').strip()
    if obs:
        return parse_violations_from_observation(obs, codes), 'ice_citation'

    # Priority 2: full inspection narrative from scraper cache
    cached = full_narratives.get(lic)
    if cached:
        viols = []
        for entry in cached:
            viol_text = (entry.get('observation') or '').strip()
            entry_codes = re.findall(r'\bV\d{2}\b', viol_text.upper())
            if len(viol_text) > 10:
                viols.extend(parse_violations_from_observation(viol_text, entry_codes or codes))
        if viols:
            return viols, 'full_narrative'

    # Priority 3: synthesize from violation codes / counts
    return synthesize_violations_from_codes(codes, total_viol, high_viol), 'synthesized'


def build_violations_export(records, full_narratives=None):
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

    if full_narratives is None:
        full_narratives = {}

    export = []
    for r in pinellas:
        total_viol = int(r.get('total_viol') or 0)
        if total_viol == 0:
            continue

        violations, narrative_source = get_best_narrative(r, full_narratives)

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
            'narrative_source': narrative_source,
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


def build_stats_export(records, violations_export):
    """Build data intelligence stats from all Pinellas records."""
    pinellas = [r for r in records if str(r.get('county', '')).lower() == 'pinellas']
    if not pinellas:
        return {}

    today = datetime.utcnow().date()

    # ── 1. Business type risk ─────────────────────────────────────────────────
    type_totals = defaultdict(lambda: {'count': 0, 'viol_sum': 0, 'with_viols': 0,
                                       'cat_counts': defaultdict(int)})
    for r in pinellas:
        btype = infer_business_type(r.get('name', ''))
        tv = int(r.get('total_viol') or 0)
        type_totals[btype]['count'] += 1
        type_totals[btype]['viol_sum'] += tv
        if tv > 0:
            type_totals[btype]['with_viols'] += 1
    for biz in violations_export:
        btype = infer_business_type(biz.get('name', ''))
        for v in biz.get('violations', []):
            type_totals[btype]['cat_counts'][v.get('category', 'other')] += 1

    business_type_risk = {}
    for btype, s in type_totals.items():
        if s['count'] < 5:
            continue
        top_cat = max(s['cat_counts'].items(), key=lambda x: x[1])[0] \
            if s['cat_counts'] else 'other'
        business_type_risk[btype] = {
            'count': s['count'],
            'violation_rate': round(s['with_viols'] / s['count'], 3),
            'avg_violations': round(s['viol_sum'] / s['count'], 2),
            'top_category': top_cat,
        }

    # ── 2. Repeat violation risk ──────────────────────────────────────────────
    cat_repeat = defaultdict(lambda: {'total': 0, 'repeat': 0})
    total_viols = total_repeat = 0
    for biz in violations_export:
        for v in biz.get('violations', []):
            cat = v.get('category', 'other')
            cat_repeat[cat]['total'] += 1
            total_viols += 1
            if v.get('repeat'):
                cat_repeat[cat]['repeat'] += 1
                total_repeat += 1

    repeat_risk = {
        'overall': {
            'total_violations': total_viols,
            'repeat_count': total_repeat,
            'rate': round(total_repeat / total_viols, 3) if total_viols else 0,
        },
        'by_category': {
            cat: {
                'total': s['total'],
                'repeat_count': s['repeat'],
                'rate': round(s['repeat'] / s['total'], 3) if s['total'] else 0,
            }
            for cat, s in cat_repeat.items() if s['total'] >= 5
        },
    }

    # ── 3. Predictive inspection timing ──────────────────────────────────────
    intervals = []
    buckets = {'recent': 0, 'normal': 0, 'due': 0, 'overdue': 0}
    for r in pinellas:
        ds = str(r.get('last_insp') or '')[:10]
        if len(ds) == 10:
            try:
                insp_date = datetime.strptime(ds, '%Y-%m-%d').date()
                days = (today - insp_date).days
                intervals.append(days)
                if days <= 60:
                    buckets['recent'] += 1
                elif days <= 120:
                    buckets['normal'] += 1
                elif days <= 180:
                    buckets['due'] += 1
                else:
                    buckets['overdue'] += 1
            except ValueError:
                pass

    total_timed = sum(buckets.values())
    median_days = sorted(intervals)[len(intervals) // 2] if intervals else 180
    inspection_timing = {
        'median_days_since_inspection': int(median_days),
        'total_tracked': total_timed,
        'tiers': {
            k: {'label': lbl, 'count': buckets[k],
                'pct': round(buckets[k] / total_timed, 3) if total_timed else 0}
            for k, lbl in [('recent', '0-60 days'), ('normal', '60-120 days'),
                           ('due', '120-180 days'), ('overdue', '180+ days')]
        },
    }

    # ── 4. Cross-violation correlation ───────────────────────────────────────
    co_occur = defaultdict(lambda: defaultdict(int))
    cat_biz_total = defaultdict(int)
    for biz in violations_export:
        cats = list({v.get('category', 'other') for v in biz.get('violations', [])})
        for cat in cats:
            cat_biz_total[cat] += 1
        for i, c1 in enumerate(cats):
            for c2 in cats[i + 1:]:
                co_occur[c1][c2] += 1
                co_occur[c2][c1] += 1

    cross_violations = {}
    for cat, co in co_occur.items():
        if cat_biz_total[cat] < 5:
            continue
        pairs = sorted(
            [{'category': c2, 'co_occurrence_rate': round(n / cat_biz_total[cat], 3)}
             for c2, n in co.items()],
            key=lambda x: -x['co_occurrence_rate']
        )[:4]
        if pairs:
            cross_violations[cat] = pairs

    # ── 5. Neighborhood benchmarking (by city) ───────────────────────────────
    city_buckets = defaultdict(lambda: {'count': 0, 'viol_sum': 0, 'score_sum': 0, 'with_viols': 0})
    for r in pinellas:
        city = str(r.get('city') or '').strip().lower()
        if not city:
            continue
        tv = int(r.get('total_viol') or 0)
        hv = int(r.get('high_viol') or 0)
        score = max(0, min(100, 100 - tv * 8 - hv * 5))
        city_buckets[city]['count'] += 1
        city_buckets[city]['viol_sum'] += tv
        city_buckets[city]['score_sum'] += score
        if tv > 0:
            city_buckets[city]['with_viols'] += 1

    neighborhood = {
        city: {
            'count': s['count'],
            'avg_violations': round(s['viol_sum'] / s['count'], 2),
            'avg_score': round(s['score_sum'] / s['count']),
            'violation_rate': round(s['with_viols'] / s['count'], 3),
        }
        for city, s in city_buckets.items() if s['count'] >= 5
    }

    print(f'  Stats: {len(business_type_risk)} business types, '
          f'{len(cross_violations)} cross-violation pairs, '
          f'{len(neighborhood)} cities')
    return {
        'generated_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_businesses': len(pinellas),
        'business_type_risk': business_type_risk,
        'repeat_risk': repeat_risk,
        'inspection_timing': inspection_timing,
        'cross_violations': cross_violations,
        'neighborhood': neighborhood,
    }


def main():
    print('Exporting CleanScore data...')

    records = load_prospects()
    if not records:
        print('  No prospects — aborting export')
        return

    full_narratives = load_full_narratives()
    partner_rows = load_partners()

    violations = build_violations_export(records, full_narratives)
    if violations:
        upload_to_storage('cleanscore_violations.json', violations)

    partners = build_partners_export(partner_rows)
    if partners:
        upload_to_storage('cleanscore_partners.json', partners)

    stats = build_stats_export(records, violations)
    if stats:
        upload_to_storage('cleanscore_stats.json', stats)

    os.makedirs('data', exist_ok=True)
    with open('data/cleanscore_violations.json', 'w') as f:
        json.dump(violations[:5], f, indent=2)
    print('  Sample written to data/cleanscore_violations.json')

    sources = {}
    for v in violations:
        s = v.get('narrative_source', 'synthesized')
        sources[s] = sources.get(s, 0) + 1
    source_summary = ', '.join(f'{v} {k}' for k, v in sorted(sources.items()))
    print(f'CleanScore export complete: '
          f'{len(violations)} businesses ({source_summary}), '
          f'{len(partners)} partners, {len(stats)} stat sections')


if __name__ == '__main__':
    main()
