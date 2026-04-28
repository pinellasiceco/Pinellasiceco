#!/usr/bin/env python3
"""
send_briefing.py — runs after build.py in GitHub Actions every day.
Sends a daily intelligence briefing email via Resend.
"""
import os, sys, json, re
from pathlib import Path
from datetime import datetime, timedelta

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '').strip()
TO_EMAIL       = os.environ.get('BRIEFING_EMAIL', '').strip()
SUPABASE_URL   = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY   = os.environ.get('SUPABASE_KEY', '').strip()
FROM_EMAIL     = 'briefing@pinellasiceco.com'

DATA_DIR = Path(__file__).parent / 'data'


def validate_secrets():
    if not RESEND_API_KEY:
        print('ERROR: RESEND_API_KEY secret is not set')
        sys.exit(1)
    if not RESEND_API_KEY.startswith('re_'):
        print(f"ERROR: RESEND_API_KEY looks wrong — expected re_... got: {RESEND_API_KEY[:10]}...")
        sys.exit(1)
    if not TO_EMAIL or '@' not in TO_EMAIL:
        print(f"ERROR: BRIEFING_EMAIL missing or invalid: '{TO_EMAIL}'")
        sys.exit(1)
    print(f'  Secrets OK — sending to {TO_EMAIL}')


def load_current():
    """Load the freshly built prospect data from index.html."""
    html_path = Path(__file__).parent / 'index.html'
    if not html_path.exists():
        print('ERROR: index.html not found')
        sys.exit(1)
    content = html_path.read_text(encoding='utf-8')
    start = content.find('const P=') + 8
    end   = content.find(';\nconst PHONES=', start)
    if start < 8 or end < 0:
        print('ERROR: Could not find prospect data array in index.html — build may have failed')
        sys.exit(1)
    try:
        data = json.loads(content[start:end])
        print(f'  Loaded {len(data):,} prospects from index.html')
        return data
    except Exception as e:
        print(f'ERROR: Failed to parse prospect data: {e}')
        sys.exit(1)


def load_previous():
    """Load last week's snapshot for comparison."""
    snap = DATA_DIR / 'snapshot_prev.json'
    if not snap.exists():
        return []
    try:
        return json.loads(snap.read_text(encoding='utf-8'))
    except:
        return []


def save_snapshot(data):
    """Save this week's data as next week's comparison baseline."""
    DATA_DIR.mkdir(exist_ok=True)
    snap = DATA_DIR / 'snapshot_prev.json'
    lite = [{
        'id':          r.get('id'),
        'score':       r.get('score', 0),
        'priority':    r.get('priority', ''),
        'days_until':  r.get('days_until', 999),
        'ice_fresh':   r.get('ice_fresh', False),
        'n_callbacks': r.get('n_callbacks', 0),
        'ice_count':   r.get('ice_count', 0),
        'last_insp':   r.get('last_insp', ''),
    } for r in data]
    snap.write_text(json.dumps(lite), encoding='utf-8')


def get_contacted_ids():
    """Fetch IDs of already-contacted prospects from Supabase. Fails open."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return set()
    try:
        import urllib.request
        url = f"{SUPABASE_URL}/rest/v1/pic_briefing_export?limit=1&order=exported_at.desc"
        req = urllib.request.Request(url, headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
        })
        resp = urllib.request.urlopen(req, timeout=10)
        rows = json.loads(resp.read())
        if rows:
            ids = set(str(x) for x in rows[0].get('contacted_ids', []))
            print(f'  Filtered {len(ids)} already-contacted prospects from cold sections')
            return ids
    except Exception as e:
        print(f'  Warning: could not fetch contacted IDs from Supabase ({e}) — showing all prospects')
    return set()


def compare(current, previous):
    """Find what changed since last week."""
    prev_map = {r['id']: r for r in previous}

    new_callbacks      = []
    new_hot            = []
    new_ice_fresh      = []
    emergency_closures = []
    score_jumpers      = []

    for r in current:
        pid  = r.get('id')
        prev = prev_map.get(pid)

        if r.get('days_until', 999) < 0 and r.get('priority') == 'CALLBACK':
            if not prev or prev.get('days_until', 999) >= 0:
                emergency_closures.append(r)

        if r.get('priority') == 'CALLBACK':
            if not prev or prev.get('priority') != 'CALLBACK':
                new_callbacks.append(r)

        if r.get('priority') == 'HOT':
            if not prev or prev.get('priority') not in ('CALLBACK', 'HOT'):
                new_hot.append(r)

        if r.get('ice_fresh') and (not prev or not prev.get('ice_fresh')):
            new_ice_fresh.append(r)

        if prev:
            jump = r.get('score', 0) - prev.get('score', 0)
            if jump >= 10:
                score_jumpers.append({**r, '_jump': jump})

    return {
        'emergency_closures': sorted(emergency_closures, key=lambda x: x.get('score', 0), reverse=True)[:10],
        'new_callbacks':      sorted(new_callbacks,      key=lambda x: x.get('score', 0), reverse=True)[:10],
        'new_hot':            sorted(new_hot,            key=lambda x: x.get('score', 0), reverse=True)[:10],
        'new_ice_fresh':      sorted(new_ice_fresh,      key=lambda x: x.get('score', 0), reverse=True)[:10],
        'score_jumpers':      sorted(score_jumpers,       key=lambda x: x.get('_jump', 0), reverse=True)[:5],
    }


def counts(data):
    from collections import Counter
    c = Counter(r.get('priority', '') for r in data)
    phones = sum(1 for r in data if r.get('phone'))
    return {
        'total':     len(data),
        'callback':  c.get('CALLBACK', 0),
        'hot':       c.get('HOT', 0),
        'warm':      c.get('WARM', 0),
        'chronic':   sum(1 for r in data if r.get('chronic')),
        'phones':    phones,
        'ice_fresh': sum(1 for r in data if r.get('ice_fresh')),
    }


def biz_row(r, extra=''):
    phone = r.get('phone', '')
    phone_html = f'<a href="tel:{phone}" style="color:#0a84ff">{phone}</a>' if phone else '<span style="color:#94a3b8">No phone</span>'
    score = r.get('score', 0)
    score_col = '#dc2626' if score >= 80 else '#d97706' if score >= 60 else '#64748b'
    return f"""
    <tr style="border-bottom:1px solid #f1f5f9">
      <td style="padding:8px 12px;font-weight:600;color:#1e293b">{r.get('name','')[:35]}</td>
      <td style="padding:8px 12px;color:#64748b;font-size:11px">{r.get('city','')}</td>
      <td style="padding:8px 12px">{phone_html}</td>
      <td style="padding:8px 12px;font-weight:700;color:{score_col};font-size:12px">{score}</td>
      {f'<td style="padding:8px 12px;font-size:11px;color:#64748b">{extra}</td>' if extra else ''}
    </tr>"""


def build_email(current, changes, stats, contacted_ids):
    today = datetime.now().strftime('%A, %B %-d, %Y')
    has_changes = any(len(v) > 0 for v in changes.values())

    sections = ''

    _nsy_labels = {
        'new_callback':       '\U0001f195 New CALLBACK',
        'new_ice_violation':  '\U0001f195 New Ice Viol.',
        'priority_escalated': '\U0001f195 Escalated',
        'score_jump':         '\U0001f195 Score ↑',
        'new_to_dataset':     '\U0001f195 New Business',
    }
    new_since = sorted(
        [r for r in current if r.get('new_reason')],
        key=lambda x: ({'CALLBACK': 0, 'HOT': 1, 'WARM': 2, 'WATCH': 3, 'LATER': 4}.get(x.get('priority', ''), 4),
                       -x.get('score', 0))
    )[:8]
    if new_since:
        rows = ''.join(biz_row(r, _nsy_labels.get(r.get('new_reason', ''), '\U0001f195 New')) for r in new_since)
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#854d0e;margin-bottom:8px">
            &#x1F195; New Since Yesterday ({len(new_since)})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef9c3"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Reason</th></tr>
            {rows}
          </table>
        </div>"""
    else:
        sections += """
        <div style="background:#f0fdf4;border:1px solid #6ee7b7;border-radius:8px;padding:12px 16px;margin-bottom:16px">
          <div style="font-size:12px;font-weight:700;color:#059669">&#x2713; No new escalations since yesterday</div>
        </div>"""

    if changes['emergency_closures']:
        rows = ''.join(biz_row(r) for r in changes['emergency_closures'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#dc2626;margin-bottom:8px">
            &#x1F6A8; Emergency Closures / Overdue Callbacks ({len(changes['emergency_closures'])})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef2f2"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Score</th></tr>
            {rows}
          </table>
        </div>"""

    if changes['new_callbacks']:
        filtered = [r for r in changes['new_callbacks'] if str(r.get('id','')) not in contacted_ids]
        if filtered:
            rows = ''.join(biz_row(r) for r in filtered)
            sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#1e3a5f;margin-bottom:8px">
            &#x1F4DE; New CALLBACK Businesses ({len(filtered)})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#f0f4ff"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Score</th></tr>
            {rows}
          </table>
        </div>"""

    if changes['new_ice_fresh']:
        filtered = [r for r in changes['new_ice_fresh'] if str(r.get('id','')) not in contacted_ids]
        if filtered:
            rows = ''.join(biz_row(r) for r in filtered)
            sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#0a84ff;margin-bottom:8px">
            &#x1F9CA; New Ice Violations (Last 6 Months) ({len(filtered)})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#eff6ff"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Score</th></tr>
            {rows}
          </table>
        </div>"""

    if changes['score_jumpers']:
        rows = ''.join(biz_row(r, f"+{r.get('_jump',0)} pts") for r in changes['score_jumpers'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#d97706;margin-bottom:8px">
            &#x1F4C8; Biggest Score Jumps
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef9ee"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Change</th></tr>
            {rows}
          </table>
        </div>"""

    if not has_changes:
        sections = """
        <div style="background:#f0fdf4;border:1px solid #6ee7b7;border-radius:8px;padding:16px;text-align:center;margin-bottom:24px">
          <div style="font-size:14px;font-weight:700;color:#059669">&#x2713; No major changes today</div>
          <div style="font-size:11px;color:#064e3b;margin-top:4px">Territory is stable. Focus on working your existing pipeline.</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:600px;margin:0 auto;padding:20px">

    <div style="background:#1e3a5f;border-radius:12px 12px 0 0;padding:20px 24px;margin-bottom:0">
      <div style="font-size:11px;color:rgba(255,255,255,.6);margin-bottom:2px">PINELLAS ICE CO</div>
      <div style="font-size:20px;font-weight:800;color:#fff">&#x1F4CB; Daily Intelligence Briefing</div>
      <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:4px">{today}</div>
    </div>

    <div style="background:#162d4a;border-radius:0;padding:12px 24px;display:flex;gap:24px;flex-wrap:wrap">
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#7dd3fc">{stats['total']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">Total Prospects</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#f87171">{stats['callback']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">CALLBACK</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#fb923c">{stats['hot']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">HOT</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#34d399">{stats['phones']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">With Phone</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#a78bfa">{stats['ice_fresh']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">Fresh Ice Viol.</div></div>
    </div>

    <div style="background:#f8fafc;padding:20px 24px;border-radius:0 0 12px 12px">
      {sections}

      <div style="text-align:center;padding:16px 0">
        <a href="https://pinellasiceco.github.io/Pinellasiceco"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;font-size:13px">
          &#x1F4F1; Open Prospect Tool
        </a>
      </div>

      <div style="text-align:center;font-size:10px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:12px">
        Pinellas Ice Co &bull; Data refreshed from FL DBPR &bull; pinellasiceco.com<br>
        Sent automatically after the daily data rebuild.
      </div>
    </div>
  </div>
</body>
</html>"""

    subject = f"PIC Briefing {datetime.now().strftime('%b %-d')} — "
    if changes['emergency_closures']:
        subject += f"\U0001f6a8 {len(changes['emergency_closures'])} closures, "
    if changes['new_callbacks']:
        subject += f"{len(changes['new_callbacks'])} new callbacks, "
    if changes['new_ice_fresh']:
        subject += f"{len(changes['new_ice_fresh'])} fresh ice viol."
    subject = subject.rstrip(', ')
    if subject.endswith('—'):
        subject += ' No major changes'

    return subject, html


def send_email(subject, html):
    import urllib.request
    payload = json.dumps({
        'from':    FROM_EMAIL,
        'to':      [TO_EMAIL],
        'subject': subject,
        'html':    html,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        method='POST',
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type':  'application/json',
            'User-Agent':    'PIC-Briefing/1.0',
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode('utf-8')
        data = json.loads(body)
        print(f'  Email sent: {data.get("id", "OK")}')
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f'  Email failed: HTTP {e.code} — {body}')
        return False
    except Exception as e:
        print(f'  Email error: {e}')
        return False


def main():
    print('\nSending daily briefing email...')
    validate_secrets()

    current  = load_current()
    previous = load_previous()
    print(f'  Previous snapshot: {len(previous):,} records')

    contacted_ids = get_contacted_ids()
    changes = compare(current, previous)
    stats   = counts(current)

    print(f"  Changes: {len(changes['emergency_closures'])} closures, {len(changes['new_callbacks'])} new callbacks, {len(changes['new_ice_fresh'])} fresh ice viol.")

    subject, html = build_email(current, changes, stats, contacted_ids)
    print(f'  Subject: {subject}')

    ok = send_email(subject, html)
    if not ok:
        print('FAILED: email did not send')
        sys.exit(1)

    save_snapshot(current)
    print('  Snapshot saved')
    print('Done.')


if __name__ == '__main__':
    main()
