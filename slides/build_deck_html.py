"""Build one self-contained HTML file of the talk from slides/deck/ (the claude.ai Slides source).

Figures are embedded as base64 from slides/figures_en/, so the output opens offline in any browser
(fonts come from Google Fonts when online, otherwise the system sans-serif).
Run from the project root:  python slides/build_deck_html.py
Output: slides/deck_standalone.html (not committed; rebuild it with this script)

Keys: right, space or page down = next; left or page up = previous; Home/End; F = full screen; N = speaker notes.
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
#hint { position: fixed; right: 14px; bottom: 10px; color: #8b95a1; font: 13px 'Segoe UI', sans-serif; opacity: .8;
  animation: hint-out 800ms ease-in 5s forwards; }
@keyframes hint-out { to { opacity: 0; } }
#notes.on ~ #hint { display: none; }
"""

JS = """
const S = [...document.querySelectorAll('#stage > section')];
const notes = document.getElementById('notes');
let i = Math.min(Math.max((parseInt(location.hash.slice(1)) || 1) - 1, 0), S.length - 1);
function fit() {
  const k = Math.min(innerWidth / 1920, innerHeight / 1080);
  document.getElementById('stage').style.transform = `scale(${k}) translate(-50%, -50%)`;
}
function show(n) {
  i = Math.min(Math.max(n, 0), S.length - 1);
  S.forEach((s, j) => s.classList.toggle('on', j === i));
  const a = S[i].querySelector('aside');
  notes.innerHTML = '<b>' + (i + 1) + ' / ' + S.length + '</b>' + (a ? a.innerHTML : '');
  history.replaceState(null, '', '#' + (i + 1));
}
addEventListener('keydown', e => {
  if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) { show(i + 1); e.preventDefault(); }
  else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) { show(i - 1); e.preventDefault(); }
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(S.length - 1);
  else if (e.key === 'f' || e.key === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
  else if (e.key === 'n' || e.key === 'N') notes.classList.toggle('on');
});
document.getElementById('stage').addEventListener('click', e => show(e.clientX > innerWidth / 3 ? i + 1 : i - 1));
addEventListener('resize', fit);
fit(); show(i);
"""


# Slide 5 (elev) gets a hover chart drawn from slides/elev_hover.json (made by slides/elev_hover_data.R);
# the published deck keeps the static PNG.
HOVER = json.loads((ROOT / "elev_hover.json").read_text(encoding="utf-8"))
HOVER_DIV = ('<div class="figcard"><div id="elevchart" style="position:relative;width:1071px;height:600px"></div></div>')
HOVER_NOTE = '<p class="note muted" style="font-size:24px">Hover over a point to see the station.</p>\n</div>\n</div>'

HOVER_JS = """
(function () {
  const box = document.getElementById('elevchart');
  if (!box) return;
  const D = JSON.parse(document.getElementById('elevdata').textContent);
  const W = 1071, H = 600, L = 84, R = 24, T = 84, B = 84, XM = 80, YM = 0.92;
  const x = e => L + e / XM * (W - L - R), y = s => H - B - s / YM * (H - T - B);
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, at, parent) => { const n = document.createElementNS(ns, tag);
    for (const k in at) n.setAttribute(k, at[k]); (parent || svg).appendChild(n); return n; };
  const txt = (s, at, parent) => { const n = el('text', at, parent); n.textContent = s; return n; };
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, 'font-family': "Inter, 'Segoe UI', sans-serif" }, box);
  [0, .25, .5, .75].forEach(v => { el('line', { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: '#e5e8eb' });
    txt(Math.round(v * 100) + '%', { x: L - 12, y: y(v) + 6, 'text-anchor': 'end', 'font-size': 17, fill: '#6b7684' }); });
  [0, 20, 40, 60, 80].forEach(v => { el('line', { x1: x(v), x2: x(v), y1: T - 10, y2: H - B, stroke: '#e5e8eb' });
    txt(v, { x: x(v), y: H - B + 28, 'text-anchor': 'middle', 'font-size': 17, fill: '#6b7684' }); });
  [20, 40].forEach(v => el('line', { x1: x(v), x2: x(v), y1: T - 20, y2: H - B, stroke: '#6b7684', 'stroke-dasharray': '6 5' }));
  const lab = ['Below 20 m', '20-40 m', '40 m and above'];
  [10, 30, 60].forEach((v, k) => { txt(lab[k], { x: x(v), y: T - 46, 'text-anchor': 'middle', 'font-size': 18, fill: '#191f28' });
    txt('mean ' + (D.bands[k] * 100).toFixed(1) + '%', { x: x(v), y: T - 22, 'text-anchor': 'middle', 'font-size': 18, fill: '#191f28' }); });
  const g = el('g', { fill: '#6b7684', 'fill-opacity': .22 });
  D.points.forEach(p => el('circle', { cx: x(p.e).toFixed(1), cy: y(p.s).toFixed(1), r: 3 }, g));
  el('path', { d: 'M' + D.curve.map(c => x(c.x).toFixed(1) + ',' + y(c.y).toFixed(1)).join('L'),
    fill: 'none', stroke: '#f04452', 'stroke-width': 4, 'stroke-linecap': 'round' });
  txt('Station elevation (m)', { x: (L + W - R) / 2, y: H - B + 58, 'text-anchor': 'middle', 'font-size': 19, fill: '#191f28' });
  txt('Morning shortage (07-09 h)', { x: 0, y: 0, transform: `translate(26 ${(T + H - B) / 2}) rotate(-90)`,
    'text-anchor': 'middle', 'font-size': 19, fill: '#191f28' });
  txt(`The ${D.n_above} stations above 80 m are left out: too few to smooth.`, { x: L, y: H - 6, 'font-size': 14, fill: '#6b7684' });
  const ring = el('circle', { r: 9, fill: 'none', stroke: '#191f28', 'stroke-width': 2.5, visibility: 'hidden' });
  const dot = el('circle', { r: 5, fill: '#f04452', visibility: 'hidden' });
  const tip = document.createElement('div');
  tip.style.cssText = 'position:absolute;pointer-events:none;display:none;background:#191f28;color:#fff;border-radius:14px;' +
    'padding:14px 18px;font:20px/1.45 Inter,"Noto Sans KR","Segoe UI",sans-serif;white-space:nowrap;box-shadow:0 6px 20px #0003';
  box.appendChild(tip);
  const row = (k, v) => { const d = document.createElement('div'); const a = document.createElement('span');
    a.style.color = '#b0b8c1'; a.textContent = k + '  '; d.append(a, v); return d; };
  function hide() { tip.style.display = 'none'; ring.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); }
  box.addEventListener('mousemove', ev => {
    const r = box.getBoundingClientRect(), k = W / r.width;
    const mx = (ev.clientX - r.left) * k, my = (ev.clientY - r.top) * k;
    let best = null, bd = 14 * 14;
    for (const p of D.points) { const dx = x(p.e) - mx, dy = y(p.s) - my, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = p; } }
    if (!best) return hide();
    const px = x(best.e), py = y(best.s);
    [ring, dot].forEach(c => { c.setAttribute('cx', px); c.setAttribute('cy', py); c.setAttribute('visibility', 'visible'); });
    tip.replaceChildren();
    const h = document.createElement('div'); h.style.cssText = 'font-weight:700;font-size:22px'; h.textContent = best.n;
    const gu = document.createElement('div'); gu.style.color = '#b0b8c1'; gu.textContent = best.g + '-gu';
    tip.append(h, gu, row('Elevation', best.e + ' m'), row('Morning shortage', (best.s * 100).toFixed(1) + '%'),
      row('Rides a day', best.u.toFixed(1)));
    if (best.m) { const b = document.createElement('div'); b.style.cssText = 'margin-top:6px;color:#ff9aa3;font-weight:600';
      b.textContent = 'Merge candidate (bottom 20% of use)'; tip.append(b); }
    tip.style.display = 'block';
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    tip.style.left = (px + 18 + tw > W ? px - 18 - tw : px + 18) + 'px';
    tip.style.top = Math.max(0, Math.min(H - th, py - th / 2)) + 'px';
  });
  box.addEventListener('mouseleave', hide);
  box.addEventListener('click', ev => ev.stopPropagation());
})();
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
    if sid == "elev":
        s, k = re.subn(r'<div class="figcard"><img [^>]*></div>', HOVER_DIV, s)
        assert k == 1, "elev figure not found"
        s, k = re.subn(r"</div>\n</div>\n<div class=\"foot\">", HOVER_NOTE + '\n<div class="foot">', s)
        assert k == 1, "elev side column end not found"
    s = re.sub(r"/_blob/([0-9a-f]{32})", img_uri, s)
    # page numbers: each slide resets the counter to its own place, since hidden slides do not count
    s = s.replace("<section ", f'<section style="counter-reset: page {n - 1}" ', 1)
    parts.append(s)
hover_json = json.dumps(HOVER, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
left = re.findall(r"/_blob/[0-9a-f]{32}", "".join(parts))
assert not left, left

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
<script type="application/json" id="elevdata">{hover_json}</script>
<script>{JS}</script>
<script>{HOVER_JS}</script>
</body></html>
"""
OUT.write_text(page, encoding="utf-8")
print(len(deck["order"]), "slides,", round(OUT.stat().st_size / 1e6, 1), "MB ->", OUT)
