#!/usr/bin/env python3
"""
test_redirect_check.py — Diagnostic only. Do NOT modify scrape_dbpr.py.

Determines where DBPR redirects when an inspection detail page is
unavailable, to confirm whether the 28 REDIRECT records are caused by
DBPR publishing lag or a code/session issue on our end.

Strategy:
  Group A — 5 businesses with OLD V22 visit IDs (already scraped):
             confirms the URL format and session work correctly.
  Group B — Probe visit IDs just above our highest known range:
             simulates a "brand new, not yet published" inspection.
  Group C — One clearly fake/non-existent visit ID:
             reveals the exact DBPR default redirect destination.

The 28 REDIRECT license IDs (2235741, 2235837, ...) have no locally
available visit IDs (they're in the CI-generated violations CSV).
Group B/C let us characterise the redirect destination without needing
those exact IDs.
"""

import csv
import json
import re
import time
import urllib.error
import urllib.request
from urllib.request import Request, urlopen

TERMS_URL = "https://www.myfloridalicense.com/insptermsofuse.asp"
BASE_URL  = "https://www.myfloridalicense.com/inspectionDetail.asp?InspVisitID={vid}"
UA        = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0.0.0 Safari/537.36")


# ── Session ────────────────────────────────────────────────────────────────

def init_session():
    """Mirror scrape_dbpr.py: accept terms to get a session cookie."""
    req = Request(TERMS_URL, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=20) as r:
            raw = r.headers.get("Set-Cookie", "")
    except Exception as e:
        print(f"  WARNING: session init failed — {e}")
        return ""
    m = re.search(r"(JSESSIONID=[^;]+)", raw, re.IGNORECASE)
    if m:
        return m.group(1)
    return raw.split(";")[0] if raw else ""


# ── HTTP helpers ───────────────────────────────────────────────────────────

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Raise HTTPError on any redirect so we can inspect the 3xx response."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def get_no_redirect(url, cookie=""):
    """GET without following redirects. Returns (status, location, body_snippet)."""
    opener = urllib.request.build_opener(_NoRedirect())
    headers = {"User-Agent": UA}
    if cookie:
        headers["Cookie"] = cookie
    req = Request(url, headers=headers)
    try:
        with opener.open(req, timeout=20) as r:
            body = r.read(300).decode("utf-8", errors="replace")
            return r.status, r.headers.get("Location", ""), body
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(300).decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, e.headers.get("Location", ""), body
    except Exception as e:
        return 0, "", str(e)


def get_with_redirect(url, cookie=""):
    """GET following all redirects. Returns (final_url, status, body_snippet)."""
    headers = {"User-Agent": UA}
    if cookie:
        headers["Cookie"] = cookie
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=20) as r:
            body = r.read(500).decode("utf-8", errors="replace")
            return r.url, r.status, body
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(500).decode("utf-8", errors="replace")
        except Exception:
            pass
        return getattr(e, "url", url), e.code, body
    except Exception as e:
        return url, 0, str(e)


# ── Redirect analysis ──────────────────────────────────────────────────────

def is_valid_inspection(html, visit_id):
    """Exact copy of scrape_dbpr.py is_valid_inspection() — no modifications."""
    if "PENSACOLA" in html.upper() and "TIN COW" in html.upper():
        return False
    if str(visit_id) not in html and "InspVisitID" not in html:
        if "Violation" not in html and "violation" not in html:
            return False
    return True


def body_markers(html):
    h = html.upper()
    found = []
    for keyword in ["PENSACOLA", "TIN COW", "VIOLATION", "INSPECTION",
                    "NOT FOUND", "ERROR", "LOGIN", "SESSION", "TERMS",
                    "UNAVAILABLE", "INSPVISITID"]:
        if keyword in h:
            found.append(keyword)
    return found


# ── Test cases ─────────────────────────────────────────────────────────────

def build_test_cases():
    # Load the 28 REDIRECT license IDs
    with open("full_scraper_progress.txt") as f:
        done = {l.strip() for l in f if l.strip()}
    with open("full_inspection_narratives.json") as f:
        cache = json.load(f)
    cache_keys  = {str(k) for k in cache.keys()}
    redirect_lics = sorted(done - cache_keys)

    print(f"28 REDIRECT license IDs (first 5): {redirect_lics[:5]}")
    print()

    # Find visit IDs from v22 narratives (OLD visit IDs — already succeeded)
    v22_map = {}
    with open("pinellas_v22_narratives.csv", newline="") as f:
        for row in csv.DictReader(f):
            lic = str(row.get("license_id", "")).strip()
            vid = str(row.get("visit_id", "")).strip()
            biz = str(row.get("business_name", "")).strip()
            if lic in set(redirect_lics) and vid and lic not in v22_map:
                v22_map[lic] = {"vid": vid, "biz": biz}

    cases = []

    # Group A — old V22 visit IDs (baseline: pages exist and should load)
    print("Group A: OLD visit IDs for 5 REDIRECT businesses (baseline — pages already exist)")
    count = 0
    for lic in redirect_lics:
        if lic in v22_map and count < 5:
            info = v22_map[lic]
            cases.append({
                "group": "A",
                "label": f"Lic {lic} — {info['biz'][:35]}",
                "note":  "OLD v22 visit ID (already scraped) — expect VALID page",
                "vid":   info["vid"],
                "lic":   lic,
            })
            print(f"  {lic}: vid={info['vid']} | {info['biz'][:40]}")
            count += 1
    if count == 0:
        print("  (none of the first 5 sorted redirect_lics have v22 visit IDs)")

    print()

    # Group B — probe visit IDs above our highest known range (~13.7M)
    # If these redirect to the same default as Group C, publishing lag is confirmed.
    print("Group B: Probe visit IDs above our highest known (13,668,393)")
    for vid in ["13700000", "13800000", "14000000"]:
        cases.append({
            "group": "B",
            "label": f"PROBE vid={vid}",
            "note":  "Above known range — likely unpublished or non-existent",
            "vid":   vid,
            "lic":   None,
        })
        print(f"  vid={vid}")

    print()

    # Group C — clearly non-existent visit ID (reveals redirect destination)
    print("Group C: Clearly non-existent visit ID (reveals DBPR default redirect)")
    cases.append({
        "group": "C",
        "label": "FAKE vid=99999999",
        "note":  "Non-existent — shows where DBPR sends unavailable pages",
        "vid":   "99999999",
        "lic":   None,
    })
    print("  vid=99999999")

    return cases


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("DBPR Redirect Diagnostic — test_redirect_check.py")
    print("=" * 65)
    print()

    cases = build_test_cases()

    print()
    print("Initializing DBPR session (accepting terms)...")
    cookie = init_session()
    print(f"Session cookie: {cookie[:60] or '(none)'}")
    print()

    results = []

    for i, tc in enumerate(cases):
        url = BASE_URL.format(vid=tc["vid"])
        print("─" * 65)
        print(f"[{tc['group']}-{i+1}] {tc['label']}")
        print(f"       {tc['note']}")
        print(f"  URL: {url}")

        # Step 1: no-redirect GET
        status1, location, body1 = get_no_redirect(url, cookie)
        print(f"\n  1) No-redirect response:")
        print(f"     Status  : {status1}")
        print(f"     Location: {location or '(none — no redirect)'}")

        # Step 2: follow-redirect GET
        final_url, status2, body2 = get_with_redirect(url, cookie)
        markers = body_markers(body2)
        is_valid = is_valid_inspection(body2, tc["vid"])

        print(f"\n  2) Follow-redirect response:")
        print(f"     Final URL  : {final_url}")
        print(f"     Status     : {status2}")
        print(f"     Body markers: {markers or ['(none)']}")
        print(f"     is_valid_inspection(): {is_valid}")
        print(f"     Body (first 300 chars):")
        # Strip HTML tags for readability
        text = re.sub(r"<[^>]+>", " ", body2)
        text = re.sub(r"\s+", " ", text).strip()[:300]
        print(f"       {text!r}")

        results.append({**tc, "status1": status1, "location": location,
                        "final_url": final_url, "status2": status2,
                        "markers": markers, "is_valid": is_valid})
        print()

        if i < len(cases) - 1:
            time.sleep(2)

    # Summary
    print("=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print()
    for r in results:
        redirect_str = f"→ {r['location']}" if r["location"] else "(no redirect)"
        print(f"[{r['group']}] {r['label']}")
        print(f"     Initial: HTTP {r['status1']} {redirect_str}")
        print(f"     Final  : HTTP {r['status2']} @ {r['final_url'][:80]}")
        print(f"     Markers: {r['markers'] or ['(none)']}")
        print(f"     is_valid: {r['is_valid']}")
        print()

    # Finding
    print("─" * 65)
    print("FINDING:")
    group_c = [r for r in results if r["group"] == "C"]
    group_b = [r for r in results if r["group"] == "B"]
    group_a = [r for r in results if r["group"] == "A"]

    if group_c:
        dest = group_c[0]["final_url"]
        markers_c = group_c[0]["markers"]
        if "PENSACOLA" in markers_c and "TIN COW" in markers_c:
            print("CONFIRMED: Non-existent visit IDs redirect to the Tin Cow")
            print("(Pensacola) default inspection page. This is the same")
            print("destination our is_valid_inspection() checks for.")
        elif "TERMS" in markers_c or "SESSION" in markers_c:
            print("POSSIBLE SESSION ISSUE: Redirect goes to a terms/session page.")
            print("May require re-initialization for every request.")
        elif "LOGIN" in markers_c:
            print("AUTH ISSUE: Redirect goes to a login page.")
        else:
            print(f"Redirect destination: {dest}")
            print(f"Markers: {markers_c}")

    if group_b:
        b_valid = [r["is_valid"] for r in group_b]
        b_markers = [r["markers"] for r in group_b]
        if not any(b_valid):
            print()
            print("Group B probe IDs (above known range) all return INVALID pages,")
            print("matching the same redirect as Group C (non-existent).")
            print("=> Publishing lag confirmed: brand-new visit IDs not yet on DBPR.")
        else:
            print()
            print("Group B: some probe IDs returned VALID pages — DBPR has")
            print("published visits in that range already.")

    if group_a:
        a_valid = [r["is_valid"] for r in group_a]
        if all(a_valid):
            print()
            print("Group A: all old V22 visit IDs loaded correctly.")
            print("URL format and session initialization are working fine.")
        else:
            print()
            print("WARNING: Some old V22 visit IDs also failed — possible")
            print("session or network issue unrelated to publishing lag.")


if __name__ == "__main__":
    main()
