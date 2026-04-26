#!/usr/bin/env python3
"""
send_briefing.py — runs after build.py in GitHub Actions every day.
Sends a daily intelligence briefing email via Resend.
"""
import os, sys, json, csv, re
from pathlib import Path
from datetime import datetime, timedelta

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '').strip()
TO_EMAIL       = os.environ.get('BRIEFING_EMAIL', 'your@email.com').strip()
FROM_EMAIL     = 'briefing@pinellasiceco.com'

DATA_DIR = Path(__file__).parent / 'data'

def load_current():
    """Load the freshly built prospect data — prefer prospecting_tool.html (CI output), fall back to index.html."""
    for fname in ('prospecting_tool.html', 'index.html'):
        html_path = Path(__file__).parent / fname
        if not html_path.exists():
            continue
        content = html_path.read_text(encoding='utf-8')
        start = content.find('const P=') + 8
        end   = content.find(';\nconst PHONES=', start)
        if start < 8 or end < 0:
            continue
        try:
            data = json.loads(content[start:end])
            print(f'  Loaded {len(data):,} prospects from {fname}')
            return data
        except Exception as e:
            print(f'  Parse error in {fname}: {e}')
            continue
    print('  No prospect data found in prospecting_tool.html or index.html')
    return []

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
    # Save fields needed by build.py's classify_new() for tomorrow's comparison
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

def load_customers():
    """Load customer records from customers.json (written by the app's export, if present)."""
    cust_path = Path(__file__).parent / 'customers.json'
    if not cust_path.exists():
        return {}
    try:
        raw = json.loads(cust_path.read_text(encoding='utf-8'))
        if isinstance(raw, list):
            return {str(r.get('id', i)): r for i, r in enumerate(raw)}
        return raw
    except:
        return {}

def get_referral_stats(customers_data, current):
    """Summarise referral activity from customer records."""
    custs = {k: v for k, v in customers_data.items() if isinstance(v, dict)}
    total = sum(len(c.get('referrals', [])) for c in custs.values())
    top = sorted(
        [(c.get('name', '?'), len(c.get('referrals', []))) for c in custs.values() if c.get('referrals')],
        key=lambda x: x[1], reverse=True
    )[:3]
    # Clients ready to ask (30+ days, 1+ service visit, not asked in 60d)
    today_str = datetime.now().strftime('%Y-%m-%d')
    ready = []
    for p in current:
        pid = str(p.get('id'))
        c = custs.get(pid, {})
        won_date = c.get('won_date', '')
        if not won_date:
            continue
        try:
            from datetime import date
            parts = won_date.replace(',', '').split()  # "Apr 19, 2026" or "Apr 19 2026"
            won_d = datetime.strptime(' '.join(parts), '%b %d %Y').date()
            days_since = (date.today() - won_d).days
        except:
            continue
        if days_since < 30:
            continue
        if not c.get('service_history'):
            continue
        last_ask = c.get('last_referral_ask', '')
        if last_ask:
            try:
                ask_d = datetime.strptime(last_ask, '%Y-%m-%d').date()
                if (date.today() - ask_d).days < 60:
                    continue
            except:
                pass
        visits = len(c.get('service_history', []))
        ready.append((p.get('name', '?'), days_since, visits))
    ready = ready[:3]
    return total, top, ready

def compare(current, previous):
    """Find what changed since last week."""
    prev_map = {r['id']: r for r in previous}
    
    new_callbacks     = []
    new_hot           = []
    new_ice_fresh     = []
    emergency_closures = []
    score_jumpers     = []

    for r in current:
        pid = r.get('id')
        prev = prev_map.get(pid)

        # New emergency closures
        if r.get('days_until', 999) < 0 and r.get('priority') == 'CALLBACK':
            if not prev or prev.get('days_until', 999) >= 0:
                emergency_closures.append(r)

        # Newly became CALLBACK
        if r.get('priority') == 'CALLBACK':
            if not prev or prev.get('priority') != 'CALLBACK':
                new_callbacks.append(r)

        # Newly became HOT
        if r.get('priority') == 'HOT':
            if not prev or prev.get('priority') not in ('CALLBACK', 'HOT'):
                new_hot.append(r)

        # Fresh ice violation appeared
        if r.get('ice_fresh') and (not prev or not prev.get('ice_fresh')):
            new_ice_fresh.append(r)

        # Big score jump (10+ points)
        if prev:
            jump = r.get('score', 0) - prev.get('score', 0)
            if jump >= 10:
                score_jumpers.append({**r, '_jump': jump})

    return {
        'emergency_closures': sorted(emergency_closures, key=lambda x: x.get('score',0), reverse=True)[:10],
        'new_callbacks':      sorted(new_callbacks,      key=lambda x: x.get('score',0), reverse=True)[:10],
        'new_hot':            sorted(new_hot,            key=lambda x: x.get('score',0), reverse=True)[:10],
        'new_ice_fresh':      sorted(new_ice_fresh,      key=lambda x: x.get('score',0), reverse=True)[:10],
        'score_jumpers':      sorted(score_jumpers,       key=lambda x: x.get('_jump',0), reverse=True)[:5],
    }

def counts(data):
    from collections import Counter
    c = Counter(r.get('priority','') for r in data)
    phones = sum(1 for r in data if r.get('phone'))
    return {
        'total':    len(data),
        'callback': c.get('CALLBACK', 0),
        'hot':      c.get('HOT', 0),
        'warm':     c.get('WARM', 0),
        'chronic':  sum(1 for r in data if r.get('chronic')),
        'phones':   phones,
        'ice_fresh': sum(1 for r in data if r.get('ice_fresh')),
    }

def biz_row(r, extra=''):
    phone = r.get('phone','')
    phone_html = f'<a href="tel:{phone}" style="color:#0a84ff">{phone}</a>' if phone else '<span style="color:#94a3b8">No phone</span>'
    score = r.get('score', 0)
    score_col = '#dc2626' if score >= 80 else '#d97706' if score >= 60 else '#64748b'
    last_insp = r.get('last_insp', '')
    try:
        from datetime import date as _d
        insp_fmt = _d.fromisoformat(last_insp).strftime('%b %-d')
    except Exception:
        insp_fmt = last_insp or '—'
    return f"""
    <tr style="border-bottom:1px solid #f1f5f9">
      <td style="padding:8px 12px;font-weight:600;color:#1e293b">{r.get('name','')[:35]}</td>
      <td style="padding:8px 12px;color:#64748b;font-size:11px">{r.get('city','')}</td>
      <td style="padding:8px 12px">{phone_html}</td>
      <td style="padding:8px 12px;font-weight:700;color:{score_col};font-size:12px">{score}</td>
      <td style="padding:8px 12px;font-size:11px;color:#64748b">{insp_fmt}</td>
      {f'<td style="padding:8px 12px;font-size:11px;color:#64748b">{extra}</td>' if extra else ''}
    </tr>"""

def build_email(current, changes, stats, ref_total=0, ref_top=None, ref_ready=None):
    today = datetime.now().strftime('%A, %B %-d, %Y')
    has_changes = any(len(v) > 0 for v in changes.values())
    ref_top = ref_top or []
    ref_ready = ref_ready or []

    sections = ''

    # New Since Yesterday
    _nsy_labels = {
        'new_callback':       '🆕 New CALLBACK',
        'new_ice_violation':  '🆕 New Ice Viol.',
        'priority_escalated': '🆕 Escalated',
        'score_jump':         '🆕 Score ↑',
        'new_to_dataset':     '🆕 New Business',
    }
    new_since = sorted(
        [r for r in current if r.get('new_reason')],
        key=lambda x: ({'CALLBACK':0,'HOT':1,'WARM':2,'WATCH':3,'LATER':4}.get(x.get('priority',''), 4),
                       -x.get('score', 0))
    )[:8]
    if new_since:
        rows = ''.join(biz_row(r, _nsy_labels.get(r.get('new_reason',''), '🆕 New')) for r in new_since)
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#854d0e;margin-bottom:8px">
            &#x1F195; New Since Yesterday ({len(new_since)})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef9c3"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Last Insp.</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#854d0e">Reason</th></tr>
            {rows}
          </table>
        </div>"""
    else:
        sections += """
        <div style="background:#f0fdf4;border:1px solid #6ee7b7;border-radius:8px;padding:12px 16px;margin-bottom:16px">
          <div style="font-size:12px;font-weight:700;color:#059669">&#x2713; No new escalations since yesterday</div>
        </div>"""

    # Emergency closures
    if changes['emergency_closures']:
        rows = ''.join(biz_row(r) for r in changes['emergency_closures'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#dc2626;margin-bottom:8px">
            &#x1F6A8; Emergency Closures / Overdue Callbacks ({len(changes['emergency_closures'])})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef2f2"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#dc2626">Last Insp.</th></tr>
            {rows}
          </table>
        </div>"""

    # New callbacks
    if changes['new_callbacks']:
        rows = ''.join(biz_row(r) for r in changes['new_callbacks'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#1e3a5f;margin-bottom:8px">
            &#x1F4DE; New CALLBACK Businesses This Week ({len(changes['new_callbacks'])})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#f0f4ff"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#1e3a5f">Last Insp.</th></tr>
            {rows}
          </table>
        </div>"""

    # Fresh ice violations
    if changes['new_ice_fresh']:
        rows = ''.join(biz_row(r) for r in changes['new_ice_fresh'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#0a84ff;margin-bottom:8px">
            &#x1F9CA; New Ice Violations (Last 6 Months) ({len(changes['new_ice_fresh'])})
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#eff6ff"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#0a84ff">Last Insp.</th></tr>
            {rows}
          </table>
        </div>"""

    # Score jumpers
    if changes['score_jumpers']:
        rows = ''.join(biz_row(r, f"+{r.get('_jump',0)} pts") for r in changes['score_jumpers'])
        sections += f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#d97706;margin-bottom:8px">
            &#x1F4C8; Biggest Score Jumps This Week
          </div>
          <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden">
            <tr style="background:#fef9ee"><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Business</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">City</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Phone</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Score</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Last Insp.</th><th style="padding:8px 12px;text-align:left;font-size:11px;color:#d97706">Change</th></tr>
            {rows}
          </table>
        </div>"""

    if not has_changes:
        sections = """
        <div style="background:#f0fdf4;border:1px solid #6ee7b7;border-radius:8px;padding:16px;text-align:center;margin-bottom:24px">
          <div style="font-size:14px;font-weight:700;color:#059669">&#x2713; No major changes this week</div>
          <div style="font-size:11px;color:#064e3b;margin-top:4px">Territory is stable. Focus on working your existing pipeline.</div>
        </div>"""

    # Referral pipeline section (only shown if there is any referral activity)
    ref_section = ''
    if ref_total > 0 or ref_ready:
        ref_rows = ''.join(
            f'<tr><td style="padding:6px 12px;font-size:11px;color:#1e293b">{name}</td>'
            f'<td style="padding:6px 12px;font-size:11px;font-weight:700;color:#7c3aed">{cnt} referral{"s" if cnt>1 else ""}</td></tr>'
            for name, cnt in ref_top
        )
        ready_rows = ''.join(
            f'<tr><td style="padding:4px 12px;font-size:11px;color:#1e293b">{name}</td>'
            f'<td style="padding:4px 12px;font-size:10px;color:#64748b">{days}d client &bull; {visits} visit{"s" if visits!=1 else ""}</td></tr>'
            for name, days, visits in ref_ready
        )
        ref_section = f"""
        <div style="margin-bottom:24px">
          <div style="font-size:13px;font-weight:800;color:#7c3aed;margin-bottom:8px">&#x1F49C; Referral Pipeline</div>
          <div style="background:#faf5ff;border:1px solid #ddd8f5;border-radius:8px;padding:12px 16px">
            <div style="font-size:11px;color:#5b21b6;margin-bottom:8px">Total referred clients: <strong>{ref_total}</strong></div>
            {f'<table style="width:100%;border-collapse:collapse;margin-bottom:8px">{ref_rows}</table>' if ref_rows else ''}
            {f'<div style="font-size:11px;color:#5b21b6;font-weight:700;margin-top:8px">Clients ready to ask ({len(ref_ready)}):</div><table style="width:100%;border-collapse:collapse">{ready_rows}</table>' if ready_rows else ''}
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:600px;margin:0 auto;padding:20px">

    <!-- Header -->
    <div style="background:#1e3a5f;border-radius:12px 12px 0 0;padding:20px 24px;margin-bottom:0">
      <div style="font-size:11px;color:rgba(255,255,255,.6);margin-bottom:2px">PINELLAS ICE CO</div>
      <div style="font-size:20px;font-weight:800;color:#fff">&#x1F4CB; Daily Intelligence Briefing</div>
      <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:4px">{today}</div>
    </div>

    <!-- Stats strip -->
    <div style="background:#162d4a;border-radius:0;padding:12px 24px;display:flex;gap:24px;flex-wrap:wrap">
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#7dd3fc">{stats['total']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">Total Prospects</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#f87171">{stats['callback']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">CALLBACK</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#fb923c">{stats['hot']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">HOT</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#34d399">{stats['phones']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">With Phone</div></div>
      <div style="text-align:center"><div style="font-size:22px;font-weight:800;color:#a78bfa">{stats['ice_fresh']:,}</div><div style="font-size:10px;color:rgba(255,255,255,.6)">Fresh Ice Viol.</div></div>
    </div>

    <!-- Body -->
    <div style="background:#f8fafc;padding:20px 24px;border-radius:0 0 12px 12px">
      {sections}
      {ref_section}

      <!-- Open app CTA -->
      <div style="text-align:center;padding:16px 0">
        <a href="https://pinellasiceco.github.io/Pinellasiceco"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;font-size:13px">
          &#x1F4F1; Open Prospect Tool
        </a>
      </div>

      <!-- Footer -->
      <div style="text-align:center;font-size:10px;color:#94a3b8;border-top:1px solid #e2e8f0;padding-top:12px">
        Pinellas Ice Co &bull; Data refreshed from FL DBPR &bull; pinellasiceco.com<br>
        This email is sent automatically every day after the daily data rebuild.
      </div>
    </div>
  </div>
</body>
</html>"""

    subject = f"PIC Briefing {datetime.now().strftime('%b %-d')} — "
    if changes['emergency_closures']:
        subject += f"🚨 {len(changes['emergency_closures'])} closures, "
    if changes['new_callbacks']:
        subject += f"{len(changes['new_callbacks'])} new callbacks, "
    if changes['new_ice_fresh']:
        subject += f"{len(changes['new_ice_fresh'])} fresh ice viol."
    subject = subject.rstrip(', ')
    if subject.endswith('—'):
        subject += ' No major changes'

    return subject, html

def send_email(subject, html):
    import urllib.request, urllib.parse
    payload = json.dumps({
        'from': FROM_EMAIL,
        'to':   [TO_EMAIL],
        'subject': subject,
        'html': html,
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
        data = json.loads(resp.read())
        print(f"  Email sent: {data.get('id','OK')}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"  Email HTTP error {e.code}: {repr(body)}")
        print(f"  Headers: {dict(e.headers)}")
        raise
    except Exception as e:
        print(f"  Email failed: {e}")
        raise

def main():
    print('\nSending daily briefing email...')
    print(f'  FROM: {FROM_EMAIL}')
    print(f'  TO:   {TO_EMAIL[:12]}... (len={len(TO_EMAIL)})')
    print(f'  KEY:  {"set (" + RESEND_API_KEY[:8] + "...)" if RESEND_API_KEY else "NOT SET"}')

    if not RESEND_API_KEY:
        print('  ERROR: RESEND_API_KEY secret is not set in GitHub repo settings.')
        raise SystemExit(1)

    if TO_EMAIL == 'your@email.com':
        print('  ERROR: BRIEFING_EMAIL secret is not set — still using placeholder.')
        raise SystemExit(1)

    current  = load_current()
    previous = load_previous()

    if not current:
        print('  No prospect data found — skipping email')
        return

    print(f'  Loaded {len(current):,} current prospects, {len(previous):,} previous')

    changes = compare(current, previous)
    stats   = counts(current)
    customers_data = load_customers()
    ref_total, ref_top, ref_ready = get_referral_stats(customers_data, current)

    print(f"  Changes: {len(changes['emergency_closures'])} closures, {len(changes['new_callbacks'])} callbacks, {len(changes['new_ice_fresh'])} ice viol.")
    print(f"  Referrals: {ref_total} total, {len(ref_ready)} clients ready to ask")

    subject, html = build_email(current, changes, stats, ref_total, ref_top, ref_ready)
    print(f'  Subject: {subject}')

    send_email(subject, html)
    save_snapshot(current)
    print('  Snapshot saved for next week comparison')

if __name__ == '__main__':
    main()
