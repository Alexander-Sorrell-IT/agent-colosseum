#!/usr/bin/env python3
"""Generate DevPost thumbnail — 3:2 ratio hero image for Agent Colosseum."""
from playwright.sync_api import sync_playwright
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
OUTPUT = DEMO_DIR / "thumbnail.png"

HTML = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1200px; height: 800px;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0a1a2e 100%);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Segoe UI', system-ui, sans-serif;
  overflow: hidden;
}
.card {
  text-align: center;
  padding: 60px 80px;
  border: 2px solid rgba(118, 185, 0, 0.3);
  border-radius: 24px;
  background: rgba(10, 10, 30, 0.85);
  box-shadow: 0 0 80px rgba(118, 185, 0, 0.15), 0 0 200px rgba(0, 150, 255, 0.08);
}
h1 {
  font-size: 72px; font-weight: 900;
  background: linear-gradient(135deg, #76B900 0%, #4CAF50 50%, #00BCD4 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}
.colosseum-icon { font-size: 80px; margin-bottom: 16px; }
.subtitle {
  font-size: 28px; color: #b0b0d0; font-weight: 300;
  margin-bottom: 32px;
}
.tags {
  display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 40px;
}
.tag {
  padding: 8px 20px; border-radius: 20px;
  font-size: 16px; font-weight: 600;
}
.tag-crusoe { background: rgba(255, 107, 0, 0.2); color: #FF6B00; border: 1px solid rgba(255, 107, 0, 0.4); }
.tag-nemotron { background: rgba(118, 185, 0, 0.2); color: #76B900; border: 1px solid rgba(118, 185, 0, 0.4); }
.tag-models { background: rgba(0, 188, 212, 0.2); color: #00BCD4; border: 1px solid rgba(0, 188, 212, 0.4); }
.tag-gatekeeper { background: rgba(156, 39, 176, 0.2); color: #CE93D8; border: 1px solid rgba(156, 39, 176, 0.4); }
.stats {
  display: flex; gap: 40px; justify-content: center;
}
.stat { text-align: center; }
.stat-value { font-size: 36px; font-weight: 800; color: #fff; }
.stat-label { font-size: 14px; color: #8888aa; text-transform: uppercase; letter-spacing: 1px; }
.bottom {
  margin-top: 40px; font-size: 14px; color: #666680;
}
</style></head><body>
<div class="card">
  <div class="colosseum-icon">&#x1F3DB;&#xFE0F;</div>
  <h1>Agent Colosseum</h1>
  <div class="subtitle">Multi-Model Agent Simulation on Crusoe Cloud</div>
  <div class="tags">
    <span class="tag tag-nemotron">NEMOTRON SUPER-120B</span>
    <span class="tag tag-crusoe">CRUSOE MANAGED INFERENCE</span>
    <span class="tag tag-models">7 MODELS</span>
    <span class="tag tag-gatekeeper">DUAL GATEKEEPER</span>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-value">232</div><div class="stat-label">API Calls</div></div>
    <div class="stat"><div class="stat-value">0</div><div class="stat-label">Errors</div></div>
    <div class="stat"><div class="stat-value">7</div><div class="stat-label">Models</div></div>
    <div class="stat"><div class="stat-value">5</div><div class="stat-label">Model Towns</div></div>
  </div>
  <div class="bottom">DevNetwork AI+ML Hackathon 2026 &middot; Solo Entry &middot; github.com/Alexander-Sorrell-IT/agent-colosseum</div>
</div>
</body></html>"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.set_content(HTML)
    page.screenshot(path=str(OUTPUT), type="png")
    browser.close()

print(f"Thumbnail saved: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
