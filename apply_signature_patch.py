#!/usr/bin/env python3
"""
Run this script from the root of the Pinellasiceco repo:
    python apply_signature_patch.py

It patches build.py in-place with two changes:
  1. Adds SIGNATURE_B64 constant above build_html()
  2. Replaces blank technician line in srGenerate() with actual signature
"""

import sys
from pathlib import Path

SIGNATURE_B64 = "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"

BUILD_PY = Path(__file__).parent / 'build.py'

if not BUILD_PY.exists():
    print(f"ERROR: build.py not found at {BUILD_PY}")
    sys.exit(1)

src = BUILD_PY.read_text(encoding='utf-8')
original = src

# ── EDIT 1: Add SIGNATURE_B64 constant above build_html() ───────────────────
OLD1 = 'def build_html(records, partners=None):'
NEW1 = f'SIGNATURE_B64 = "{SIGNATURE_B64}"\n\ndef build_html(records, partners=None):'

if OLD1 not in src:
    print("ERROR: Could not find 'def build_html' anchor. Has the file changed?")
    sys.exit(1)

if 'SIGNATURE_B64' in src:
    print("NOTE: SIGNATURE_B64 already present — skipping EDIT 1")
else:
    src = src.replace(OLD1, NEW1, 1)
    print("EDIT 1 applied: SIGNATURE_B64 constant added")

# ── EDIT 2: Replace blank sig line with image + name + title ────────────────
OLD2 = (
    '    +\'<table style="width:100%;border-collapse:collapse;margin-bottom:10px"><tr>\'\n'
    '    +\'<td style="width:48%;padding-right:14px"><div style="border-bottom:1px solid #94a3b8;height:26px;margin-bottom:3px"></div><div style="font-size:9px;color:#94a3b8">Technician Signature</div></td>\'\n'
    '    +\'<td style="width:4%"></td>\'\n'
    '    +\'<td style="width:48%;padding-left:14px"><div style="border-bottom:1px solid #94a3b8;height:26px;margin-bottom:3px"></div><div style="font-size:9px;color:#94a3b8">Date</div></td>\'\n'
    '    +\'</tr></table>\''
)

NEW2 = (
    '    +\'<table style="width:100%;border-collapse:collapse;margin-bottom:10px"><tr>\'\n'
    "    +'<td style=\"width:48%;padding-right:14px\">'\n"
    "    +'<img src=\"data:image/png;base64,'+SIGNATURE_B64+'\" alt=\"Authorized Signature\" style=\"height:60px;width:auto;max-width:220px;object-fit:contain;display:block;margin-bottom:2px\">'\n"
    "    +'<div style=\"width:180px;border-top:1px solid #0f1f38;margin-bottom:4px\"></div>'\n"
    "    +'<div style=\"font-size:11px;font-weight:700;color:#0f1f38;letter-spacing:0.02em;line-height:1.3\">John Serrantino</div>'\n"
    "    +'<div style=\"font-size:10px;color:#64748b;line-height:1.3\">Owner &#45; Pinellas Ice Co.</div>'\n"
    "    +'</td>'\n"
    '    +\'<td style="width:4%"></td>\'\n'
    '    +\'<td style="width:48%;padding-left:14px"><div style="border-bottom:1px solid #94a3b8;height:26px;margin-bottom:3px"></div><div style="font-size:9px;color:#94a3b8">Date</div></td>\'\n'
    '    +\'</tr></table>\''
)

if OLD2 not in src:
    # Try a looser match to give a useful error
    if 'Technician Signature' in src:
        print("ERROR: Found 'Technician Signature' but surrounding context didn't match exactly.")
        print("The signature table block in srGenerate() may have been edited since this patch was created.")
    else:
        print("ERROR: Could not find the technician signature block in srGenerate().")
    print("No changes written. Check build.py manually.")
    sys.exit(1)

if 'John Serrantino' in src:
    print("NOTE: Signature block already patched — skipping EDIT 2")
else:
    src = src.replace(OLD2, NEW2, 1)
    print("EDIT 2 applied: Signature image + name + title inserted")

# ── Write back only if changed ───────────────────────────────────────────────
if src == original:
    print("No changes needed — build.py already up to date.")
else:
    BUILD_PY.write_text(src, encoding='utf-8')
    print(f"\nbuild.py patched successfully.")
    print("Run: python build.py <your_csv_files>  to rebuild the tool.")
