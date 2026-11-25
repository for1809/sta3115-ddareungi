"""Final talk deck: the teammate's deck (slides/team/deck_ddareungi_teammate.html, kept untouched) plus our analysis.

Changes, all made here so the original stays as received:
  1. a new slide "STEP 7. WHEN" after slide 16 (g12): hourly stock matched with trip records shows the hills are
     refilled every day by moves other than rides (mostly rebalancing), but not during the 7-9 am peak
     (figure slides/figures_en/10b_rebalance_bare.png; numbers from analysis/rebalance_bare_log.txt, by bare-earth
     elevation like the teammate deck; 2025 weekdays with under 1 mm of rain)
  2. the conclusion: refill the hills before the morning, and a warning about merging low-use stations
     (bottom 20% of use with another station within 300 m: 84 of the 156 at 40 m and above already empty)
  3. limits, item 1: trucks are now seen, but only as the part of stock change rides do not explain
  4. page numbers: each slide's counter is reset to its new place
  5. slide "why": yearly rides 2021-2025 and the operating deficit as side-by-side bars (team's table)
  6. slide "weather": every station's mean rentals by 5 C band of its local daily maximum, 2024-2025 weekdays (data/station_tmax_band.csv)
  7. slide "gumap": the hourly-use map in green, so it is not confused with the blue of the net-flow maps
  0. a "What is Ddareungi" slide after the cover
  10. storyline (slides/final_deck_story.py, slides/final_deck_new.py): the new question on slide 4, slide order in four acts, eyebrows, and
      five new slides drawn from the data (ids d_*)
  9b. net outflow in bikes, no docks (slides/final_deck_nodocks.py)
Run from the project root:  python slides/build_final_deck.py
Output: slides/deck_final.html (steps 0-10); slides/deck_draft.html is written as the same file
"""
import base64
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "team" / "deck_ddareungi_teammate.html"
OUT = ROOT / "deck_final.html"
DRAFT = ROOT / "deck_draft.html"   # same file as deck_final.html, kept for links to the draft
FIG = ROOT / "figures_en" / "10b_rebalance_bare.png"   # bare-earth elevation bands, as in the teammate deck

t = SRC.read_text(encoding="utf-8")
img = "data:image/png;base64," + base64.b64encode(FIG.read_bytes()).decode("ascii")
jpg = lambda name: "data:image/jpeg;base64," + base64.b64encode((ROOT / "photos" / name).read_bytes()).decode("ascii")

# 0. "What is Ddareungi?" after the cover: photos from Wikimedia Commons (slides/photos/CREDITS.md), facts from the
#    Seoul press release of 2025-11-12 and the city's how-to article of 2024-07-22 (sources in CREDITS.md)
CARD = "background:var(--tint);border-radius:24px;padding:26px 30px;display:flex;flex-direction:column;gap:10px"
CT = "font-size:28px;font-weight:700;margin:0;color:var(--ink)"
CB = "font-size:22px;line-height:1.45;margin:0;color:var(--ink2)"
INTRO = f"""<section id="intro" data-transition="fade">
<p class="eyebrow">WHAT IS DDAREUNGI</p>
<h2>Seoul’s public bikes: rent at any station, return at any station</h2>
<div style="display:flex;gap:24px;margin-top:32px;align-items:stretch">
<img src="{jpg('seoul_bike_31590.jpg')}" alt="A white Ddareungi bike with green wheels locked at a green station rack on a Seoul pavement." style="width:640px;height:360px;object-fit:cover;border-radius:24px">
<img src="{jpg('hangang_station_6.jpg')}" alt="A Ddareungi station under a bridge on the Han River bikeway, with a row of bikes in green racks." style="width:480px;height:360px;object-fit:cover;border-radius:24px">
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:18px;padding-left:8px">
<div class="stat"><p class="stat-num ink">45,000 bikes</p><p class="stat-lab">at about 2,800 stations (2025)</p></div>
<div class="stat"><p class="stat-num blue">Since 2015</p><p class="stat-lab">5.06 million members, 250 million rides in ten years</p></div>
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:24px">
<div style="{CARD}"><p style="{CT}">Rent</p><p style="{CB}">Scan the QR code on the bike with the app. The lock opens by Bluetooth. Age 13 and over, 24 hours a day.</p></div>
<div style="{CARD}"><p style="{CT}">Return</p><p style="{CB}">Lock the rear wheel at any station and the return is automatic. Locked anywhere else, it still counts as rented.</p></div>
<div style="{CARD}"><p style="{CT}">Price</p><p style="{CB}">1,000 won for an hour on a day pass. Season passes run 7 to 365 days; return and rent again when time is up.</p></div>
<div style="{CARD}"><p style="{CT}">Commute</p><p style="{CB}">7–9 am and 5–7 pm carry 44% of weekday rides. The city already sends 33 staff to 330 crowded or empty stations.</p></div>
</div>
<p style="font-size:16px;color:var(--muted);margin:14px 0 0">Photos: *Youngjin, CC BY-SA 3.0 (left); Sarang, public domain (right); Wikimedia Commons. Facts: Seoul Metropolitan Government, 2024 and 2025.</p>
<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>
<aside>First, a quick look at Ddareungi for anyone who has not used it. It started in October 2015, and today there are about 45,000 bikes at around 2,800 stations. You rent with an app: scan the QR code on the bike and the lock opens. You can return it at any station, just by locking the rear wheel there. A day pass is 1,000 won an hour, and there are season passes too. Most important for us: on weekdays, the morning and evening commute hours carry 44% of all rides. Because bikes are rented at one station and returned at another, some stations empty out and others fill up. The city already knows this: at commute times it sends 33 staff to 330 stations that are too full or too empty. That is the problem we look at.</aside>
</section>
"""

WHEN = f"""<section id="when" data-transition="fade">
<p class="eyebrow">STEP 7. WHEN</p>
<h2>Trucks already refill the hills every day, but not before 8 am</h2>
<div class="body">
<div class="figcard"><img src="{img}" alt="Bikes added to a station per weekday by riders and by other moves, by bare-earth elevation band. Below 20 m riders add 1.0 and other moves take 1.4; at 40 m and above riders take 4.3 and other moves add 4.3." style="width:1071px;height:557px;object-fit:contain"></div>
<div class="side" style="gap:18px">
<div class="stat"><p class="stat-num">−4.3</p><p class="stat-lab">bikes a day riders take from stations at 40 m and above</p></div>
<div class="stat"><p class="stat-num blue">+4.3</p><p class="stat-lab">bikes a day put back there by other moves, mostly rebalancing</p></div>
<div class="stat"><p class="stat-num ink">0.99</p><p class="stat-lab">correlation of stock change and rides at 7 to 9 am: almost no refilling in the peak</p></div>
<div class="stat"><p class="stat-num">28%</p><p class="stat-lab">of commute hours those stations still have zero bikes</p></div>
<p class="note muted" style="font-size:20px">2025 dry weekdays; hourly stock matched with trips.</p>
</div>
</div>
<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>
<aside>Trip records do not show the trucks. So we also took the hourly stock at every station and matched it with the trips: whatever the rides do not explain is other moves, mostly the trucks. Below 20 metres, riders bring in about one bike a day and other moves take about one away. At 40 metres and above, riders take away about four bikes a day, and other moves bring almost exactly four back. So the trucks already go up the hills every day. But between 7 and 9 a.m. the stock moves almost exactly with the rides, a correlation of 0.99: almost nothing is refilled during the peak, and those hill-top stations still have no bikes in 28% of the commute hours. The question is not only where the trucks go, but when.</aside>
</section>
"""

CONCLUSION = """<section id="conclusion" class="accent" data-transition="fade">
<p class="eyebrow">CONCLUSION</p>
<h2>Send the trucks up the hills before the morning, and skip the stations that refill themselves</h2>
<div class="take">
<p class="take-line soft">Bikes roll downhill in the morning and are not ridden back up: net flow runs downhill 69% of the time where the ground slopes.</p>
<p class="take-line soft">An empty station at 9 am is not always a problem. 703 stations (G2) refill themselves by night.</p>
<p class="take-line soft">The hills already get bikes back every day, yet stay empty in 28% of commute hours: the refill does not arrive before the peak.</p>
<p class="take-line"><b>Refill the 893 hill-top G1 stations before 7 am, with bikes from the 533 low-lying G3 stations. And do not merge low-use stations on ride counts alone: half the hill-top merge candidates already run empty.</b></p>
</div>
<aside>To sum up. Bikes roll downhill in the morning and are not ridden back up. Because of that, an empty station at 9 am is not always a problem: 703 stations get their bikes back by night without any help. The stations that really need a truck are the 893 G1 stations on the hills, and they are already refilled every day, just not before the morning peak. So the plan is about timing: bring bikes from the 533 G3 stations on low ground that pile up all day, and have them on the hills before 7 a.m. One more point for the debate about cutting the system: if you merge the least-used stations by ride counts alone, half of the hill-top candidates are stations that are already empty in the morning. Their low use may mean no bikes, not no demand.</aside>
</section>
"""

# ---- 5. slide "why": yearly rides 2021-2025 and the operating deficit as side-by-side bars (two axes) (numbers from the team's table:
#      rides 2022-2025 match data/monthly_age.csv; deficit 2023 and 2024 match the press report in README)
WHY_SIDE_OLD = re.search(r'(<section[^>]*id="why".*?<div class="side">)(.*?)(</div>\n</div>\n<div class="foot">)', t, re.S)
assert WHY_SIDE_OLD, "why side not found"
WHY_SIDE = """
<div class="stat"><p class="stat-num ink">44.9M → 37.4M</p><p class="stat-lab">rides a year, 2023 → 2025; 2025 alone is −14.8%</p></div>
<div class="stat"><p class="stat-num">₩17.6 bn</p><p class="stat-lab">operating deficit in 2025, almost double the ₩9.4 bn of 2022</p></div>
"""
t = (t[:WHY_SIDE_OLD.start(1)] + WHY_SIDE_OLD.group(1).replace('<div class="side">', '<div class="side" style="justify-content:center">')
     + WHY_SIDE + t[WHY_SIDE_OLD.end(2):])   # two stats, centred in the column
WHY_NOTE_OLD = re.search(r'(<section[^>]*id="why".*?<aside>)(.*?)(</aside>)', t, re.S)
t = t[:WHY_NOTE_OLD.start(2)] + (
    "Ddareungi grew fast: from 32 million rides in 2021 to almost 45 million in 2023. Then it fell two years in a row, "
    "to 37.4 million in 2025, 14.8% fewer than the year before. At the same time the operating deficit grew, from 9.4 billion won "
    "in 2022 to 17.6 billion won in 2025. In October a newspaper reported that the city was considering cutting the fleet. "
    "The city denied it the same day, but it confirmed that a study of the right size of the system and its running costs is under way.") + t[WHY_NOTE_OLD.end(2):]

WHY_JS = r"""  // ---------- why: yearly rides 2021-2025 (left axis) and operating deficit (right axis), bars side by side ----------
  (function () {
    const box = document.getElementById('ix-ride'); if (!box) return;
    const YR = [2021, 2022, 2023, 2024, 2025], RIDES = [32.05, 40.95, 44.91, 43.85, 37.37], DEF = [10.3, 9.4, 10.9, 12.7, 17.6];
    const W = 1071, H = 560, L = 96, R = 104, T = 78, B = 92, minR = 20, maxR = 50, maxD = 40;   // rides axis starts at 20M so the rise and fall show
    const svg = makeSvg(box, W, H);
    const y = v => H - B - (v - minR) / (maxR - minR) * (H - T - B), yd = v => H - B - v / maxD * (H - T - B), bw = (W - L - R) / YR.length;
    axisY(svg, L, R, W, y, [20, 30, 40, 50], v => v + 'M');
    el('line', { x1: L, x2: W - R, y1: H - B, y2: H - B, stroke: C.muted, 'stroke-width': 1.5 }, svg);
    ylab(svg, 'Rides a year (million)', T, H, B);
    YR.forEach((yr, j) => {
      const cx = L + bw * (j + .5);
      const rx = cx - bw * .42, rw = bw * .42;   // rides on the left of each year, the deficit bar overlaps it slightly on the right
      el('rect', { x: rx, width: rw, y: y(RIDES[j]), height: y(minR) - y(RIDES[j]), rx: 8, fill: j === 4 ? C.blue : C.light }, svg);
      halo(txt(RIDES[j].toFixed(1) + 'M', { x: rx + rw / 2, y: y(RIDES[j]) - 12, 'text-anchor': 'middle', 'font-size': 20, 'font-weight': 700, fill: C.ink }, svg));
      txt(yr, { x: cx - bw * .06, y: H - B + 30, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, svg);
    });
    const lg = el('g', {}, svg);
    el('rect', { x: L, y: 14, width: 18, height: 18, rx: 4, fill: C.blue }, lg);
    txt('Rides a year (left axis)', { x: L + 26, y: 30, 'font-size': 19, fill: C.ink }, lg);
    const dl = el('g', {}, svg);
    el('rect', { x: L + 300, y: 14, width: 18, height: 18, rx: 4, fill: C.red }, dl);
    txt('Operating deficit, billion won (right axis)', { x: L + 326, y: 30, 'font-size': 19, fill: C.ink }, dl);
    [0, 10, 20, 30, 40].forEach(v => txt('₩' + v + 'B', { x: W - R + 14, y: yd(v) + 6, 'font-size': 17, fill: C.red }, dl));
    txt('Operating deficit (billion won)', { x: 0, y: 0, transform: `translate(${W - 16} ${(T + H - B) / 2}) rotate(90)`, 'text-anchor': 'middle', 'font-size': 19, fill: C.red }, dl);
    DEF.forEach((v, j) => {
      const dx = L + bw * (j + .5) - bw * .06, dw = bw * .36;
      el('rect', { x: dx, width: dw, y: yd(v), height: yd(0) - yd(v), rx: 8, fill: j === 4 ? C.red : '#FFC9CE', stroke: '#fff', 'stroke-width': 3 }, dl);
      halo(txt('₩' + v.toFixed(1) + 'B', { x: dx + dw / 2, y: yd(v) - 12, 'text-anchor': 'middle', 'font-size': 19, 'font-weight': 700, fill: C.red }, dl));
    });
    txt('Left axis starts at 20M. Rides: Seoul Open Data. Deficit: Seoul Facilities Corporation figures as reported in the press.', { x: L, y: H - 30, 'font-size': 14, fill: C.muted }, svg);
    const side = sideItems('why');
    IX.why = {
      steps: 2,
      cues: ['Rides grew to 44.9 million in 2023, then fell two years in a row: 37.4 million in 2025, 14.8% fewer than 2024.',
             'Meanwhile the operating deficit grew, from 9.4 billion won in 2022 to 17.6 billion won in 2025.'],
      set(k) { fade(dl, k >= 1); reveal(side, k === 0 ? 1 : side.length); },
    };
    stop(box);
  })();

"""
i0 = t.find("  // ---------- why: average rides a day, 2024 vs 2025 ----------")
i1 = t.find("  // ---------- hours:", i0)
assert i0 > 0 and i1 > i0, "why chart block not found"
t = t[:i0] + WHY_JS + t[i1:]

# ---- 7. slide "gumap": the hourly-use map in green, so it is not read as the blue "gains bikes" of the net-flow maps
GREEN = "#12a150"
gi = t.find("// ---------- gu map:")
gj = t.find("// ----------", gi + 10)
blk = t[gi:gj]
for a, b in [("ps[g].setAttribute('fill', seq(GH[g][h].u, 8))",
              f"ps[g].setAttribute('fill', mix('#f7f9fc', '{GREEN}', Math.max(0, Math.min(1, GH[g][h].u / 8))))"),
             ("linear-gradient(90deg, #f7f9fc, ${C.navy})", f"linear-gradient(90deg, #f7f9fc, {GREEN})")]:
    assert blk.count(a) == 1, a
    blk = blk.replace(a, b)
t = t[:gi] + blk + t[gj:]
GU_STAT = '<div class="stat"><p class="stat-num blue">8 am, 6 pm</p><p class="stat-lab">every district lights up at the two commute peaks</p></div>'
assert t.count(GU_STAT) == 1
t = t.replace(GU_STAT, GU_STAT.replace('class="stat-num blue"', f'class="stat-num" style="color:{GREEN}"'))

# ---- 9. charts: stmap and quad redrawn, gumap shows losing and gaining together, cover map (slides/final_deck_charts.py)
cspec = importlib.util.spec_from_file_location("final_deck_charts", ROOT / "final_deck_charts.py")
CH = importlib.util.module_from_spec(cspec)
cspec.loader.exec_module(CH)
a, b = CH.GUMAP_REVEAL
assert t.count(a) == 1, "gumap reveal not found"
t = t.replace(a, b)
for start, end, new in [("  // ---------- station map with contours ----------", "  // ---------- flow field", CH.STMAP),
                        ("  // ---------- the 2x2 ----------", "  // ---------- the 2x2 on the map", CH.QUAD)]:
    i0 = t.find(start); i1 = t.find(end, i0)
    assert i0 > 0 and i1 > i0, start
    t = t[:i0] + new + t[i1:]
ST = re.search(r'(<section[^>]*id="stmap".*?<div class="side">)(.*?)(</div>\n</div>\n<div class="foot">)', t, re.S)
assert ST, "stmap side not found"
t = t[:ST.start(2)] + CH.STMAP_SIDE + t[ST.end(2):]
assert len(CH.COVER_OLD.findall(t)) == 1, "cover hill not found"
WX = re.search(r'(<section[^>]*id="weather".*?<div class="side">)(.*?)(</div>\n</div>\n<div class="foot">)', t, re.S)
assert WX, "weather side not found"
t = t[:WX.start(2)] + CH.WEATHER_SIDE + t[WX.end(2):]
w0 = t.find("  // ---------- weather: temperature vs rides"); w1 = t.find("  // ----------", w0 + 20)
assert w0 > 0 and w1 > w0, "weather chart not found"
import csv as _csv
import statistics as _st
_band = {}
for r in _csv.DictReader(open(ROOT.parent / "data" / "station_tmax_band.csv", encoding="utf-8")):
    _band.setdefault(int(r["band"]), []).append(round(float(r["mean_rent"]), 1))
_lab = {-5: "< 0", 35: "35+"}
TMAX = [{"lo": b, "lab": _lab.get(b, f"{b}–{b + 5}"), "med": _st.median(v), "v": v} for b, v in sorted(_band.items())]
t = t[:w0] + CH.WEATHER.replace("__TMAX_BAND__", json.dumps(TMAX, separators=(",", ":"), ensure_ascii=False)) + t[w1:]
IXD = json.loads(re.search(r'<script[^>]*id="ixdata"[^>]*>(.*?)</script>', t, re.S).group(1))
t = CH.COVER_OLD.sub(lambda m: CH.cover_map(IXD), t)

secs = list(re.finditer(r"<section\b.*?</section>\s*", t, re.S))
ids = [re.search(r'id="([^"]+)"', m.group(0)).group(1) for m in secs]
assert "when" not in ids and "intro" not in ids and {"cover", "g12", "conclusion", "limits"} <= set(ids), ids

parts, k_prev = [], 0
for m, sid in zip(secs, ids):
    parts.append(t[k_prev:m.start()])
    s = m.group(0)
    if sid == "conclusion":
        s = CONCLUSION + "\n"
    if sid == "limits":
        old = "Trip records hide trucks: we see where bikes go, not where trucks already move them."
        assert s.count(old) == 1, "limits item 1 changed"
        s = s.replace(old, "Trucks appear only as the stock change that rides do not explain: we do not see when each truck comes.")
        s = s.replace("First, trip records do not show the trucks, so we see where riders move bikes, not where trucks already move them back.",
                      "First, we see the trucks only indirectly, as the change in stock that rides do not explain, so we do not know when each truck arrives.")
    parts.append(s)
    if sid == "cover":
        parts.append(INTRO + "\n")
    if sid == "g12":
        parts.append(WHEN + "\n")
    k_prev = m.end()
parts.append(t[k_prev:])
out = "".join(parts)

# ---- 8. wording: plainer English for every slide, its notes, the step cues and the chart group names
#      (slides/final_deck_copy.py; same content, numbers and order)
spec = importlib.util.spec_from_file_location("final_deck_copy", ROOT / "final_deck_copy.py")
COPY = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COPY)
for sid, rw in COPY.SLIDES.items():
    m = re.search(r'<section\b[^>]*id="%s".*?</section>' % sid, out, re.S)
    assert m, sid
    s = m.group(0)
    for a, b in rw.get("pairs", []):
        assert s.count(a) == 1, (sid, a[:60])
        s = s.replace(a, b)
    if "eyebrow" in rw:
        s, k = re.subn(r'<p class="eyebrow">.*?</p>', f'<p class="eyebrow">{rw["eyebrow"]}</p>', s, count=1)
        assert k == 1, sid
    if "title" in rw:
        s, k = re.subn(r"<h2>.*?</h2>", f"<h2>{rw['title']}</h2>", s, count=1, flags=re.S)
        assert k == 1, sid
    if "aside" in rw:
        s, k = re.subn(r"<aside>.*?</aside>", f"<aside>{rw['aside']}</aside>", s, count=1, flags=re.S)
        assert k == 1, sid
    out = out[:m.start()] + s + out[m.end():]
out, k = re.subn(r"<title>.*?</title>", "<title>Where Do All the Ddareungi Go? Bikes roll downhill, and nobody rides them back up</title>", out, count=1)
assert k == 1
js0 = out.find("// Step-by-step SVG charts for the deck.")
js1 = out.find("</script>", js0)
assert js0 > 0
js = out[js0:js1]
for a, b in COPY.JS:
    assert js.count(a) >= 1, a[:60]
    js = js.replace(a, b)
out = out[:js0] + js + out[js1:]

# ---- 9b. net outflow in bikes, no docks anywhere (slides/final_deck_nodocks.py; decision 2026-11-25):
#      dock counts are not capacity, so station and district values are in bikes and the 2x2 groups use the sign only
nspec = importlib.util.spec_from_file_location("final_deck_nodocks", ROOT / "final_deck_nodocks.py")
NODOCK = importlib.util.module_from_spec(nspec)
nspec.loader.exec_module(NODOCK)
out, _ = NODOCK.apply(out)
assert "dock" not in re.sub(r'<script[^>]*id="ixdata".*?</script>', "", out, flags=re.S).lower()

# ---- 10. storyline (slides/final_deck_story.py, slides/final_deck_new.py): the final deck since 2026-11-25
#      the new question, slide order, eyebrows, and text drafts for slides to come
sspec = importlib.util.spec_from_file_location("final_deck_story", ROOT / "final_deck_story.py")
STORY = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(STORY)
m = re.search(r'<section\b[^>]*id="cost".*?</section>', out, re.S)
s = m.group(0)
s, k = re.subn(r'<p style="margin:0;font-size:76px.*?</p>', lambda _: STORY.QUESTION, s, count=1, flags=re.S)
assert k == 1
s, k = re.subn(r"<aside>.*?</aside>", lambda _: f"<aside>{STORY.QUESTION_NOTE}</aside>", s, count=1, flags=re.S)
assert k == 1
out = out[:m.start()] + s + out[m.end():]
for sid, eb in STORY.EYEBROWS.items():
    m = re.search(r'<section\b[^>]*id="%s".*?</section>' % sid, out, re.S)
    s, k = re.subn(r'<p class="eyebrow">.*?</p>', f'<p class="eyebrow">{eb}</p>', m.group(0), count=1)
    assert k == 1, sid
    out = out[:m.start()] + s + out[m.end():]
secs = list(re.finditer(r"<section\b.*?</section>", out, re.S))
for a, b in zip(secs, secs[1:]):
    assert not out[a.end():b.start()].strip(), "text between sections"
have = {re.search(r'id="([^"]+)"', m.group(0)).group(1): m.group(0) for m in secs}
have.update(STORY.DRAFTS)
nspec2 = importlib.util.spec_from_file_location("final_deck_new", ROOT / "final_deck_new.py")
NEW = importlib.util.module_from_spec(nspec2)
nspec2.loader.exec_module(NEW)
have.update(NEW.SLIDES)                                   # the five new slides drawn from the data
have["when"] = STORY.when_slide(ROOT.parent / "data" / "hourly_refill_2025.csv")   # hourly version of STEP 7 (analysis/hourly_refill.py)
assert set(have) == set(STORY.ORDER) and len(STORY.ORDER) == len(set(STORY.ORDER)), set(have) ^ set(STORY.ORDER)
out = out[:secs[0].start()] + "\n\n".join(have[i].strip() for i in STORY.ORDER) + out[secs[-1].end():]

# page numbers: section n resets the counter to n - 1 (hidden slides do not count)
def renumber(html):
    n = 0

    def one(m):
        nonlocal n
        n += 1
        tag = re.sub(r'\sstyle="counter-reset: page \d+"', "", m.group(0))
        return tag.replace("<section ", f'<section style="counter-reset: page {n - 1}" ', 1)

    return re.sub(r"<section\b[^>]*>", one, html), n


for html, path in ((out, OUT), (out, DRAFT)):        # the storyline is now the final deck; deck_draft.html is the same file
    html, n = renumber(html)
    path.write_text(html, encoding="utf-8")
    print(n, "slides ->", path, round(path.stat().st_size / 1e6, 2), "MB")
