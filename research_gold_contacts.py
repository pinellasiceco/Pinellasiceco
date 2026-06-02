"""
research_gold_contacts.py — Find Owner/GM contacts for all Gold lead accounts.

Run with ANTHROPIC_API_KEY set:
    ANTHROPIC_API_KEY=sk-ant-... python3 research_gold_contacts.py

Writes output to docs/data/gold_contacts.json.
"""
import json
import re
import time
import os

import anthropic

# ── Extract gold leads from built index.html ──────────────────────────────────
html = open('index.html').read()

# Use bracket-counting to extract P[] — regex fails on the large 9000+ record array
idx = html.find('const P=[')
if idx == -1:
    idx = html.find('var P=[')
if idx == -1:
    print('ERROR: P[] not found in index.html')
    exit(1)

start = idx + html[idx:].index('[')
depth = 0
end = start
for i, ch in enumerate(html[start:], start):
    if ch == '[':
        depth += 1
    elif ch == ']':
        depth -= 1
        if depth == 0:
            end = i + 1
            break

prospects = json.loads(html[start:end])
gold = [
    p for p in prospects
    if p.get('ice_gold') == True
]
print(f'Found {len(gold)} Gold leads')

# ── API client ────────────────────────────────────────────────────────────────
client = anthropic.Anthropic()


def find_contact(business_name, city):
    prompt = (
        f"Find the Owner, General Manager, or Bar Manager at "
        f"{business_name} in {city}, Florida.\n\n"
        "These are independent restaurants, bars, cafes, and food service "
        "businesses — not large hotels. Look for the current business owner, "
        "operator, or general manager by name.\n\n"
        "Return ONLY a valid JSON object, no other text:\n"
        '{"name": "Full Name", "title": "Exact Title"}\n\n'
        "If you cannot find a specific named person, return exactly:\n"
        '{"name": null, "title": null}\n\n'
        "Do not include explanations, markdown, or any text outside the JSON object."
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text += block.text

        text = text.strip()
        text = re.sub(r'```json|```', '', text).strip()

        result = json.loads(text)

        name = result.get('name')
        title = result.get('title')

        reject_names = ['full name', 'name here', 'unknown', 'n/a', 'none']
        if name and name.lower() in reject_names:
            name = None
        if title and title.lower() in ['exact title', 'title here', 'unknown']:
            title = None

        return {'name': name, 'title': title}

    except (json.JSONDecodeError, Exception):
        return {'name': None, 'title': None}


# ── Load existing contacts to enable resume ───────────────────────────────────
output_path = 'docs/data/gold_contacts.json'
os.makedirs('docs/data', exist_ok=True)

existing = {}
if os.path.exists(output_path):
    try:
        with open(output_path) as f:
            existing = json.load(f)
        found_existing = sum(1 for v in existing.values() if v.get('dm_name'))
        print(f'Loaded {len(existing)} existing entries ({found_existing} with '
              f'contacts) — will skip these')
    except Exception:
        existing = {}

contacts = dict(existing)

# ── Main research loop ────────────────────────────────────────────────────────
found = 0
not_found = 0
skipped = 0

for i, p in enumerate(gold):
    pid = str(p.get('id') or p.get('pid') or i)

    # Skip only if we already have a confirmed contact name
    if pid in existing and existing[pid].get('dm_name'):
        contacts[pid] = existing[pid]
        skipped += 1
        continue

    name = p.get('name', 'Unknown')
    city = p.get('city', 'Pinellas County')

    print(f'[{i+1}/{len(gold)}] {name[:50]} — {city}')

    result = find_contact(name, city)

    contacts[pid] = {
        'business_name': name,
        'city': city,
        'dm_name': result['name'],
        'dm_title': result['title']
    }

    if result['name']:
        found += 1
        print(f'  FOUND: {result["name"]} ({result["title"]})')
    else:
        not_found += 1
        print(f'  NOT FOUND')

    # Save progress every 50 accounts
    if (i + 1) % 50 == 0:
        with open(output_path, 'w') as f:
            json.dump(contacts, f, indent=2)
        print(f'  [checkpoint saved at {i+1} accounts]')

    time.sleep(0.5)

# ── Final write and summary ───────────────────────────────────────────────────
with open(output_path, 'w') as f:
    json.dump(contacts, f, indent=2)

total = found + not_found
found_pct = (found / total * 100) if total else 0

print(f'\nDone.')
print(f'Skipped (already done): {skipped}')
print(f'Found:     {found} ({found_pct:.0f}%)')
print(f'Not found: {not_found}')
print(f'Total entries: {len(contacts)}')
print(f'Saved to:  {output_path}')

if found_pct < 10:
    print('\nWARNING: Found rate below 10% — check API output above for errors.')
elif found_pct >= 30:
    print('\nQuality looks good (>= 30% found rate). Proceed to commit.')
