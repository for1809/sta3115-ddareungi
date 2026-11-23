"""Build one self-contained HTML file of the talk from slides/deck/ (the claude.ai Slides source).

Figures are embedded as base64 from slides/figures_en/, so the output opens offline in any browser
(fonts come from Google Fonts when online, otherwise the system sans-serif).
Slides 5 (elev), 7 (cands) and 11 (rain) are replaced by step-by-step charts (slides/interactive.js,
data in slides/interactive.json from slides/interactive_data.R); the published claude.ai deck keeps the static figures.
Run from the project root:  python slides/build_deck_html.py
Output: slides/deck_standalone.html (not committed; rebuild it with this script)

Keys: right, space or page down = next step or slide; left or page up = back; Home/End; F = full screen; N = speaker notes.
"""
import base64
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECK = ROOT / "deck"
FIG = ROOT / "figures_en"
OUT = ROOT / "deck_standalone.html"

# asset id in the published deck -> figure file
BLOB = {
    "8d184f4f31dbb32b1cbbe6e4eb191261": "01_scale.png",
    "642ec584c48df621acb3eea3f3c2b884": "02_elevation_loess.png",
    "a011fed22ec4beed4f65485517bd3c06": "03_map.png",
    "95d53bd0670f7b0c384fb0c1c88dd251": "04_coplot_subway.png",
    "9af914590f1e2877963d8f8258bee366": "05a_candidates_by_elevation.png",
    "8a8eaaede91dbc4655fde0ad06fcf9d7": "05b_mosaic_roles.png",
    "b6f528463f269f6c06a3afb7a9949150": "06_residual_slope_climb.png",
    "aa8684ab86365684d1ab1ddfb2b4f036": "07_tukey_rain.png",
    "9f41a3ae6d1f2320376a787f500be4c0": "08_coplot_residential.png",
    "cd5672ff0cc1fcadb3101a04e04e554a": "09_gu_slope.png",
    "2de907bdd0d64101b0eece25e7c382e7": "b1_net_change.png",
    "67fa9588c98c4b989e0b9d2469d3b32d": "b2_monthly_bands.png",
    "e8bbf921f66e5df472402d9de7c6b79a": "b3_logit_prediction.png",
    "411e9b98376154af6bd8044a8d8fe0c4": "b4_logit_calibration.png",
}
# slides whose figure becomes a step-by-step chart: slide id -> chart size (same box as the static figure)
IX_SLOTS = {"elev": (1071, 600), "cands": (1100, 506), "rain": (1071, 600)}
ELEV_HINT = '<p class="note muted" style="font-size:24px">Hover over a dot to name the station.</p>\n</div>\n</div>'

# defaults the Slides viewer applies before deck.css
BASE_CSS = """
* { margin: 0; box-sizing: border-box; }
html, body { height: 100%; background: #0b0d10; overflow: hidden; }
body { font: 32px/1.2 'Inter', 'Noto Sans KR', 'Segoe UI', Arial, sans-serif; }
#stage { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: 0 0; }
#stage > section { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden; display: none; isolation: isolate; }
#stage > section.on { display: flex; }
aside { display: none !important; }
h1 { font-size: 96px; font-weight: 600; } h2 { font-size: 64px; font-weight: 600; } h3 { font-size: 44px; font-weight: 600; }
p, li, h1, h2, h3, td, th { overflow-wrap: break-word; text-wrap: pretty; }
table { width: 100%; border-collapse: separate; border-spacing: 0; border: solid #0003; border-width: 2px 0 0 2px; }
th, td { padding: .35em .6em; text-align: left; border: solid #0003; border-width: 0 2px 2px 0; }
.cover-hill { z-index: -1; }
"""

UI_CSS = """
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 38vh; overflow: auto; display: none;
  background: rgba(20, 24, 30, .94); color: #f2f4f6; font: 18px/1.55 'Inter', 'Segoe UI', sans-serif; padding: 18px 28px 22px; }
#notes.on { display: block; }
#notes b { color: #90c2ff; font-weight: 600; margin-right: 8px; }
#notes .cue { color: #ffd76a; display: block; margin-bottom: 6px; }
#hint { position: fixed; right: 14px; bottom: 10px; color: #8b95a1; font: 13px 'Segoe UI', sans-serif; opacity: .8;
  animation: hint-out 800ms ease-in 5s forwards; }
@keyframes hint-out { to { opacity: 0; } }
#notes.on ~ #hint { display: none; }
"""

NAV_JS = """
const S = [...document.querySelectorAll('#stage > section')];
const notes = document.getElementById('notes');
let i = Math.min(Math.max((parseInt(location.hash.slice(1)) || 1) - 1, 0), S.length - 1), step = 0;
const ctrl = () => (window.IX || {})[S[i].id];
function fit() {
  const k = Math.min(innerWidth / 1920, innerHeight / 1080);
  document.getElementById('stage').style.transform = `scale(${k}) translate(-50%, -50%)`;
}
function paintNotes() {
  const a = S[i].querySelector('aside'), c = ctrl();
  const cue = c ? `<span class="cue">Step ${step + 1} of ${c.steps}: ${c.cues[step]}</span>` : '';
  notes.innerHTML = '<b>' + (i + 1) + ' / ' + S.length + '</b>' + cue + (a ? a.innerHTML : '');
}
function setStep(k) { const c = ctrl(); if (!c) return; step = Math.min(Math.max(k, 0), c.steps - 1); c.set(step); paintNotes(); }
window.goStep = setStep;
function show(n, atEnd) {
  i = Math.min(Math.max(n, 0), S.length - 1);
  S.forEach((s, j) => s.classList.toggle('on', j === i));
  const c = ctrl();
  step = c && atEnd ? c.steps - 1 : 0;
  if (c) c.set(step);
  paintNotes();
  history.replaceState(null, '', '#' + (i + 1));
}
function next() { const c = ctrl(); if (c && step < c.steps - 1) setStep(step + 1); else if (i < S.length - 1) show(i + 1); }
function prev() { const c = ctrl(); if (c && step > 0) setStep(step - 1); else if (i > 0) show(i - 1, true); }
addEventListener('keydown', e => {
  if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) { next(); e.preventDefault(); }
  else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) { prev(); e.preventDefault(); }
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(S.length - 1);
  else if (e.key === 'f' || e.key === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
  else if (e.key === 'n' || e.key === 'N') notes.classList.toggle('on');
});
document.getElementById('stage').addEventListener('click', e => (e.clientX > innerWidth / 3 ? next() : prev()));
addEventListener('resize', fit);
fit(); show(i);
"""


def img_uri(m):
    f = FIG / BLOB[m.group(1)]
    return "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode("ascii")


deck = json.loads((DECK / "deck.json").read_text(encoding="utf-8"))
css = (DECK / "deck.css").read_text(encoding="utf-8")
fonts = "\n".join(f'<link rel="stylesheet" href="{html.escape(v["href"])}">' for v in deck["faces"].values())
parts = []
for n, sid in enumerate(deck["order"], 1):
    s = (DECK / "slides" / f"{sid}.html").read_text(encoding="utf-8")
    if sid in IX_SLOTS:
        w, h = IX_SLOTS[sid]
        s, k = re.subn(r'<div class="figcard"><img [^>]*></div>',
                       f'<div class="figcard"><div id="ix-{sid}" style="position:relative;width:{w}px;height:{h}px"></div></div>', s)
        assert k == 1, f"{sid}: figure not found"
        if sid == "elev":
            s, k = re.subn(r'</div>\n</div>\n<div class="foot">', ELEV_HINT + '\n<div class="foot">', s)
            assert k == 1, "elev side column end not found"
    s = re.sub(r"/_blob/([0-9a-f]{32})", img_uri, s)
    # page numbers: each slide resets the counter to its own place, since hidden slides do not count
    s = s.replace("<section ", f'<section style="counter-reset: page {n - 1}" ', 1)
    parts.append(s)
left = re.findall(r"/_blob/[0-9a-f]{32}", "".join(parts))
assert not left, left
ix_json = (ROOT / "interactive.json").read_text(encoding="utf-8").replace("</", "<\\/")
ix_js = (ROOT / "interactive.js").read_text(encoding="utf-8")

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(deck["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{fonts}
<style>{BASE_CSS}</style>
<style>{css}</style>
<style>{UI_CSS}</style>
</head><body>
<div id="stage">
{chr(10).join(parts)}
</div>
<div id="notes"></div>
<div id="hint">→ next, ← back, F full screen, N notes</div>
<script type="application/json" id="ixdata">{ix_json}</script>
<script>{ix_js}</script>
<script>{NAV_JS}</script>
</body></html>
"""
OUT.write_text(page, encoding="utf-8")
print(len(deck["order"]), "slides,", round(OUT.stat().st_size / 1e6, 1), "MB ->", OUT)
