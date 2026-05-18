#!/usr/bin/env python3
"""
Pinellas Ice Co — Daily Briefing Email
Simple status email: data freshness + action counts.
Sends once per day from rebuild.yml after CI completes.
Cron in send_briefing.yml is a fallback only.
"""

import os
import json
import re
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import requests

ET = ZoneInfo('America/New_York')

# ── Config ──────────────────────────────────────────────
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
BRIEFING_EMAIL = os.environ.get('BRIEFING_EMAIL', '')
SUPABASE_URL   = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY   = os.environ.get('SUPABASE_SERVICE_KEY', '')

# ── Data helpers ─────────────────────────────────────────

def get_data_freshness():
    csv_path = 'data/3fdinspi_current.csv'
    if not os.path.exists(csv_path):
        return None, None
    try:
        import pandas as pd
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            df = pd.read_csv(csv_path, header=None, low_memory=False)
        df[14] = pd.to_datetime(df[14], errors='coerce')
        max_date = df[14].max()
        if hasattr(max_date, 'date'):
            max_date = max_date.date()
        if not max_date:
            return None, None
        lag = (date.today() - max_date).days
        return max_date.strftime('%b %d'), lag
    except Exception as e:
        print(f'  Freshness error: {e}')
        return None, None


def load_prospects():
    """Load P[] records from built index.html."""
    if not os.path.exists('index.html'):
        return []
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        # Find P= start, then locate the closing ];\nconst
        start = re.search(r'const P\s*=\s*\[', html)
        if not start:
            return []
        bracket_start = start.end() - 1  # position of opening [
        # Walk forward counting brackets to find matching ]
        depth = 0
        i = bracket_start
        for i in range(bracket_start, len(html)):
            if html[i] == '[':
                depth += 1
            elif html[i] == ']':
                depth -= 1
                if depth == 0:
                    break
        array_str = html[bracket_start:i + 1]
        return json.loads(array_str)
    except Exception as e:
        print(f'  Prospects load error: {e}')
        return []


def load_supabase_table(table):
    """Load all rows from a Supabase table via REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        url = f'{SUPABASE_URL}/rest/v1/{table}?select=*'
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f'  Supabase {table}: {r.status_code}')
        return []
    except Exception as e:
        print(f'  Supabase {table} error: {e}')
        return []


def count_fresh_citations(records):
    cutoff = date.today() - timedelta(days=3)
    count = 0
    for r in records:
        if not r.get('ice_confirmed'):
            continue
        if 'customer' in str(r.get('status', '')):
            continue
        cit = r.get('cit_latest_date', '') or ''
        try:
            if date.fromisoformat(str(cit)[:10]) >= cutoff:
                count += 1
        except Exception:
            continue
    return count


def count_unclaimed(records, contacted_ids):
    cutoff_old  = date.today() - timedelta(days=30)
    cutoff_new  = date.today() - timedelta(days=3)
    count = 0
    for r in records:
        if not r.get('ice_confirmed'):
            continue
        if r.get('id') in contacted_ids:
            continue
        if 'customer' in str(r.get('status', '')):
            continue
        cit = r.get('cit_latest_date', '') or ''
        try:
            d = date.fromisoformat(str(cit)[:10])
            if d >= cutoff_new:   # too fresh (in Fresh Citations)
                continue
            if d < cutoff_old:    # too old
                continue
            count += 1
        except Exception:
            continue
    return count


def count_overdue(log_rows, records):
    today = date.today()
    client_ids = {
        r.get('id') for r in records
        if 'customer' in str(r.get('status', ''))
    }
    latest = {}
    for row in log_rows:
        pid = row.get('prospect_id')
        if not pid:
            continue
        data = row.get('data') or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                continue
        entries = data if isinstance(data, list) else []
        if entries:
            latest[pid] = entries[-1]

    count = 0
    for pid, entry in latest.items():
        if pid in client_ids:
            continue
        followup = (entry.get('followup') or '').strip()
        if not followup:
            continue
        try:
            if date.fromisoformat(followup[:10]) < today:
                count += 1
        except Exception:
            continue
    return count


def count_nudges_due(log_rows, cust_rows, records):
    today = date.today()
    client_ids = {
        r.get('id') for r in records
        if 'customer' in str(r.get('status', ''))
    }
    contacted_ids = {
        row.get('prospect_id') for row in log_rows
        if row.get('prospect_id')
    }

    custs = {}
    for row in cust_rows:
        pid = row.get('prospect_id')
        if not pid:
            continue
        data = row.get('data') or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                continue
        custs[pid] = data

    count = 0
    phones = {r.get('id'): r.get('phone', '') for r in records}

    for r in records:
        pid = r.get('id')
        if not pid or pid in client_ids or pid not in contacted_ids:
            continue
        c = custs.get(pid, {})
        if c.get('nudge_dismissed'):
            continue
        if not (c.get('dm_phone') or phones.get(pid, '')):
            continue
        last_nudge = (c.get('last_nudge_date') or '').strip()
        if last_nudge:
            try:
                if (today - date.fromisoformat(last_nudge[:10])).days < 7:
                    continue
            except Exception:
                pass
        count += 1

    return min(count, 99)


def count_retests_due(cust_rows, records):
    today = date.today()
    client_ids = {
        r.get('id') for r in records
        if 'customer' in str(r.get('status', ''))
    }
    cutoff_early = today - timedelta(days=7)
    cutoff_late  = today + timedelta(days=7)

    count = 0
    for row in cust_rows:
        pid = row.get('prospect_id')
        if not pid or pid in client_ids:
            continue
        data = row.get('data') or {}
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                continue
        if data.get('retest_done'):
            continue
        sched = (data.get('retest_scheduled') or '').strip()
        if not sched:
            continue
        try:
            d = date.fromisoformat(sched[:10])
            if cutoff_early <= d <= cutoff_late:
                count += 1
        except Exception:
            continue
    return count


# ── Email builder ─────────────────────────────────────────

def build_email(insp_date, lag, n_prospects, n_fresh,
                n_unclaimed, n_overdue, n_nudges, n_retests):

    now_et    = datetime.now(ET)
    today_str = now_et.strftime('%a %b %d, %Y')
    time_str  = now_et.strftime('%I:%M %p ET')

    # Subject
    if lag is not None and lag > 5:
        subject = (f'⚠️ PIC Daily — {now_et.strftime("%a %b %d")}'
                   f' · DATA STALE ({lag} days)')
    elif insp_date:
        subject = (f'PIC Daily — {now_et.strftime("%a %b %d")}'
                   f' · Data: {insp_date}'
                   + (f' ({lag}d)' if lag is not None else ''))
    else:
        subject = f'PIC Daily — {now_et.strftime("%a %b %d")}'

    # Stale data banner
    stale_warning = ''
    if lag is not None and lag > 5:
        stale_warning = (
            '<div style="background:#fef3c7;border:1px solid #f59e0b;'
            'border-radius:6px;padding:10px 14px;margin-bottom:16px;'
            'font-size:13px;color:#92400e;font-weight:600">'
            f'⚠️ Data is {lag} days old — DBPR may have an issue'
            '</div>'
        )

    # Action rows — only non-zero items shown
    action_rows = []
    if n_fresh > 0:
        action_rows.append(
            '<tr>'
            '<td style="padding:4px 0;color:#dc2626;font-weight:700">'
            '\U0001f6a8 Fresh citations</td>'
            f'<td style="padding:4px 0;text-align:right;font-weight:700;color:#dc2626">{n_fresh}</td>'
            '</tr>'
        )
    if n_unclaimed > 0:
        action_rows.append(
            '<tr>'
            '<td style="padding:4px 0;color:#475569">'
            '\U0001f4cb Unclaimed citations</td>'
            f'<td style="padding:4px 0;text-align:right;font-weight:600">{n_unclaimed}</td>'
            '</tr>'
        )
    if n_overdue > 0:
        action_rows.append(
            '<tr>'
            '<td style="padding:4px 0;color:#475569">'
            '⏰ Overdue follow-ups</td>'
            f'<td style="padding:4px 0;text-align:right;font-weight:600">{n_overdue}</td>'
            '</tr>'
        )
    if n_nudges > 0:
        action_rows.append(
            '<tr>'
            '<td style="padding:4px 0;color:#475569">'
            '\U0001f4f1 Nudges due</td>'
            f'<td style="padding:4px 0;text-align:right;font-weight:600">{n_nudges}</td>'
            '</tr>'
        )
    if n_retests > 0:
        action_rows.append(
            '<tr>'
            '<td style="padding:4px 0;color:#475569">'
            '\U0001f52c Re-tests due</td>'
            f'<td style="padding:4px 0;text-align:right;font-weight:600">{n_retests}</td>'
            '</tr>'
        )

    if action_rows:
        action_block = (
            '<table style="width:100%;font-size:14px;border-collapse:collapse">'
            + ''.join(action_rows)
            + '</table>'
        )
    else:
        action_block = (
            '<div style="color:#94a3b8;font-size:13px;padding:8px 0">'
            'No urgent items — all clear'
            '</div>'
        )

    lag_label = f'({lag} days ago)' if lag is not None else ''

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f8fafc;
font-family:-apple-system,BlinkMacSystemFont,sans-serif">
<div style="max-width:480px;margin:0 auto;padding:20px 16px">

  <div style="background:#0f1f38;border-radius:10px;
  padding:16px 20px;margin-bottom:16px">
    <div style="color:#fff;font-size:16px;font-weight:700">
      Pinellas Ice Co
    </div>
    <div style="color:#94a3b8;font-size:12px;margin-top:2px">
      {today_str} &middot; {time_str}
    </div>
  </div>

  {stale_warning}

  <div style="background:#fff;border:1px solid #e2e8f0;
  border-radius:10px;padding:14px 16px;margin-bottom:12px">
    <div style="font-size:11px;font-weight:700;color:#94a3b8;
    text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">
      Data Status
    </div>
    <div style="font-size:13px;color:#475569">
      Last inspection:
      <strong style="color:#1e293b">
        {insp_date or 'Unknown'} {lag_label}
      </strong>
    </div>
    <div style="font-size:13px;color:#475569;margin-top:4px">
      Prospects loaded:
      <strong style="color:#1e293b">{n_prospects:,}</strong>
    </div>
  </div>

  <div style="background:#fff;border:1px solid #e2e8f0;
  border-radius:10px;padding:14px 16px;margin-bottom:16px">
    <div style="font-size:11px;font-weight:700;color:#94a3b8;
    text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">
      Today
    </div>
    {action_block}
  </div>

  <a href="https://pinellasiceco.github.io/Pinellasiceco"
  style="display:block;background:#0f1f38;color:#fff;
  text-align:center;padding:14px;border-radius:10px;
  text-decoration:none;font-size:14px;font-weight:600">
    Open App &rarr;
  </a>

</div>
</body>
</html>'''

    return subject, html


# ── Send ─────────────────────────────────────────────────

def send_email(subject, html):
    if not RESEND_API_KEY or not BRIEFING_EMAIL:
        print('  Missing RESEND_API_KEY or BRIEFING_EMAIL — skipping send')
        return False
    try:
        r = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'from': 'PIC Briefing <briefing@pinellasiceco.com>',
                'to': [BRIEFING_EMAIL],
                'subject': subject,
                'html': html,
            },
            timeout=15,
        )
        if r.status_code in (200, 201):
            print(f'  Email sent: {r.json().get("id", "?")}')
            return True
        print(f'  Email failed: {r.status_code} {r.text[:200]}')
        return False
    except Exception as e:
        print(f'  Email error: {e}')
        return False


# ── Main ─────────────────────────────────────────────────

def main():
    print('Sending daily briefing email...')
    print(f'  Secrets: RESEND={"set" if RESEND_API_KEY else "MISSING"}'
          f'  EMAIL={"set" if BRIEFING_EMAIL else "MISSING"}'
          f'  SUPABASE={"set" if SUPABASE_URL and SUPABASE_KEY else "MISSING"}')

    insp_date, lag = get_data_freshness()
    print(f'  Inspection: {insp_date} ({lag}d lag)' if insp_date
          else '  Inspection: unknown')

    records = load_prospects()
    print(f'  Prospects loaded: {len(records):,}')

    log_rows  = load_supabase_table('pic_log')
    cust_rows = load_supabase_table('pic_customers')
    print(f'  Log rows: {len(log_rows)}  Customer rows: {len(cust_rows)}')

    contacted_ids = {
        row.get('prospect_id') for row in log_rows
        if row.get('prospect_id')
    }

    n_fresh     = count_fresh_citations(records)
    n_unclaimed = count_unclaimed(records, contacted_ids)
    n_overdue   = count_overdue(log_rows, records)
    n_nudges    = count_nudges_due(log_rows, cust_rows, records)
    n_retests   = count_retests_due(cust_rows, records)

    print(f'  Fresh={n_fresh} Unclaimed={n_unclaimed} '
          f'Overdue={n_overdue} Nudges={n_nudges} Retests={n_retests}')

    subject, html = build_email(
        insp_date, lag, len(records),
        n_fresh, n_unclaimed, n_overdue, n_nudges, n_retests,
    )
    print(f'  Subject: {subject}')
    send_email(subject, html)
    print('Done.')


if __name__ == '__main__':
    main()
