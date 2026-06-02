"""
research_contacts.py — Find decision maker contacts for all Premium accounts.

Run with ANTHROPIC_API_KEY set:
    ANTHROPIC_API_KEY=sk-ant-... python3 research_contacts.py

Writes output to docs/data/strategic_contacts.json.
Delete this script after a successful run — do not commit it.
"""
import json
import re
import time
import os

import anthropic

# ── Extract premium accounts from built index.html ────────────────────────────
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
premium = [
    p for p in prospects
    if (p.get('premium_score') or 0) >= 4
]
print(f'Found {len(premium)} Premium accounts')

# ── API client ────────────────────────────────────────────────────────────────
client = anthropic.Anthropic()


def find_contact(business_name, city, score):
    """
    Find the most appropriate decision maker for this business.
    Priority order:
      - Score >= 7: Director of Engineering or Chief Engineer first,
                    then F&B Director, then General Manager
      - Score 4-6:  General Manager or Owner first,
                    then Bar Manager or Restaurant Manager

    Returns dict with name and title, or {name: None, title: None}.
    """
    if score >= 7:
        role_priority = (
            "Director of Engineering, Chief Engineer, "
            "Director of Food and Beverage, or General Manager"
        )
    else:
        role_priority = (
            "Owner, General Manager, Bar Manager, "
            "or Restaurant Manager"
        )

    prompt = (
        f"Find the {role_priority} at {business_name} in {city}, Florida.\n\n"
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

        # Extract text from response content blocks
        text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                text += block.text

        text = text.strip()

        # Parse JSON — handle markdown fences
        text = re.sub(r'```json|```', '', text).strip()

        result = json.loads(text)

        name = result.get('name')
        title = result.get('title')

        # Reject placeholder values
        reject_names = ['full name', 'name here', 'unknown', 'n/a', 'none']
        if name and name.lower() in reject_names:
            name = None
        if title and title.lower() in ['exact title', 'title here', 'unknown']:
            title = None

        return {'name': name, 'title': title}

    except (json.JSONDecodeError, Exception):
        return {'name': None, 'title': None}


# ── Load existing output so a crashed run can resume ─────────────────────────
output_path = 'docs/data/strategic_contacts.json'
os.makedirs('docs/data', exist_ok=True)

if os.path.exists(output_path):
    with open(output_path) as f:
        contacts = json.load(f)
    print(f'Loaded {len(contacts)} existing entries (resuming)')
else:
    contacts = {}

# ── Main research loop ────────────────────────────────────────────────────────
found = 0
not_found = 0

for i, p in enumerate(premium):
    pid = str(p.get('id') or p.get('pid') or str(i))
    name = p.get('name', 'Unknown')
    city = p.get('city', 'Pinellas County')
    score = p.get('premium_score', 0)

    # Skip if already researched in a previous run
    existing = contacts.get(pid, {})
    if existing.get('dm_name') is not None or existing.get('_researched'):
        if existing.get('dm_name'):
            found += 1
        else:
            not_found += 1
        continue

    print(f'[{i+1}/{len(premium)}] {name[:50]} — {city}')

    result = find_contact(name, city, score)

    contacts[pid] = {
        'business_name': name,
        'city': city,
        'premium_score': score,
        'dm_name': result['name'],
        'dm_title': result['title'],
        '_researched': True
    }

    if result['name']:
        found += 1
        print(f'  FOUND: {result["name"]} ({result["title"]})')
    else:
        not_found += 1
        print(f'  NOT FOUND')

    # Save incrementally so a crash loses at most one record
    with open(output_path, 'w') as f:
        json.dump(contacts, f, indent=2)

    # Rate limit
    time.sleep(0.5)

# ── Final write and summary ───────────────────────────────────────────────────
# Strip internal _researched flags from output
for entry in contacts.values():
    entry.pop('_researched', None)

with open(output_path, 'w') as f:
    json.dump(contacts, f, indent=2)

total = found + not_found
found_pct = (found / total * 100) if total else 0

print(f'\nDone.')
print(f'Found:     {found} ({found_pct:.0f}%)')
print(f'Not found: {not_found}')
print(f'Total:     {len(contacts)}')
print(f'Saved to:  {output_path}')

if found_pct < 30:
    print('\nWARNING: Found rate below 30% — check API output above for errors.')
elif found_pct >= 70:
    print('\nQuality looks good (>= 70% found rate). Proceed to commit.')
