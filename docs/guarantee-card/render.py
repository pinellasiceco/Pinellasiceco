#!/usr/bin/env python3
"""
Pinellas Ice Co — Guarantee Card Renderer
Outputs front.png + back.png at 1800×1200px via Playwright/Chromium.
Run from repo root or from docs/guarantee-card/.
"""

import asyncio, base64, os, sys
from pathlib import Path

# ── Resolve paths relative to repo root ──────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent.parent
OUT_DIR     = SCRIPT_DIR

def b64(rel_path: str, mime: str) -> str:
    p = REPO_ROOT / rel_path
    if not p.exists():
        raise FileNotFoundError(f"Asset not found: {p}")
    with open(p, 'rb') as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

LOGO = b64('IMG_0110.png',  'image/png')    # Full wordmark logo
ICON = b64('IMG_0037.jpeg', 'image/jpeg')   # Ice cube icon only
QR   = b64('IMG_0738.jpeg', 'image/jpeg')   # QR code → explore page

# ── Fonts ─────────────────────────────────────────────────────────────────────
GFONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:ital,wght@0,700;0,900;1,700;1,900"
    "&family=Barlow+Condensed:wght@600;700;800"
    "&family=Barlow:wght@300;400;500;600;700"
    "&display=swap"
)


# ── FRONT HTML ────────────────────────────────────────────────────────────────
def make_front() -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{GFONTS}" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width: 1800px; height: 1200px;
    overflow: hidden;
    background: #0f1f38;
    font-family: 'Barlow', sans-serif;
    display: flex;
    flex-direction: column;
  }}

  /* TOP BAR — tall enough for a real logo */
  .top-bar {{
    width: 1800px; height: 196px;
    background: #162844;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 72px;
    flex-shrink: 0;
    border-bottom: 3px solid #c9973a;
  }}
  .top-bar img {{
    height: 148px;
    max-width: 700px;
    object-fit: contain;
    object-position: left center;
    filter: brightness(0) invert(1);
    display: block;
  }}
  .top-bar-right {{
    text-align: right;
    flex-shrink: 0;
  }}
  .top-bar-url {{
    font-family: 'Barlow', sans-serif;
    font-weight: 500;
    font-size: 22px;
    color: #c9973a;
    letter-spacing: 0.04em;
    display: block;
  }}
  .top-bar-sub {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 15px;
    color: rgba(255,255,255,0.45);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 6px;
    display: block;
  }}

  /* HERO — fills the space between bars */
  .hero {{
    flex: 1;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 28px 100px 20px;
    text-align: center;
    overflow: hidden;
  }}
  /* Faint watermark logo fills background */
  .hero-watermark {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 860px;
    opacity: 0.04;
    filter: brightness(0) invert(1);
    pointer-events: none;
  }}
  .headline-number {{
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: 268px;
    color: #c9973a;
    line-height: 0.9;
    letter-spacing: -0.03em;
    position: relative;
  }}
  .headline-desc {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 106px;
    color: #ffffff;
    letter-spacing: 6px;
    line-height: 1;
    margin-top: 4px;
    text-transform: uppercase;
    position: relative;
  }}
  .headline-guarantee {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 76px;
    color: #c9973a;
    letter-spacing: 14px;
    line-height: 1;
    margin-top: 10px;
    text-transform: uppercase;
    position: relative;
  }}
  .gold-rule {{
    width: 560px;
    height: 3px;
    background: #c9973a;
    margin: 26px auto;
    border-radius: 2px;
    position: relative;
  }}
  .promise-line1 {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 28px;
    color: rgba(255,255,255,0.88);
    line-height: 1.5;
    position: relative;
  }}
  .promise-line2 {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 34px;
    color: #ffffff;
    line-height: 1.4;
    margin-top: 6px;
    position: relative;
  }}

  /* FOOTER */
  .footer-bar {{
    width: 1800px; height: 86px;
    background: #c9973a;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    flex-shrink: 0;
  }}
  .footer-phone {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 40px;
    color: #0f1f38;
    padding: 0 64px 0 72px;
    letter-spacing: 0.03em;
  }}
  .footer-rule {{
    width: 2px; height: 44px;
    background: rgba(15,31,56,0.35);
    flex-shrink: 0;
  }}
  .footer-tagline {{
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 20px;
    color: #0f1f38;
    padding: 0 72px 0 64px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}
</style>
</head>
<body>

  <!-- TOP BAR — large logo -->
  <div class="top-bar">
    <img src="{LOGO}" alt="Pinellas Ice Co">
    <div class="top-bar-right">
      <span class="top-bar-url">PinellasIceCo.com</span>
      <span class="top-bar-sub">Licensed &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; ATP Certified</span>
    </div>
  </div>

  <!-- HERO -->
  <div class="hero">
    <img class="hero-watermark" src="{LOGO}" alt="">
    <div class="headline-number">30-DAY</div>
    <div class="headline-desc">INSPECTION PROTECTION</div>
    <div class="headline-guarantee">GUARANTEE</div>
    <div class="gold-rule"></div>
    <div class="promise-line1">
      If your ice machine fails a health inspection within 30 days of our service &mdash;
    </div>
    <div class="promise-line2">we refund you in full.</div>
  </div>

  <!-- FOOTER -->
  <div class="footer-bar">
    <span class="footer-phone">(727) 855-6873</span>
    <div class="footer-rule"></div>
    <span class="footer-tagline">Local &nbsp;&middot;&nbsp; Insured &nbsp;&middot;&nbsp; Professional</span>
  </div>

</body>
</html>"""


# ── BACK HTML ─────────────────────────────────────────────────────────────────
def make_back() -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{GFONTS}" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{
    width: 1800px; height: 1200px;
    overflow: hidden;
    font-family: 'Barlow', sans-serif;
    display: flex;
  }}

  /* LEFT COLUMN */
  .col-left {{
    width: 480px;
    height: 1200px;
    background: #0f1f38;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 52px 44px;
    flex-shrink: 0;
  }}
  .col-left-icon {{
    width: 88px; height: 88px;
    filter: brightness(0) invert(1);
    display: block;
    object-fit: contain;
  }}
  .col-left-name {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 28px;
    color: #ffffff;
    text-align: center;
    line-height: 1.15;
    margin-top: 20px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }}
  .col-left-rule {{
    width: 60px; height: 2px;
    background: #c9973a;
    margin: 20px auto;
  }}
  .col-left-why-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    color: #c9973a;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 14px;
  }}
  .col-left-body {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: #ffffff;
    line-height: 1.75;
    text-align: center;
  }}
  .col-left-spacer {{ flex: 1; }}
  .col-left-divider {{
    width: 100%;
    height: 1px;
    background: rgba(255,255,255,0.15);
    margin-bottom: 20px;
  }}
  .col-left-phone {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 20px;
    color: #c9973a;
    text-align: center;
    margin-bottom: 6px;
  }}
  .col-left-web {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: rgba(255,255,255,0.7);
    text-align: center;
  }}

  /* CENTER COLUMN */
  .col-center {{
    flex: 1;
    height: 1200px;
    background: #ffffff;
    padding: 52px 52px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .cc-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    color: #0f1f38;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .cc-headline {{
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: 34px;
    color: #0f1f38;
    line-height: 1.15;
    margin-bottom: 6px;
  }}
  .cc-subline {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-style: italic;
    font-size: 15px;
    color: #5a6e87;
  }}
  .cc-divider {{
    height: 1px;
    background: #e0e0e0;
    margin: 20px 0;
  }}
  .cc-section-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .cc-section-label.green {{ color: #0a6b3c; }}
  .cc-section-label.red   {{ color: #b22a2a; }}
  .cc-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-family: 'Barlow', sans-serif;
    font-size: 14px;
    line-height: 1.8;
  }}
  .cc-item.good {{ font-weight: 500; color: #2d3e57; }}
  .cc-item.bad  {{ font-weight: 400; color: #5a6e87; font-size: 13px; }}
  .dot-green {{ color: #0a6b3c; font-weight: 700; flex-shrink: 0; margin-top: 1px; }}
  .dot-red   {{ color: #b22a2a; font-weight: 700; flex-shrink: 0; margin-top: 1px; }}
  .claim-box {{
    background: #f7f2ea;
    border-radius: 8px;
    padding: 20px 20px;
    border-left: 4px solid #c9973a;
  }}
  .claim-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    color: #0f1f38;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .claim-body {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 13px;
    color: #2d3e57;
    line-height: 1.7;
  }}

  /* RIGHT COLUMN */
  .col-right {{
    width: 480px;
    height: 1200px;
    background: #f7f2ea;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 52px 44px;
    flex-shrink: 0;
  }}
  .cr-scan-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    color: #0f1f38;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 18px;
  }}
  .cr-qr {{
    width: 200px; height: 200px;
    background: #ffffff;
    padding: 8px;
    border-radius: 4px;
    display: block;
    object-fit: contain;
  }}
  .cr-qr-sub {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 12px;
    color: #5a6e87;
    text-align: center;
    margin-top: 10px;
  }}
  .cr-divider {{
    width: 100%;
    height: 1px;
    background: #d0d0d0;
    margin: 28px 0;
  }}
  /* SERVICE STICKER MOCKUP */
  .sticker-wrap {{
    width: 100%;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}
  .sticker {{
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
    border: 2px solid #b8c4d8;
    box-shadow: 0 6px 20px rgba(0,0,0,0.14);
  }}
  .sticker-header {{
    background: #1e3a6e;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 22px;
  }}
  .sticker-icon {{
    width: 60px; height: 60px;
    object-fit: contain;
    filter: brightness(0) invert(1);
    flex-shrink: 0;
  }}
  .sticker-company {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 28px;
    color: #ffffff;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    line-height: 1.1;
  }}
  .sticker-subheader {{
    background: #2d3748;
    color: #ffffff;
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 15px;
    text-align: center;
    padding: 11px 12px;
    letter-spacing: 0.03em;
  }}
  .sticker-body {{
    background: #ffffff;
    padding: 20px 22px 16px;
  }}
  .sticker-field {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 13px;
    color: #2d3e57;
    border-bottom: 1.5px solid #b0b8c8;
    padding-bottom: 5px;
    margin-bottom: 13px;
  }}
  .sticker-field strong {{
    font-weight: 700;
  }}
  .sticker-atp-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    color: #0f1f38;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .sticker-ratings {{
    display: flex;
    gap: 6px;
    margin-bottom: 18px;
  }}
  .sticker-rating {{
    flex: 1;
    border-radius: 5px;
    padding: 9px 4px;
    text-align: center;
  }}
  .sticker-rating.clean    {{ background: #d4edda; border: 1.5px solid #28a745; }}
  .sticker-rating.moderate {{ background: #fff3cd; border: 1.5px solid #ffc107; }}
  .sticker-rating.high     {{ background: #f8d7da; border: 1.5px solid #dc3545; }}
  .sticker-rating-name {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .clean    .sticker-rating-name {{ color: #155724; }}
  .moderate .sticker-rating-name {{ color: #856404; }}
  .high     .sticker-rating-name {{ color: #721c24; }}
  .sticker-rating-range {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 10px;
    margin-top: 2px;
  }}
  .clean    .sticker-rating-range {{ color: #155724; }}
  .moderate .sticker-rating-range {{ color: #856404; }}
  .high     .sticker-rating-range {{ color: #721c24; }}
  .sticker-phone {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 21px;
    color: #0f1f38;
    text-align: center;
    letter-spacing: 0.04em;
  }}
  .sticker-phone-pre {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: #0f1f38;
    text-align: center;
    margin-bottom: 2px;
  }}
  .sticker-footer {{
    background: #1e3a6e;
    color: #ffffff;
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 12px;
    text-align: center;
    padding: 9px 8px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }}
</style>
</head>
<body>

  <!-- LEFT COLUMN -->
  <div class="col-left">
    <img class="col-left-icon" src="{ICON}" alt="Pinellas Ice Co icon">
    <div class="col-left-name">PINELLAS<br>ICE CO.</div>
    <div class="col-left-rule"></div>
    <div class="col-left-why-label">WHY WE CAN OFFER THIS</div>
    <div class="col-left-body">
      Every machine we clean is ATP-tested<br>
      with a professional luminometer<br>
      before and after service.<br><br>
      You receive a timestamped compliance<br>
      report documenting your reading.<br><br>
      We stand behind that number.
    </div>
    <div class="col-left-spacer"></div>
    <div class="col-left-divider"></div>
    <div class="col-left-phone">(727) 855-6873</div>
    <div class="col-left-web">PinellasIceCo.com</div>
  </div>

  <!-- CENTER COLUMN -->
  <div class="col-center">
    <div class="cc-label">THE PINELLAS ICE CO.</div>
    <div class="cc-headline">Inspection Protection Guarantee</div>
    <div class="cc-subline">What&rsquo;s covered. What&rsquo;s not. How to claim.</div>

    <div class="cc-divider"></div>

    <div class="cc-section-label green">&#x2713; WHAT THIS COVERS</div>
    <div class="cc-item good">
      <span class="dot-green">&#x25CF;</span>
      <span>Any DBPR V22 citation for ice machine contamination, mold, biofilm, or scale</span>
    </div>
    <div class="cc-item good">
      <span class="dot-green">&#x25CF;</span>
      <span>Issued within 30 days of your most recent Pinellas Ice Co service visit</span>
    </div>
    <div class="cc-item good">
      <span class="dot-green">&#x25CF;</span>
      <span>At the location we serviced</span>
    </div>

    <div class="cc-divider"></div>

    <div class="cc-section-label red">&#x2715; WHAT THIS DOESN&rsquo;T COVER</div>
    <div class="cc-item bad">
      <span class="dot-red">&#x25CF;</span>
      <span>Citations unrelated to ice machine cleanliness</span>
    </div>
    <div class="cc-item bad">
      <span class="dot-red">&#x25CF;</span>
      <span>Locations we haven&rsquo;t serviced</span>
    </div>
    <div class="cc-item bad">
      <span class="dot-red">&#x25CF;</span>
      <span>Machines tampered with or modified after our visit</span>
    </div>

    <div class="cc-divider"></div>

    <div class="claim-box">
      <div class="claim-label">HOW TO CLAIM</div>
      <div class="claim-body">
        Contact us within 7 days of the citation. Send a photo of the
        inspection report to (727) 855-6873 and we&rsquo;ll process your refund
        immediately. No questions asked.
      </div>
    </div>
  </div>

  <!-- RIGHT COLUMN -->
  <div class="col-right">
    <div class="cr-scan-label">SCAN TO VERIFY</div>
    <img class="cr-qr" src="{QR}" alt="QR code">
    <div class="cr-qr-sub">This location&rsquo;s certification</div>

    <div class="cr-divider"></div>

    <!-- SERVICE STICKER MOCKUP -->
    <div class="sticker-wrap">
      <div class="sticker">
        <div class="sticker-header">
          <img class="sticker-icon" src="{ICON}" alt="">
          <div class="sticker-company">PINELLAS<br>ICE CO.</div>
        </div>
        <div class="sticker-subheader">Ice Machine Serviced &amp; Sanitized</div>
        <div class="sticker-body">
          <div class="sticker-field"><strong>Last Service:</strong> _______________</div>
          <div class="sticker-field"><strong>Next Service:</strong> _______________</div>
          <div class="sticker-atp-label">ATP Cleanliness Rating:</div>
          <div class="sticker-ratings">
            <div class="sticker-rating clean">
              <div class="sticker-rating-name">&#x2713; CLEAN</div>
              <div class="sticker-rating-range">&lt;100</div>
            </div>
            <div class="sticker-rating moderate">
              <div class="sticker-rating-name">MODERATE</div>
              <div class="sticker-rating-range">100&ndash;300</div>
            </div>
            <div class="sticker-rating high">
              <div class="sticker-rating-name">HIGH</div>
              <div class="sticker-rating-range">&gt;300</div>
            </div>
          </div>
          <div class="sticker-phone-pre">Call:</div>
          <div class="sticker-phone">(727) 855-6873</div>
        </div>
        <div class="sticker-footer">ATP Tested for Sanitation</div>
      </div>
    </div>
  </div>

</body>
</html>"""


# ── PREVIEW PAGE ──────────────────────────────────────────────────────────────
def make_preview() -> str:
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Guarantee Card Preview — Pinellas Ice Co</title>
<style>
  body {
    margin: 0; padding: 48px;
    background: #f0f0f0;
    font-family: -apple-system, sans-serif;
    text-align: center;
  }
  h1 { font-size: 22px; color: #0f1f38; margin-bottom: 6px; }
  .note { font-size: 14px; color: #666; margin-bottom: 40px; }
  .card-wrap { margin-bottom: 48px; }
  .card-label { font-size: 13px; font-weight: 700; color: #444; margin-bottom: 10px; letter-spacing: .05em; text-transform: uppercase; }
  img.card { width: 900px; height: 600px; display: block; margin: 0 auto; border-radius: 6px; box-shadow: 0 4px 24px rgba(0,0,0,.18); }
  .back-link { display: inline-block; margin-top: 32px; font-size: 14px; color: #0f1f38; text-decoration: none; border-bottom: 1px solid #c9973a; padding-bottom: 2px; }
</style>
</head>
<body>
  <h1>Guarantee Card &mdash; Pinellas Ice Co</h1>
  <div class="note">Matte 4&times;6 &nbsp;&middot;&nbsp; Upload both files to VistaPrint.com</div>

  <div class="card-wrap">
    <div class="card-label">FRONT &mdash; VistaPrint ready (1800&times;1200px)</div>
    <img class="card" src="front.png" alt="Front">
  </div>

  <div class="card-wrap">
    <div class="card-label">BACK &mdash; VistaPrint ready (1800&times;1200px)</div>
    <img class="card" src="back.png" alt="Back">
  </div>

  <a class="back-link" href="../explore/">&#x2190; Back to Explore</a>
</body>
</html>"""


# ── RENDER ────────────────────────────────────────────────────────────────────
async def render(html: str, out_path: str):
    from playwright.async_api import async_playwright
    CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROMIUM)
        page = await browser.new_page(viewport={'width': 1800, 'height': 1200})
        await page.set_content(html, wait_until='networkidle')
        await page.wait_for_timeout(3000)   # font load buffer
        await page.screenshot(
            path=out_path,
            clip={'x': 0, 'y': 0, 'width': 1800, 'height': 1200}
        )
        await browser.close()


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    front_html = make_front()
    back_html  = make_back()

    print("Rendering front...")
    await render(front_html, str(OUT_DIR / 'front.png'))
    print("Rendering back...")
    await render(back_html,  str(OUT_DIR / 'back.png'))

    (OUT_DIR / 'index.html').write_text(make_preview())
    print("Written index.html")

    from PIL import Image
    for fname in ['front.png', 'back.png']:
        img = Image.open(OUT_DIR / fname)
        assert img.size == (1800, 1200), f"Wrong size: {img.size}"
        print(f"  {fname}: {img.size} ✓")

    print("\nDone. Files in docs/guarantee-card/")


if __name__ == '__main__':
    asyncio.run(main())
