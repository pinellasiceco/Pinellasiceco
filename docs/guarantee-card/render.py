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
    width: 1800px; height: 230px;
    background: #162844;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 72px;
    flex-shrink: 0;
    border-bottom: 3px solid #c9973a;
  }}
  .top-bar img {{
    height: 184px;
    max-width: 780px;
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
    width: 100%;
    height: auto;
    filter: brightness(0) invert(1);
    display: block;
    object-fit: contain;
  }}
  .col-left-rule {{
    width: 60px; height: 2px;
    background: #c9973a;
    margin: 26px auto;
  }}
  .col-left-why-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: #c9973a;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 16px;
  }}
  .col-left-body {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 17px;
    color: #ffffff;
    line-height: 1.8;
    text-align: center;
  }}
  .col-left-spacer {{ flex: 1; }}
  .col-left-divider {{
    width: 100%;
    height: 1px;
    background: rgba(255,255,255,0.15);
    margin-bottom: 22px;
  }}
  .col-left-phone {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 24px;
    color: #c9973a;
    text-align: center;
    margin-bottom: 8px;
  }}
  .col-left-web {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 16px;
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
    font-size: 13px;
    color: #0f1f38;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .cc-headline {{
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: 46px;
    color: #0f1f38;
    line-height: 1.1;
    margin-bottom: 10px;
  }}
  .cc-subline {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-style: italic;
    font-size: 19px;
    color: #5a6e87;
  }}
  .cc-divider {{
    height: 1px;
    background: #e0e0e0;
    margin: 28px 0;
  }}
  .cc-section-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
  }}
  .cc-section-label.green {{ color: #0a6b3c; }}
  .cc-section-label.red   {{ color: #b22a2a; }}
  .cc-item {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    font-family: 'Barlow', sans-serif;
    font-size: 18px;
    line-height: 2;
  }}
  .cc-item.good {{ font-weight: 500; color: #2d3e57; }}
  .cc-item.bad  {{ font-weight: 400; color: #5a6e87; font-size: 17px; }}
  .dot-green {{ color: #0a6b3c; font-weight: 700; flex-shrink: 0; margin-top: 2px; }}
  .dot-red   {{ color: #b22a2a; font-weight: 700; flex-shrink: 0; margin-top: 2px; }}
  .claim-box {{
    background: #f7f2ea;
    border-radius: 10px;
    padding: 26px 26px;
    border-left: 5px solid #c9973a;
    margin-top: 4px;
  }}
  .claim-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 13px;
    color: #0f1f38;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .claim-body {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-size: 17px;
    color: #2d3e57;
    line-height: 1.8;
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
  }}
  .sticker {{
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 100%;
    border-radius: 16px;
    overflow: hidden;
    border: 2px solid #c0cad8;
    box-shadow: 0 6px 24px rgba(0,0,0,0.16);
    background: #ffffff;
  }}
  .stk-logo-sect {{
    background: #ffffff;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 24px 20px 18px;
  }}
  .stk-logo-img {{
    width: 100%;
    height: auto;
    object-fit: contain;
  }}
  .stk-dark {{
    background: #2c2c2c;
    padding: 14px 16px;
    text-align: center;
  }}
  .stk-dark-text {{
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 22px;
    color: #ffffff;
    letter-spacing: 0.01em;
  }}
  .stk-body {{
    flex: 1;
    background: #ffffff;
    padding: 22px 24px 18px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }}
  .stk-field {{
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 16px;
  }}
  .stk-field-lbl {{
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 20px;
    color: #1a1a1a;
    white-space: nowrap;
  }}
  .stk-field-line {{
    flex: 1;
    border-bottom: 1.5px solid #444;
    height: 24px;
  }}
  .stk-atp-lbl {{
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    font-size: 19px;
    color: #1a1a1a;
    margin-bottom: 12px;
  }}
  .stk-ratings {{
    display: flex;
    gap: 0;
    border-radius: 8px;
    overflow: hidden;
  }}
  .stk-rating {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 18px 6px 16px;
    gap: 8px;
    text-align: center;
  }}
  .stk-rating.clean    {{ background: #1a7a3c; }}
  .stk-rating.moderate {{ background: #cc9900; }}
  .stk-rating.high     {{ background: #c0311a; }}
  .stk-rtitle {{
    font-family: 'Barlow', sans-serif;
    font-weight: 800;
    font-size: 16px;
    text-transform: uppercase;
    line-height: 1.2;
  }}
  .stk-rrange {{
    font-family: 'Barlow', sans-serif;
    font-weight: 500;
    font-size: 14px;
    line-height: 1;
  }}
  .stk-rating.clean .stk-rtitle,
  .stk-rating.clean .stk-rrange,
  .stk-rating.high  .stk-rtitle,
  .stk-rating.high  .stk-rrange  {{ color: #ffffff; }}
  .stk-rating.moderate .stk-rtitle,
  .stk-rating.moderate .stk-rrange {{ color: #1a1a1a; }}
  .stk-checkbox {{ font-size: 22px; line-height: 1; }}
  .stk-rating.clean .stk-checkbox,
  .stk-rating.high  .stk-checkbox {{ color: #ffffff; }}
  .stk-rating.moderate .stk-checkbox {{ color: #1a1a1a; }}
  .stk-call {{
    background: #f5f5f5;
    border-top: 1px solid #ddd;
    padding: 16px 16px;
    text-align: center;
  }}
  .stk-phone {{
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    font-size: 30px;
    color: #111111;
  }}
  .stk-footer {{
    border-top: 1px solid #e8e8e8;
    padding: 13px 16px;
    text-align: center;
    background: #ffffff;
  }}
  .stk-footer-text {{
    font-family: 'Barlow', sans-serif;
    font-weight: 400;
    font-style: italic;
    font-size: 17px;
    color: #1456b0;
  }}
  /* QR label */
  .cr-qr-label {{
    font-family: 'Barlow', sans-serif;
    font-weight: 500;
    font-size: 13px;
    color: #5a6e87;
    text-align: center;
    margin-top: 12px;
    letter-spacing: 0.03em;
  }}
</style>
</head>
<body>

  <!-- LEFT COLUMN -->
  <div class="col-left">
    <img class="col-left-icon" src="{LOGO}" alt="Pinellas Ice Co">
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
    <div class="cr-qr-label">PinellasIceCo.com/verify</div>

    <div class="cr-divider"></div>

    <!-- SERVICE STICKER MOCKUP -->
    <div class="sticker-wrap">
      <div class="sticker">
        <div class="stk-logo-sect">
          <img class="stk-logo-img" src="{LOGO}" alt="Pinellas Ice Co">
        </div>
        <div class="stk-dark">
          <div class="stk-dark-text">Ice Machine Serviced &amp; Sanitized</div>
        </div>
        <div class="stk-body">
          <div class="stk-field">
            <span class="stk-field-lbl">Last Service:</span>
            <div class="stk-field-line"></div>
          </div>
          <div class="stk-field">
            <span class="stk-field-lbl">Next Service:</span>
            <div class="stk-field-line"></div>
          </div>
          <div class="stk-atp-lbl">ATP Cleanliness Rating:</div>
          <div class="stk-ratings">
            <div class="stk-rating clean">
              <div class="stk-rtitle">CLEAN<br>(&lt;100)</div>
              <div class="stk-checkbox">&#x2611;</div>
            </div>
            <div class="stk-rating moderate">
              <div class="stk-rtitle">MODERATE</div>
              <div class="stk-rrange">(100&ndash;300)</div>
            </div>
            <div class="stk-rating high">
              <div class="stk-rtitle">HIGH<br>(&gt;300)</div>
              <div class="stk-checkbox">&#x2611;</div>
            </div>
          </div>
        </div>
        <div class="stk-call">
          <div class="stk-phone">Call: (727) 855-6873</div>
        </div>
        <div class="stk-footer">
          <div class="stk-footer-text">ATP Tested for Sanitation</div>
        </div>
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
