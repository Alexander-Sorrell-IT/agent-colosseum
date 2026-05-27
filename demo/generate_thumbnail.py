#!/usr/bin/env python3
"""Generate DevPost thumbnail — avatar-led hero image for Agent Colosseum.

3:2 (1200x800). Leads with 4 Perfect-Corp-generated model avatars, then title,
sponsor tags, and final verified stats. Avatars are base64-embedded so this is
a single self-contained PNG with no external requests.
"""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

DEMO_DIR = Path(__file__).resolve().parent
OUTPUT = DEMO_DIR / "thumbnail.png"
AVATARS = DEMO_DIR / "model_avatars"

# Pick 4 visually distinctive avatars — the four most representative characters.
PICKS = [
    ("nemotron_super", "Nemotron Super 120B", "#76B900"),
    ("deepseek",       "DeepSeek V4 Pro",     "#1E3A8A"),
    ("llama",          "Llama 3.3 70B",       "#F97316"),
    ("qwen",           "Qwen3 235B",          "#10B981"),
]

def data_url(p: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()

avatar_cards = "".join(
    f"""
    <div class="avatar">
      <img src="{data_url(AVATARS / (f + '.jpg'))}" alt="{name}"/>
      <div class="avatar-name" style="color:{color}">{name}</div>
    </div>
    """ for (f, name, color) in PICKS
)

HTML = f"""<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:1200px; height:800px;
  background:
    radial-gradient(ellipse at top left, rgba(118,185,0,0.20), transparent 50%),
    radial-gradient(ellipse at bottom right, rgba(0,188,212,0.18), transparent 50%),
    linear-gradient(135deg,#06070f 0%,#0a0a1a 40%,#10081d 100%);
  font-family:'Segoe UI', system-ui, sans-serif;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding:48px; overflow:hidden;
}}
.header {{ text-align:center; margin-bottom:28px; }}
h1 {{
  font-size:72px; font-weight:900; line-height:1;
  background: linear-gradient(135deg,#76B900 0%,#00BCD4 50%,#E91E63 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  letter-spacing:-1.5px;
}}
.subtitle {{
  font-size:22px; color:#c0c0d8; font-weight:300; margin-top:8px;
  max-width:1000px;
}}
.avatars {{
  display:flex; gap:20px; justify-content:center; margin: 8px 0 28px;
}}
.avatar {{
  width:180px; text-align:center;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius:16px;
  padding:12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}
.avatar img {{
  width:156px; height:156px; object-fit:cover;
  border-radius:12px;
  display:block;
}}
.avatar-name {{
  margin-top:10px; font-weight:700; font-size:14px; letter-spacing:0.3px;
}}
.tags {{
  display:flex; gap:14px; justify-content:center; flex-wrap:wrap;
  margin-bottom:24px;
}}
.tag {{
  padding:8px 18px; border-radius:24px; font-size:14px; font-weight:600;
  letter-spacing:0.4px;
}}
.tag-crusoe   {{ background:rgba(255,107,0,0.18); color:#FFB066; border:1px solid rgba(255,107,0,0.45); }}
.tag-pcorp    {{ background:rgba(233,30,99,0.18); color:#F48FB1; border:1px solid rgba(233,30,99,0.45); }}
.tag-lark     {{ background:rgba(108,92,231,0.18); color:#B0A4F5; border:1px solid rgba(108,92,231,0.45); }}
.tag-tf       {{ background:rgba(0,188,212,0.18); color:#7FE3F0; border:1px solid rgba(0,188,212,0.45); }}
.stats {{
  display:flex; gap:48px; justify-content:center;
}}
.stat {{ text-align:center; }}
.stat-value {{ font-size:34px; font-weight:800; color:#fff; line-height:1; }}
.stat-label {{ font-size:12px; color:#8888aa; text-transform:uppercase;
               letter-spacing:1.4px; margin-top:6px; }}
.footer {{ margin-top:22px; font-size:13px; color:#666680;
           letter-spacing:0.6px; }}
</style></head><body>
  <div class="header">
    <h1>Agent Colosseum</h1>
    <div class="subtitle">7 Crusoe models. 7 Perfect-Corp-generated faces. One Nemotron-orchestrated arena.</div>
  </div>
  <div class="avatars">
    {avatar_cards}
  </div>
  <div class="tags">
    <span class="tag tag-crusoe">CRUSOE &middot; NEMOTRON SUPER-120B</span>
    <span class="tag tag-pcorp">PERFECT CORP YCE</span>
    <span class="tag tag-lark">LARK CI</span>
    <span class="tag tag-tf">TRUEFOUNDRY CHAOS</span>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-value">100% A+</div><div class="stat-label">Gatekeeper · 24/24</div></div>
    <div class="stat"><div class="stat-value">7</div><div class="stat-label">Live Models</div></div>
    <div class="stat"><div class="stat-value">5</div><div class="stat-label">Lark Workflows Live</div></div>
    <div class="stat"><div class="stat-value">0</div><div class="stat-label">Anomalies · 5 Sims</div></div>
  </div>
  <div class="footer">DevNetwork AI+ML Hackathon 2026 &middot; Solo Entry &middot; Four-Sponsor Verified</div>
</body></html>"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.set_content(HTML)
    page.screenshot(path=str(OUTPUT), type="png", full_page=False, clip={"x":0,"y":0,"width":1200,"height":800})
    browser.close()

print(f"Thumbnail saved: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
