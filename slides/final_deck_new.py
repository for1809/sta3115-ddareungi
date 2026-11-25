"""Slides of the storyline written here: five drawn from the data, and the DATA slide (read by slides/build_final_deck.py, step 10).

  scope         DATA: the days, the stations and the sources (text only)
TITLES: short slide titles, applied last.
  d_buffer      STARTING INVENTORY: flat vs hill stations far from the subway (bars at 7 and 9 am, empty share)
  a_buffer      appendix: every station, bikes at 8 am against the empty share
  traits        FACTORS TOGETHER: logistic model of running out (the 20% line) on elevation, relief and subway distance
NOTES and WEATHER_LEAD: speaker notes of current slides that follow the new order.
intro(): the "What is Ddareungi" slide with an icon strip in place of four text cards.
  d_measures    WHAT WE MEASURE: every station, morning net outflow against empty share (losing bikes is not running out)
  d_subway      FACTOR 4: net outflow and empty share by quarter of subway distance
  d_cop_subway  FACTORS TOGETHER: coplot of empty share on elevation, one panel per quarter of subway distance
  d_wx_elev     FACTORS TOGETHER: morning net outflow by morning temperature and elevation band
  d_buffer      FACTORS TOGETHER: bikes at 7 and 9 am for flat and hill stations near and far from the subway
Net outflow in bikes (team table data/od_2024_2025/od/s0_station_daily.csv.gz, 2024-2025 clear weekdays, 07-09 h);
empty share and hourly stock from 2025 dry weekdays (data/station_master.csv, data/story_numbers.json from analysis/story_numbers.py).
"""
import csv, gzip, json, math, re
from collections import defaultdict
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[1]
N = json.load(open(R / "data/story_numbers.json", encoding="utf-8"))

RED, BLUE, GREY, MUTED, LINE, INK, INK2, TINT = "#F04452", "#3182F6", "#B0B8C1", "#6B7684", "#E5E8EB", "#191F28", "#333D4B", "#F4F8FF"
NAVY = "#1B3A6B"
FOOT = '<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>'


RT_ = ' style="text-align:right"'


def t(x, y, s, size=18, fill=MUTED, anchor="start", weight=None, extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}"{w}{extra}>{s}</text>'


def svg(w, h, label, body):
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}" style="font-family:inherit;display:block">{"".join(body)}</svg>'


def slide(sid, eyebrow, title, chart, side, note):
    return f"""<section id="{sid}" data-transition="fade">
<p class="eyebrow">{eyebrow}</p>
<h2>{title}</h2>
<div class="body">
<div class="figcard">{chart}</div>
{side}
</div>
{FOOT}
<aside>{note}</aside>
</section>"""


def stat(num, lab, cls=""):
    return f'<div class="stat"><p class="stat-num {cls}">{num}</p><p class="stat-lab">{lab}</p></div>'


def sidebox(*items, note=None):
    n = f'<p class="note muted" style="font-size:20px">{note}</p>' if note else ""
    return f'<div class="side" style="gap:22px">{"".join(items)}{n}</div>'


# ---------------- station table
st = []
for r in csv.DictReader(open(R / "data/station_master.csv", encoding="utf-8-sig")):
    if r["subway_m"] and r["elev_bare_m"] and r["am_empty_dry"]:
        st.append(dict(id=r["station_id"], sub=float(r["subway_m"]), elev=float(r["elev_bare_m"]), empty=float(r["am_empty_dry"])))
cut = N["subway_cuts"]
q_of = lambda d: sum(d >= c for c in cut)
band = lambda e: "hill" if e >= 40 else ("flat" if e < 20 else "mid")
QLAB = [f"under {cut[0]} m", f"{cut[0]}–{cut[1]} m", f"{cut[1]}–{cut[2]} m", f"{cut[2]} m and over"]

net = defaultdict(lambda: [0.0, 0])
with gzip.open(R / "data/od_2024_2025/od/s0_station_daily.csv.gz", "rt", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["clear_weekday"] == "True":
            a = net[r["st_id"]]; a[0] += float(r["am_net"]); a[1] += 1
for s in st:
    a = net.get(s["id"]); s["net"] = a[0] / a[1] if a else None
mean = lambda v: sum(v) / len(v)
byq = {q: [s for s in st if q_of(s["sub"]) == q] for q in range(4)}
qnet = [mean([s["net"] for s in byq[q] if s["net"] is not None]) for q in range(4)]
qemp = [mean([s["empty"] for s in byq[q]]) for q in range(4)]
cell = lambda q, b: [s for s in byq[q] if band(s["elev"]) == b]

stock = {(r["band"], r["q"], r["hour"]): r for r in N["stock"]}
def stock_of(bands, qs, h, k="mean"):
    rows = [stock[(b, q, h)] for b in bands for q in qs if (b, q, h) in stock]
    n = sum(r["n"] for r in rows)
    return sum(r[k] * r["n"] for r in rows) / n


# ================= 1. two measures: every station, net outflow (x) against empty share (y); no factor used yet
allst = []
for r in csv.DictReader(open(R / "data/station_master.csv", encoding="utf-8-sig")):
    a = net.get(r["station_id"])
    if r["am_empty_dry"] and a and a[1]:
        allst.append((a[0] / a[1], float(r["am_empty_dry"])))
TH = 0.2
n_all = len(allst)
lose = [p for p in allst if p[0] > 0]
lose_out = [p for p in lose if p[1] >= TH]
gain = n_all - len(lose)
W, H, L, RT, T, B = 1071, 600, 96, 24, 56, 78
XM = 30
x = lambda v: L + (max(-XM, min(XM, v)) + XM) / (2 * XM) * (W - L - RT)
y = lambda v: H - B - v * (H - T - B)
o = []
for v in (0, .2, .4, .6, .8, 1):
    o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{LINE}"/>' + t(L - 12, y(v) + 6, f"{v:.0%}", 18, MUTED, "end"))
for v in range(-30, 31, 10):
    o.append(t(x(v), H - B + 30, f"{v:+d}".replace("-", "−").replace("+0", "0"), 18, MUTED, "middle"))
o.append(t((L + W - RT) / 2, H - 14, "Net outflow, 7–9 am: bikes lost per morning (stations beyond ±30 drawn at the edge)", 19, INK2, "middle"))
o.append(t(L, T - 18, "Empty share, 7–9 am", 20, INK, "start", 700))
o.append(f'<rect x="{x(0):.1f}" y="{T}" width="{x(XM) - x(0):.1f}" height="{y(TH) - T:.1f}" fill="#FFF1F2"/>')
for vx, vy in allst:
    c = GREY if vx <= 0 else (RED if vy >= TH else BLUE)
    o.append(f'<circle cx="{x(vx):.1f}" cy="{y(vy):.1f}" r="3.4" fill="{c}" fill-opacity="{.35 if c == GREY else .55}"/>')
o.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{T}" y2="{H - B}" stroke="#8B95A1" stroke-width="2"/>')
o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y(TH):.1f}" y2="{y(TH):.1f}" stroke="{INK2}" stroke-width="2" stroke-dasharray="6 5"/>')
o.append(t(x(XM) - 8, T + 28, f"loses bikes and runs out: {len(lose_out):,}", 20, RED, "end", 700))
HALO = ' stroke="#fff" stroke-width="6" stroke-linejoin="round" paint-order="stroke"'
o.append(t(x(-XM) + 8, y(TH) - 12, "empty in 1 of 5 readings or more", 17, INK2, "start", None, HALO))
o.append(t(x(XM) - 8, y(0.14), f"loses bikes; empty share <20%: {len(lose) - len(lose_out):,}", 20, BLUE, "end", 700, HALO))
o.append(t(x(-XM) + 8, T + 28, f"gains bikes: {gain:,}", 20, MUTED, "start", 700))
c1 = svg(W, H, f"Each dot is a station: morning net outflow against empty share. {len(lose):,} of {n_all:,} stations lose bikes each morning; "
         f"only {len(lose_out):,} of them are empty in at least one in five morning readings.", o)
s1 = slide("d_measures", "WHAT WE MEASURE", "Losing bikes is not the same as running out", c1,
           sidebox('<p class="note"><b>Net outflow</b>: rentals minus returns, in bikes. Above 0, the station loses bikes; below 0, it gains them.<br>'
                   '<b>Empty share</b>: how often the station has zero bikes at 7, 8 or 9 am.</p>',
                   stat(f"{len(lose) / n_all:.0%}", f"of stations lose bikes every morning: net outflow above 0 ({len(lose):,} of {n_all:,})", "blue"),
                   stat(f"{len(lose_out) / len(lose):.0%}", f"of those have empty share ≥20%: empty in at least one in five morning readings ({len(lose_out):,})", "red")),
           f"We use two measures. The first is net outflow: rentals minus returns, counted in bikes. When it is positive, the station loses bikes; when "
           f"it is negative, it gains them. We compute it for the whole day and for the morning commute; a daily net outflow of plus 4 means the station "
           f"loses four bikes a day on average through user trips. Net outflow tells us where bikes leave. But our question is where they run out, so the second measure is the "
           f"empty share: how often the station has no bike at all at 7, 8 or 9 am. Each dot is one station. Everything right of the line loses bikes in the morning: "
           f"{len(lose) / n_all:.0%} of all stations. But only the red ones, above the dashed line, are empty in at least one in five readings, and that is "
           f"just {len(lose_out) / len(lose):.0%} of the stations that lose bikes. The blue stations have empty share below 20%; they can still run out, just less frequently. "
           "We keep both measures from here on. We considered time of day, weather, terrain and distance to the subway. "
           "First, we look at the usage patterns that help explain our choice of days and commute hours.")

# ================= 2. subway: net outflow and empty share by quarter
W, H = 1071, 600
o = []
px = [(96, 520), (600, 1047)]            # two panels
for p, (a, b) in enumerate(px):
    bw = (b - a) / 4
    if p == 0:
        y0 = lambda v: 300 - v / 4 * 190               # -3..+4
        for v in (-2, 0, 2, 4):  # ticks
            o.append(f'<line x1="{a}" x2="{b}" y1="{y0(v):.1f}" y2="{y0(v):.1f}" stroke="{"#8B95A1" if v == 0 else LINE}"/>' + t(a - 10, y0(v) + 6, f"{v:+d}".replace("-", "−") if v else "0", 18, MUTED, "end"))
        o.append(t(a, 52, "Net outflow, 7–9 am (bikes per day)", 20, INK, "start", 700))
        for q in range(4):
            v = qnet[q]; c = RED if v > 0 else BLUE
            o.append(f'<rect x="{a + q * bw + bw * .18:.1f}" y="{min(y0(0), y0(v)):.1f}" width="{bw * .64:.1f}" height="{abs(y0(v) - y0(0)):.1f}" fill="{c}" rx="4"/>')
            o.append(t(a + (q + .5) * bw, (y0(v) - 12) if v > 0 else (y0(v) + 28), f"{v:+.1f}".replace("-", "−"), 22, c, "middle", 700))
        o.append(t(a + bw, y0(0) - 14, "↑ loses bikes", 17, RED, "middle")); o.append(t(a + 3 * bw, y0(0) + 28, "↓ gains bikes", 17, BLUE, "middle"))
    else:
        y1 = lambda v: 440 - v / .15 * 360
        for v in (0, .05, .10, .15):
            o.append(f'<line x1="{a}" x2="{b}" y1="{y1(v):.1f}" y2="{y1(v):.1f}" stroke="{"#8B95A1" if v == 0 else LINE}"/>' + t(a - 10, y1(v) + 6, f"{v:.0%}", 18, MUTED, "end"))
        o.append(t(a, 52, "Empty share, 7–9 am", 20, INK, "start", 700))
        for q in range(4):
            v = qemp[q]
            o.append(f'<rect x="{a + q * bw + bw * .18:.1f}" y="{y1(v):.1f}" width="{bw * .64:.1f}" height="{y1(0) - y1(v):.1f}" fill="{RED}" fill-opacity=".85" rx="4"/>')
            o.append(t(a + (q + .5) * bw, y1(v) - 12, f"{v:.1%}", 22, RED, "middle", 700))
    for q in range(4):
        o.append(t(a + (q + .5) * bw, 478, QLAB[q].replace(" and over", "+"), 17, MUTED, "middle"))
    o.append(t((a + b) / 2, 512, "distance to the nearest subway station", 18, INK2, "middle"))
c2 = svg(W, H, f"Morning net outflow rises from {qnet[0]:.1f} near the subway to {qnet[3]:+.1f} far from it; empty share rises from {qemp[0]:.1%} to {qemp[3]:.1%}.", o)
s2 = slide("d_subway", "FACTOR 4. DISTANCE TO THE NEAREST SUBWAY STATION",
           "Farther from the subway, more bikes leave", c2,
           sidebox(stat(f"{qnet[3]:+.1f}", f"bikes a morning at stations {cut[2]} m or more from the subway; {qnet[0]:+.1f} within {cut[0]} m".replace("-", "−"), "ink"),
                   stat(f"{qemp[0]:.1%} → {qemp[3]:.1%}", "morning empty share, nearest → farthest quarter"),
                   '<p class="note">A clearer contrast in <b>net movement</b> than in <b>shortage frequency</b>.</p>'),
           f"Next, we looked at subway distance. Stations within about {cut[0]} metres of the subway gain bikes on average in the morning, "
           f"while those {cut[2]} metres or farther away lose almost three. This is consistent with people riding toward the subway. "
           f"Empty share rises from {qemp[0]:.1%} to {qemp[3]:.1%}, a less pronounced contrast than we saw across elevation groups. "
           "So the direction of bicycle movement and the frequency of shortages tell us different things. "
           "We then compared the station characteristics together.")

# ================= 3. coplot elevation x subway
def lowess(xs, ys, grid, span=.75):
    xs, ys = np.asarray(xs), np.asarray(ys); k = max(3, int(np.ceil(span * len(xs)))); out = []
    for g in grid:
        d = np.abs(xs - g); h = np.sort(d)[k - 1]; w = np.clip(1 - (d / h) ** 3, 0, None) ** 3
        X = np.c_[np.ones_like(xs), xs - g]; WX = X * w[:, None]
        beta = np.linalg.lstsq(WX.T @ X, WX.T @ ys, rcond=None)[0]; out.append(beta[0])
    return np.array(out)

W, H = 1071, 640
o = []
pw, ph, gx, top = 230, 400, 22, 92
X0 = 70
for q in range(4):
    a = X0 + q * (pw + gx); b = a + pw
    xx = lambda e: a + min(e, 80) / 80 * pw
    yy = lambda v: top + ph - v * ph
    o.append(f'<rect x="{a}" y="{top - 44}" width="{pw}" height="34" fill="{TINT}" rx="6"/>' + t((a + b) / 2, top - 20, QLAB[q], 17, INK2, "middle", 700))
    o.append(f'<rect x="{xx(40):.1f}" y="{top}" width="{b - xx(40):.1f}" height="{ph}" fill="#FFF1F2"/>')
    for v in (0, .25, .5, .75, 1):
        o.append(f'<line x1="{a}" x2="{b}" y1="{yy(v):.1f}" y2="{yy(v):.1f}" stroke="{LINE}"/>')
        if q == 0: o.append(t(a - 8, yy(v) + 6, f"{v:.0%}", 16, MUTED, "end"))
    for e in (0, 20, 40, 60, 80):
        o.append(t(xx(e), top + ph + 24, e, 16, MUTED, "middle"))
    pts = [s for s in byq[q] if s["elev"] <= 80]
    for s in pts:
        o.append(f'<circle cx="{xx(s["elev"]):.1f}" cy="{yy(s["empty"]):.1f}" r="2.6" fill="{GREY}" fill-opacity=".55"/>')
    grid = np.linspace(min(s["elev"] for s in pts), max(s["elev"] for s in pts), 40)
    fit = np.clip(lowess([s["elev"] for s in pts], [s["empty"] for s in pts], grid), 0, 1)
    o.append(f'<polyline points="{" ".join(f"{xx(g):.1f},{yy(v):.1f}" for g, v in zip(grid, fit))}" fill="none" stroke="{RED}" stroke-width="4"/>')
    hv = mean([s["empty"] for s in cell(q, "hill")]); fv = mean([s["empty"] for s in cell(q, "flat")])
    o.append(t(a + 8, top + 26, f"40 m and above: {hv:.0%}", 17, RED, "start", 700))
    o.append(t(a + 8, top + 50, f"below 20 m: {fv:.0%}", 17, MUTED, "start", 700))
o.append(t(X0 + 2 * (pw + gx) - gx / 2, top + ph + 56, "Station elevation, bare earth (m)", 18, INK2, "middle"))
o.append(t(X0, 26, "Given: distance to the nearest subway station", 18, INK2, "start", 700))
o.append(f'<text transform="translate(20 {top + ph / 2}) rotate(-90)" text-anchor="middle" font-size="18" fill="{INK2}">Empty share, 7–9 am</text>')
c3 = svg(W, H, "Coplot of empty share against elevation in four panels of subway distance; the LOESS curve rises with elevation in every panel.", o)
hills = [mean([s["empty"] for s in cell(q, "hill")]) for q in range(4)]
s3 = slide("d_cop_subway", "FACTORS TOGETHER", "Near the subway or far from it, the hill-top stations run out", c3,
           sidebox(stat(f"{min(hills):.0%}–{max(hills):.0%}", "empty share at 40 m and above, in every quarter of subway distance"),
                   stat("≈ 5%", "on flat ground below 20 m, in every quarter", "ink"),
                   '<p class="note">Subway distance moves the flow; elevation decides who runs out.</p>',
                   note="Coplot: one panel per quarter of subway distance; LOESS (span 0.75), stations up to 80 m; 2025 dry weekdays."),
           "Now two factors together. Each panel holds the stations in one quarter of subway distance, from the closest on the left to the farthest "
           f"on the right, and the red curve is a LOESS fit of empty share on elevation. The shape is the same in every panel: about 5 percent "
           f"on flat ground and {min(hills):.0%} to {max(hills):.0%} on the hills. Near the subway or far from it, what decides whether a station runs out is the hill.")

# ================= 4. elevation x weather
TL = ["< 0", "0–5", "5–10", "10–15", "15–20", "20–25", "25+"]
wx = {(r["band"], r["temp"]): r for r in N["wx"]}
W, H, L, RT, T, B = 1071, 600, 90, 150, 60, 92
x = lambda i: L + (i + .5) / 7 * (W - L - RT)
y = lambda v: T + (2.4 - v) / 3.6 * (H - T - B)
o = []
for v in (-1, 0, 1, 2):
    o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{"#8B95A1" if v == 0 else LINE}" stroke-width="{2 if v == 0 else 1}"/>' + t(L - 10, y(v) + 6, f"{v:+d}".replace("-", "−") if v else "0", 18, MUTED, "end"))
for i, l in enumerate(TL):
    o.append(t(x(i), H - B + 30, l, 18, MUTED, "middle"))
o.append(t((L + W - RT) / 2, H - B + 62, "Morning temperature at the station's nearest weather station, 7–9 am (°C)", 18, INK2, "middle"))
o.append(t(L, T - 22, "Net outflow, 7–9 am (bikes per station per morning)", 20, INK, "start", 700))
o.append(t(W - RT + 8, y(0) - 10, "loses ↑", 17, RED)); o.append(t(W - RT + 8, y(0) + 26, "gains ↓", 17, BLUE))
for bnd, c, lab in (("hill", RED, "40 m and above"), ("mid", "#F7A1A8", "20–40 m"), ("flat", BLUE, "below 20 m")):
    vs = [wx[(bnd, l)]["net"] for l in TL]
    o.append(f'<polyline points="{" ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vs))}" fill="none" stroke="{c}" stroke-width="5" stroke-linejoin="round"/>')
    for i, v in enumerate(vs):
        o.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="6" fill="{c}"/>')
    o.append(t(x(6) + 16, y(vs[-1]) + 6, lab, 18, c, "start", 700))
c4 = svg(W, H, "Morning net outflow by morning temperature: hill-top stations lose bikes and flat stations gain them in every temperature band.", o)
hv = [wx[("hill", l)]["net"] for l in TL]; fv = [wx[("flat", l)]["net"] for l in TL]
nwx = N["wx_rows"]
s4 = slide("d_wx_elev", "FACTORS TOGETHER", "At every temperature, the hills lose bikes and the flat ground gains them", c4,
           sidebox(stat(f"{min(hv):+.1f} to {max(hv):+.1f}", "bikes lost by a hill-top station each morning, depending on the temperature band"),
                   stat(f"{max(fv):+.1f} to {min(fv):+.1f}".replace("-", "−"), "on flat ground: it gains bikes at every temperature", "blue"),
                   '<p class="note">Weather changes <b>how many</b> bikes move, not <b>which way</b>.</p>',
                   note=f"{nwx:,} station-mornings, 2024–2025 clear weekdays; temperature = mean of the 7, 8 and 9 am readings at the nearest KMA AWS."),
           "Earlier we saw that weather changes how many people ride. Does it change where the bikes go? No. In every temperature band, from below "
           f"zero to above 25 degrees, hill-top stations lose bikes, between {min(hv):.1f} and {max(hv):.1f} a morning, and flat stations gain them. "
           "Warm mornings move a few more bikes, cold mornings fewer, but always in the same direction.")

# ================= 5. buffer
types = [("Flat, near the subway", ["flat"], [0]), ("Flat, far from the subway", ["flat"], [3]),
         ("Hill, near the subway", ["hill"], [0]), ("Hill, far from the subway", ["hill"], [3])]
W, H, L, RT = 1071, 600, 300, 150
x = lambda v: L + v / 20 * (W - L - RT)
o = [t(L, 40, "Bikes at the station at 7 am → 9 am", 20, INK, "start", 700), t(W - RT + 30, 40, "Empty share", 20, INK, "start", 700)]
for v in (0, 5, 10, 15, 20):
    o.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="64" y2="520" stroke="{LINE}"/>' + t(x(v), 548, v, 18, MUTED, "middle"))
for j, (lab, bs, qs_) in enumerate(types):
    yc = 120 + j * 112
    a, b = stock_of(bs, qs_, 7), stock_of(bs, qs_, 9)
    e = mean([stock_of(bs, qs_, h, "empty") for h in (7, 8, 9)])
    hillish = bs == ["hill"]
    c = RED if hillish else NAVY
    o.append(t(L - 20, yc + 7, lab, 20, INK, "end", 700 if hillish else None))
    o.append(f'<line x1="{x(min(a, b)):.1f}" x2="{x(max(a, b)):.1f}" y1="{yc}" y2="{yc}" stroke="{c}" stroke-width="6" stroke-opacity=".35"/>')
    o.append(f'<circle cx="{x(a):.1f}" cy="{yc}" r="10" fill="#fff" stroke="{c}" stroke-width="4"/><circle cx="{x(b):.1f}" cy="{yc}" r="11" fill="{c}"/>')
    o.append(t(x(b), yc - 20, f"{b:.1f}", 18, c, "middle", 700))
    o.append(t(x(a), yc + 34, f"{a:.1f}", 16, MUTED, "middle"))
    o.append(t(W - RT + 30, yc + 8, f"{e:.0%}", 26, RED if e > .15 else MUTED, "start", 700))
o.append(f'<circle cx="{L + 8}" cy="578" r="8" fill="#fff" stroke="{MUTED}" stroke-width="3"/>' + t(L + 24, 584, "7 am", 17))
o.append(f'<circle cx="{L + 110}" cy="578" r="9" fill="{MUTED}"/>' + t(L + 126, 584, "9 am", 17))
c5 = svg(W, H, "Mean bikes at 7 and 9 am for four kinds of station: flat stations keep twelve or more bikes even after losing some; hill-top stations hold about four.", o)
ff7, ff9 = stock_of(["flat"], [3], 7), stock_of(["flat"], [3], 9)
h9 = stock_of(["hill"], [0, 1, 2, 3], 9)
s5 = slide("d_buffer", "FACTORS TOGETHER", "Flat stations lose bikes but keep a buffer; hill-top stations have none", c5,
           sidebox(stat(f"{ff7:.0f} → {ff9:.0f}", "bikes at a flat station far from the subway: it loses the most, and keeps the most", "ink"),
                   stat(f"{h9:.0f}", "bikes left at a hill-top station at 9 am: one or two rentals empty it"),
                   '<p class="note">Bikes ride down all day and fill the flat ground. The ones that leave the hills do not come back up.</p>',
                   note="Mean hourly stock, 2025 dry weekdays; empty share over the 7, 8 and 9 am readings."),
           f"So why do stations far from the subway lose the most bikes and still not run out? Because they keep a buffer. At 7 am a flat station far from "
           f"the subway has about {ff7:.0f} bikes, and after the rush it still has {ff9:.0f}. A hill-top station has about {h9:.0f}, because the bikes that went "
           "down never ride back up. Losing one or two is enough to empty it. Many stations lose bikes in the morning; only the hills cannot get them back.")

W, H = 1664, 650
plot_top, plot_bottom = 100, 390
stock_y = lambda value: plot_bottom - value / 20 * (plot_bottom - plot_top)
parts = []
for value in (0, 5, 10, 15, 20):
    yy = stock_y(value)
    parts.append(f'<line x1="100" x2="1570" y1="{yy}" y2="{yy}" stroke="{LINE}"/>'
                 + t(80, yy + 7, value, 21, MUTED, 'end'))
buffer_values = []
for bnd, label, color, left in [('flat', 'Flat stations', BLUE, 280), ('hill', 'Hill stations', RED, 1050)]:
    start, end = stock_of([bnd], [3], 7), stock_of([bnd], [3], 9)
    empty = mean([stock_of([bnd], [3], hour, 'empty') for hour in (7, 8, 9)])
    buffer_values.append((start, end, empty))
    center = left + 166
    parts.append(t(center, 38, label, 34, color, 'middle', 700))
    for j, (value, hour) in enumerate([(start, '7 am'), (end, '9 am')]):
        xx, yy = left + j * 200, stock_y(value)
        parts.append(f'<rect x="{xx}" y="{yy:.1f}" width="132" height="{plot_bottom-yy:.1f}" '
                     f'fill="{color}" fill-opacity="{.38 if j == 0 else 1}" rx="5"/>')
        parts.append(t(xx + 66, yy - 14, f'{value:.1f}', 31, INK, 'middle', 700))
        parts.append(t(xx + 66, 423, hour, 24, INK2, 'middle'))
    parts.append(t(center, 465, f'Stock change: {end-start:+.1f} bikes'.replace('-', '−'), 24, MUTED, 'middle'))
    parts.append(t(center, 548, f'{empty:.0%}', 68, color, 'middle', 700))
    parts.append(t(center, 585, 'empty share', 25, INK2, 'middle'))
parts.append(t(100, 637, 'Bars: mean available bicycles (group means). Empty share: zero-bike readings at 7, 8 and 9 am, 2025 dry weekdays.', 20, MUTED))
buffer_chart = svg(W, H, 'Far from the subway: flat stations start with 19.0 bikes and end with 15.0, with 5% empty share; '
                   'hill stations start with 5.9 and end with 5.4, with 28% empty share. Both groups use the same zero-baseline scale.', parts)
flat_start, flat_end, flat_empty = buffer_values[0]
hill_start, hill_end, hill_empty = buffer_values[1]
s5 = f"""<section id="d_buffer" data-transition="fade">
<p class="eyebrow">STARTING INVENTORY</p>
<h2>Fewer bikes, more shortages</h2>
<p style="font-size:26px;color:var(--muted);margin:16px 0 0">Both groups are far from the subway: the farthest distance quarter ({cut[2]} m and above).</p>
<div style="margin-top:12px">{buffer_chart}</div>
{FOOT}
<aside>Bikes tend to move downhill. But movement alone does not tell us whether a station runs out—the number of bicycles available at the start also matters.
Here, both groups are far from the subway. Flat stations start with {flat_start:.0f} bicycles and still have {flat_end:.0f} at 9 am.
Hill stations start with about {hill_start:.0f}, and their empty share is {hill_empty:.0%}, compared with {flat_empty:.0%} on flat ground.
Despite a smaller decline in average stock, hill stations are empty more frequently. These are group averages, and stock changes can include non-trip activity.
Starting inventory helps us understand shortages. A separate question is whether the bicycles lost in the morning come back later.
To explore that, we classified stations using morning and full-day net outflow.</aside>
</section>"""


# ================= slide "traits": which station features go with running out (logistic model, the 20% line of d_measures)
def _logit(X, y, it=50):
    A = np.column_stack([np.ones(len(y)), X]); b = np.zeros(A.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-A @ b)); W = p * (1 - p)
        step = np.linalg.solve(A.T @ (A * W[:, None]), A.T @ (y - p)); b += step
        if np.abs(step).max() < 1e-10:
            break
    p = 1 / (1 + np.exp(-A @ b)); cov = np.linalg.inv(A.T @ (A * (p * (1 - p))[:, None]))
    return b, np.sqrt(np.diag(cov)), p


def _ranks(v):
    v = np.asarray(v, float); o = np.argsort(v, kind="mergesort"); r = np.empty(len(v)); r[o] = np.arange(1, len(v) + 1)
    for u in np.unique(v[np.r_[False, np.diff(v[o]) == 0][np.argsort(o)]] if len(v) else []):
        k = v == u; r[k] = r[k].mean()
    return r


_emp = {r["station_id"]: float(r["am_empty_dry"]) for r in csv.DictReader(open(R / "data/station_master.csv", encoding="utf-8-sig")) if r["am_empty_dry"]}
_rows = []
for r in csv.DictReader(open(R / "data/od_2024_2025/od/s0_station_summary.csv", encoding="utf-8-sig")):
    if r["enough_days"] == "True" and r["st_id"] in _emp and r["elevation_m"] and r["relief_300m"] and r["subway_dist_m"] and float(r["subway_dist_m"]) > 0:
        _rows.append((float(r["elevation_m"]), float(r["relief_300m"]), float(np.log(float(r["subway_dist_m"]))), _emp[r["st_id"]]))
_D = np.array(_rows); _X = _D[:, :3]; _share = _D[:, 3]; _y = (_share >= TH).astype(float)
_Z = (_X - _X.mean(0)) / _X.std(0, ddof=1)
_b, _se, _p = _logit(_Z, _y)
_b10, _, _ = _logit(np.column_stack([_X[:, 0] / 10, _X[:, 1], _X[:, 2]]), _y)
_rr = _ranks(_p); _n1 = _y.sum(); _n0 = len(_y) - _n1
AUC16 = (_rr[_y == 1].sum() - _n1 * (_n1 + 1) / 2) / (_n1 * _n0)
_rho = [float(np.corrcoef(_ranks(_X[:, k]), _ranks(_share))[0, 1]) for k in range(3)]
_pv = [math.erfc(abs(b / e) / math.sqrt(2)) for b, e in zip(_b[1:], _se[1:])]
_pf = lambda v: "&lt; 0.001" if v < 0.001 else f"{v:.2f}"
_names = ["Elevation (m)", "Local relief within 300 m (m)", "Distance to nearest subway station (log)"]
_trs = "".join(('<tr class="hl">' if k == 0 else "<tr>") + f"<td>{_names[k]}</td><td{RT_}>{_rho[k]:.2f}</td>"
               f"<td{RT_}>{np.exp(_b[k + 1]):.2f} ({np.exp(_b[k + 1] - 1.96 * _se[k + 1]):.2f}–{np.exp(_b[k + 1] + 1.96 * _se[k + 1]):.2f})</td>"
               f"<td{RT_}>{_pf(_pv[k])}</td></tr>\n" for k in range(3))
OR10 = float(np.exp(_b10[1])); SD_E = float(_X[:, 0].std(ddof=1))
TRAITS = f"""<section id="traits" data-transition="fade">
<p class="eyebrow">FACTORS TOGETHER</p>
<h2>Of the station features we tested, only elevation goes with running out</h2>
<table class="tbl" style="margin-top:40px">
<tr><th style="width:40%">Station feature</th><th style="width:20%;text-align:right">Rank correlation with empty share (ρ)</th><th style="width:26%;text-align:right">Odds ratio per 1 SD (95% CI)</th><th style="width:14%;text-align:right">p</th></tr>
{_trs}</table>
<p class="text muted" style="margin-top:28px">Outcome: runs out, empty in at least 20% of 7–9 am readings (2025 dry weekdays): {int(_n1):,} of {len(_y):,} stations. One logistic model with all three features, standardised. Elevation: odds ×{OR10:.2f} for every 10 m; AUC {AUC16:.2f}.</p>
{FOOT}
<aside>Which station features go with running out? We put three of them in one logistic model. The outcome is whether a station runs out, as we defined it
earlier: empty in at least one in five readings between 7 and 9 am, which holds for {int(_n1):,} of {len(_y):,} stations. The first column is the rank
correlation with the empty share, one feature at a time; the second is the odds ratio for one standard deviation, with all three features together.
Only elevation matters. One standard deviation higher, about {SD_E:.0f} metres, multiplies the odds of running out by {np.exp(_b[1]):.1f}; that is
{OR10:.1f} times for every 10 metres. Local relief goes with running out on its own, but not once elevation is in the model, and distance to the
subway hardly matters. The model tells stations that run out from those that do not with an AUC of {AUC16:.2f}.</aside>
</section>"""


# ================= slide "why": operating deficit motivates examining redistribution
WHY = f"""<section id="why" data-transition="fade">
<p class="eyebrow">WHY THIS MATTERS</p>
<h2>A growing operating deficit led us to look at redistribution</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;margin-top:64px">
<div style="background:var(--tint);border-radius:24px;padding:40px">
<p style="font-size:26px;color:var(--muted);margin:0 0 24px">Operating deficit · 2022 → 2025</p>
<p style="font-size:68px;font-weight:700;line-height:1.15;letter-spacing:-1.5px;margin:0">₩9.4 bn → ₩17.6 bn</p>
<p style="font-size:28px;line-height:1.4;color:var(--ink2);margin:24px 0 0">Nearly doubled in three years</p>
</div>
<div style="background:var(--tint);border-radius:24px;padding:40px">
<p style="font-size:26px;color:var(--muted);margin:0 0 24px">Redistribution staff time</p>
<p style="font-size:88px;font-weight:700;line-height:1;color:var(--blue);margin:0">53%</p>
<p style="font-size:28px;line-height:1.4;color:var(--ink2);margin:24px 0 0">of operating cost, according to Bike Magazine</p>
</div>
</div>
<p style="font-size:34px;line-height:1.5;margin:44px 0 0">Redistribution moves bicycles from stations with a surplus to those with shortages.</p>
<p style="font-size:26px;line-height:1.5;color:var(--muted);margin:16px 0 0">Understanding these imbalances can help the city assess redistribution needs.</p>
{FOOT}
<aside>We began with the operating deficit. It grew from 9.4 billion won in 2022 to 17.6 billion won in 2025, nearly doubling in three years.
This led us to look at the costs of running the service. According to Bike Magazine, 53% of operating cost is staff time spent redistributing bicycles.
This is the work of moving bikes from stations with a surplus to stations with shortages. That made redistribution an important motivation for our study.
We wanted to provide insights by understanding the factors associated with bicycle imbalances and shortages.</aside>
</section>"""


# ================= slide "scope" as DATA: how the days and stations were chosen (a funnel), and the sources as icons
# counts: data/od_2024_2025/od/s0_qa.txt (720 days with clean records; 378 dry weekdays, 238 weekends and holidays, 104 rainy weekdays;
# 2,878 stations, 2,843 with at least 50 dry weekdays)
_STEPS = [(731, "Calendar days, 2024–2025", ""),
          (720, "Clean records", "−11 with incomplete records"),
          (482, "Weekdays", "−238 weekends and public holidays"),
          (378, "Dry weekdays", "−104 with 1 mm of rain or more")]
_fw, _bh, _gap = 640, 62, 34
_rows = []
for k, (n, lab, cut_) in enumerate(_STEPS):
    yy = 20 + k * (_bh + _gap); w = n / _STEPS[0][0] * _fw; last = k == len(_STEPS) - 1
    _rows.append(f'<rect x="0" y="{yy}" width="{w:.1f}" height="{_bh}" rx="12" fill="{BLUE if last else "#DCE8FD"}"/>'
                 + t(20, yy + 42, f"{n:,}", 32, "#fff" if last else INK, "start", 700)
                 + t(w + 24, yy + 28, lab, 24, INK, "start", 700)
                 + (t(w + 24, yy + 54, cut_, 19, MUTED) if cut_ else ""))
_funnel = svg(1060, 20 + 4 * (_bh + _gap), "Days kept at each step: 731 calendar days, 720 with clean records, 482 weekdays, 378 dry weekdays.", _rows)
_G = 'stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
_SRC = [("Trips", "5-minute records", f'<path d="M18 26 H44 M38 20 L44 26 L38 32 M46 38 H20 M26 32 L20 38 L26 44" {_G}/>'),
        ("Bikes at stations", "hourly, 2025", f'<rect x="18" y="34" width="6" height="12" fill="#fff"/><rect x="29" y="24" width="6" height="22" fill="#fff"/><rect x="40" y="30" width="6" height="16" fill="#fff"/>'),
        ("Weather", "27 KMA stations, hourly", f'<path d="M22 36 a8 8 0 0 1 2-15 a10 10 0 0 1 19 3 a7 7 0 0 1-1 12 Z" {_G}/><path d="M26 42 l-2 5 M34 42 l-2 5 M42 42 l-2 5" {_G}/>'),
        ("Elevation", "1:5,000 contour map", f'<path d="M14 46 L28 24 L36 35 L41 29 L50 46 Z" {_G}/>'),
        ("Subway", "every station in Seoul", f'<rect x="21" y="16" width="22" height="26" rx="5" {_G}/><path d="M21 31 H43 M26 48 L29 42 M38 48 L35 42" {_G}/><circle cx="27" cy="36" r="1.6" fill="#fff"/><circle cx="37" cy="36" r="1.6" fill="#fff"/>')]
_chips = "".join(f'<div style="display:flex;align-items:center;gap:16px;flex:1">'
                 f'<svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true" style="flex:0 0 auto"><circle cx="32" cy="32" r="32" fill="{BLUE}"/>{g}</svg>'
                 f'<div><p style="font-size:22px;font-weight:700;margin:0;color:var(--ink)">{h}</p><p style="font-size:18px;margin:2px 0 0;color:var(--muted)">{sub}</p></div></div>'
                 for h, sub, g in _SRC)
SCOPE = f"""<section id="scope" data-transition="fade">
<p class="eyebrow">DATA</p>
<h2>378 dry weekdays, 2,843 stations</h2>
<div style="display:flex;gap:40px;margin-top:36px;align-items:center">
<div style="flex:0 0 1060px">{_funnel}</div>
<div style="flex:1;background:var(--tint);border-radius:24px;padding:32px 34px">
<p style="font-size:24px;font-weight:700;margin:0;color:var(--ink)">Stations</p>
<p style="font-size:72px;font-weight:700;line-height:1.1;margin:10px 0 0;color:var(--blue)">2,843</p>
<p style="font-size:21px;line-height:1.45;margin:10px 0 0;color:var(--ink2)">with records on at least 50 of the 378 days, of 2,878 in the trip data</p>
</div>
</div>
<div style="display:flex;gap:24px;margin-top:34px;padding:22px 30px;border-top:2px solid var(--line)">{_chips}</div>
{FOOT}
<aside>To answer it, we use every trip between Seoul's bike stations in 2024 and 2025. Of the 731 days, 720 have clean records: we dropped
ten days where rentals and returns did not match, and one empty file. Then we keep weekdays that are not public holidays, 482 days, and of those
the dry ones, under 1 mm of rain: 378 days. Weekends follow a different pattern from the commute, and rain changes how many people ride. That leaves
2,843 stations with records on at least 50 of those days. We also use the hourly bikes at every station in 2025, weather from 27 weather stations,
elevation from the city's contour map, and the subway stations. Next: what we measure on those days.</aside>
</section>"""

# ================= slide "intro": the four text cards become a three-step strip; title without a colon
def _icon(glyph):
    return (f'<svg width="84" height="84" viewBox="0 0 84 84" aria-hidden="true"><circle cx="42" cy="42" r="42" fill="{BLUE}"/>{glyph}</svg>')


_W = 'stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"'
_QR = (f'<rect x="21" y="21" width="15" height="15" rx="2" {_W}/><rect x="48" y="21" width="15" height="15" rx="2" {_W}/>'
       f'<rect x="21" y="48" width="15" height="15" rx="2" {_W}/><rect x="49" y="49" width="6" height="6" fill="#fff"/>'
       f'<rect x="57" y="57" width="6" height="6" fill="#fff"/><rect x="57" y="47" width="5" height="5" fill="#fff"/><rect x="48" y="58" width="5" height="5" fill="#fff"/>')
_BIKE = (f'<circle cx="27" cy="51" r="10" {_W}/><circle cx="58" cy="51" r="10" {_W}/>'
         f'<path d="M27 51 L37 34 H52 L58 51 M37 34 L44 51 H27 M48 27 H55" {_W}/>')
_LOCK = (f'<path d="M33 40 V33 a9 9 0 0 1 18 0 V40" {_W}/><rect x="27" y="40" width="30" height="23" rx="4" fill="#fff"/>'
         f'<circle cx="42" cy="51" r="3.5" fill="{BLUE}"/>')
_ARROW = ('<svg width="36" height="40" viewBox="0 0 36 40" aria-hidden="true" style="flex:0 0 auto;margin-bottom:58px">'
          '<path d="M10 6 L26 20 L10 34" stroke="#B0B8C1" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def _step(glyph, head, sub):
    return (f'<div style="display:flex;flex-direction:column;align-items:center;gap:8px;width:250px;text-align:center">{_icon(glyph)}'
            f'<p style="font-size:26px;font-weight:700;margin:6px 0 0;color:var(--ink)">{head}</p>'
            f'<p style="font-size:20px;margin:0;color:var(--muted)">{sub}</p></div>')


INTRO_STRIP = ('<div style="display:flex;align-items:center;justify-content:center;gap:48px;background:var(--tint);border-radius:24px;padding:26px 36px;margin-top:24px">'
               + _step(_QR, "Rent", "Scan the QR code in the app") + _ARROW
               + _step(_BIKE, "Ride", "Travel to your destination") + _ARROW
               + _step(_LOCK, "Return", "Lock the bike at any station")
               + '</div>\n')
INTRO_TITLE = "Rent a bike at one station, return it at any other"


def intro(sec):
    """The built intro slide with the strip in place of the four text cards and a title without a colon."""
    i = sec.index('<div style="display:grid;grid-template-columns:repeat(4,1fr)')
    j = sec.index('<p style="font-size:16px;color:var(--muted)', i)
    sec = sec[:i] + INTRO_STRIP + sec[j:]
    sec, k = re.subn(r"<h2>.*?</h2>", f"<h2>{INTRO_TITLE}</h2>", sec, count=1, flags=re.S)
    assert k == 1
    return sec


# ================= slide "cover": a Ddareungi photo on the right half, the title on the left; no caption and no data line
# photo: "Bicycle-sharing station in Seoul 1", Sarang, public domain, Wikimedia Commons (slides/photos/CREDITS.md)
import base64 as _b64
_COVER_IMG = "data:image/jpeg;base64," + _b64.b64encode((R / "slides/photos/station_row_seoul_1.jpg").read_bytes()).decode("ascii")


def cover(sec):
    """The cover as photo + title; keeps the speaker note."""
    note = re.search(r"<aside>.*?</aside>", sec, re.S).group(0)
    return ('<section id="cover" class="dark" data-transition="fade">'
            f'<img src="{_COVER_IMG}" alt="Seoul Bike bicycles in a row at a station on a sunny pavement." '
            'style="position:absolute;right:0;top:0;width:900px;height:1080px;object-fit:cover;object-position:38% 50%">'
            '<div style="position:absolute;left:128px;top:0;bottom:0;width:820px;display:flex;flex-direction:column;justify-content:center">'
            '<p class="eyebrow">STA3115 EXPLORATORY DATA ANALYSIS, FINAL PROJECT</p>'
            '<h1 style="max-width:800px">Exploring Bicycle Imbalances</h1>'
            '<p class="byline">Group 1, November 26, 2026</p></div>'
            + note + '</section>')


# ================= last fixes on the built deck (applied in build_final_deck.py after the teammates' passes)
_CLIP = ("const _cp = el('clipPath', { id: '%s' }, el('defs', {}, %s)); "
         "D.gu.forEach(u => el('path', { d: u.d }, _cp)); ")


def final_fixes(html):
    def rep(old, new, n=1):
        nonlocal html
        assert html.count(old) == n, (old[:70], html.count(old))
        html = html.replace(old, new)

    # slide 8: no "hover" hint on the slide (the presenter shows it)
    rep('<p class="note muted" style="font-size:24px">Hover over a dot to name the station.</p>', '')
    # slide 9: ground 50 m and higher clipped to Seoul's outline
    rep("const hill = el('g', {}, svg);",
        "const hill = el('g', {}, svg); " + _CLIP % ("clip-stmap", "svg") + "hill.setAttribute('clip-path', 'url(#clip-stmap)');")
    # slide 12: drawn here as static SVG (city map left; 69% and the Yonsei–Sinchon inset right); same steps, same note
    import json
    D = json.loads(re.search(r'<script[^>]*id="ixdata"[^>]*>(.*?)</script>', html, re.S).group(1))
    m = re.search(r'<section\b[^>]*id="vec".*?</section>', html, re.S)
    note = re.search(r"<aside>.*?</aside>", m.group(0), re.S).group(0)
    html = html[:m.start()] + _vec_section(D, note) + html[m.end():]
    a = html.index("  // ---------- flow field (whole city) and the zoom ----------")
    b = html.index("  // ----------", a + 20)
    html = html[:a] + _VEC_JS + html[b:]
    return html


_RAMP = lambda e: "#f8fafc" if e < 20 else "#f1f0ea" if e < 40 else "#e7e1d3" if e < 70 else "#dbcfb8" if e < 120 else "#cdbb9a"


def _city_arrow(a):
    ln = min(30, 7 + 2.6 * math.sqrt(a["m"])); n = math.hypot(a["u"], a["v"]) or 1; ux, uy = a["u"] / n, a["v"] / n
    x1, y1, x2, y2 = a["x"] - ux * ln / 2, a["y"] - uy * ln / 2, a["x"] + ux * ln / 2, a["y"] + uy * ln / 2
    hx, hy, hl = -uy, ux, min(8, ln * .4)
    return (f"M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}M{x2 - ux * hl + hx * hl * .55:.1f},{y2 - uy * hl + hy * hl * .55:.1f}"
            f"L{x2:.1f},{y2:.1f}L{x2 - ux * hl - hx * hl * .55:.1f},{y2 - uy * hl - hy * hl * .55:.1f}")


def _vec_section(D, note):
    F, Z = D["frame"], D["zoom"]
    # ---- left: the city, ground clipped to its outline; grey arrows (step 1), coloured arrows (step 2 on)
    city = ['<defs><clipPath id="vec-clip">' + "".join(f'<path d="{u["d"]}"/>' for u in D["gu"]) + "</clipPath></defs>",
            '<g clip-path="url(#vec-clip)">' + "".join(
                f'<rect x="{t["x"]}" y="{t["y"]}" width="{F["cell"] + .4}" height="{F["cell"] + .4}" fill="{_RAMP(t["e"])}"/>' for t in D["terrain"]) + "</g>",
            "".join(f'<path d="{u["d"]}" fill="none" stroke="#fff" stroke-width="1.4" vector-effect="non-scaling-stroke"/>' for u in D["gu"])]
    sw = lambda a: min(3.2, 1.1 + a["m"] / 40)
    grey = "".join(f'<path d="{_city_arrow(a)}" stroke="#6b7684" stroke-width="{sw(a):.2f}"/>' for a in D["vec"]["day"])
    colr = {"down": RED, "up": BLUE, "side": "#d1d6db", "flat": "#e5e8eb"}
    order = sorted(D["vec"]["day"], key=lambda a: a["c"] in ("down", "up"))
    col = "".join(f'<path d="{_city_arrow(a)}" stroke="{colr[a["c"]]}" stroke-width="{sw(a) + (.4 if a["c"] in ("down", "up") else 0):.2f}"/>' for a in order)
    gattr = 'fill="none" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"'
    city.append(f'<g class="v-grey" {gattr}>{grey}</g><g class="v-col" {gattr} style="opacity:0">{col}</g>')
    CW = 780; CH = round(CW * F["h"] / 1000)
    city_svg = (f'<svg width="{CW}" height="{CH}" viewBox="0 0 1000 {F["h"]}" role="img" aria-label="Net bicycle flow across Seoul, one arrow per 1 km cell, '
                f'over the terrain; red arrows run downhill, blue uphill.">' + "".join(city) + "</svg>")
    # ---- right bottom: Yonsei–Sinchon, the 30 strongest net connections between 500 m cells (cropped to where they are)
    zmax = max(a["net"] for a in Z["arrows"])
    Y0 = 280; ZH = Z["h"] - Y0
    near = lambda x, y: min(Z["terrain"], key=lambda t: (t["x"] + Z["cell"] / 2 - x) ** 2 + (t["y"] + Z["cell"] / 2 - y) ** 2)["e"]
    ins = [f'<defs><clipPath id="vec-inset"><rect x="0" y="{Y0}" width="1000" height="{ZH}" rx="36"/></clipPath></defs><g clip-path="url(#vec-inset)">',
           f'<rect x="0" y="{Y0}" width="1000" height="{ZH}" fill="#f8fafc"/>']
    ins += [f'<rect x="{t["x"]:.1f}" y="{t["y"]:.1f}" width="{Z["cell"] + 1:.1f}" height="{Z["cell"] + 1:.1f}" fill="{_RAMP(t["e"])}"/>' for t in Z["terrain"]
            if -Z["cell"] < t["x"] < 1000 and Y0 - Z["cell"] < t["y"] < Z["h"]]
    ins += [f'<path d="{c["d"]}" fill="none" stroke="#8a6d4b" stroke-width="{1.6 if c["level"] == 50 else 1}" stroke-opacity=".45" vector-effect="non-scaling-stroke"/>'
            for c in Z["contours"]]
    halos, lines, heads = [], [], []
    for a in sorted(Z["arrows"], key=lambda a: (a["c"] == "down", a["net"])):
        dx, dy = a["x2"] - a["x1"], a["y2"] - a["y1"]; n = math.hypot(dx, dy)
        if not n:
            continue
        ux, uy = dx / n, dy / n; hx, hy = -uy, ux
        main = a["c"] in ("down", "up")
        w = (7 + 14 * a["net"] / zmax) * (1 if main else .6)
        head = min(52, n * .3, 3.2 * w + 18); half = head * .55
        x1, y1 = a["x1"] + ux * 8, a["y1"] + uy * 8
        tx, ty = a["x2"] - ux * 10, a["y2"] - uy * 10
        bx, by = tx - ux * head, ty - uy * head
        c = RED if a["c"] == "down" else BLUE if a["c"] == "up" else "#b0b8c1"
        halos.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#fff" stroke-width="{w + 8:.1f}" stroke-linecap="round"/>')
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{c}" stroke-width="{w:.1f}" stroke-linecap="round"/>')
        heads.append(f'<polygon points="{tx:.1f},{ty:.1f} {bx + hx * half:.1f},{by + hy * half:.1f} {bx - hx * half:.1f},{by - hy * half:.1f}" fill="{c}" stroke="#fff" stroke-width="3"/>')
    ins += halos + lines + heads
    # the campus as a soft dashed area (smooth closed curve through the outline points), drawn under the arrows
    P = Z["campus"]; k = len(P)
    seg_ = []
    for i in range(k):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % k], P[(i + 2) % k]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        seg_.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    campus_d = f"M{P[0][0]:.1f},{P[0][1]:.1f}" + "".join(seg_) + "Z"
    campus_el = (f'<path d="{campus_d}" fill="#fff" fill-opacity=".28" stroke="{INK}" stroke-width="6" stroke-opacity=".55" '
                 f'stroke-dasharray="20 14" stroke-linejoin="round"/>')
    ins.insert(ins.index(halos[0]) if halos else len(ins), campus_el)
    for l in Z["labels"]:
        e = near(l["x"], l["y"])
        if l["en"].startswith("Sinchon"):
            # the station as a dot, the name beside it
            ins.append(f'<circle cx="{l["x"]}" cy="{l["y"]}" r="22" fill="{INK}" stroke="#fff" stroke-width="9"/>')
            tx, anchor = l["x"] + 40, "start"
            ins.append(f'<text x="{tx}" y="{l["y"] + 18}" text-anchor="{anchor}" font-size="58" font-weight="700" fill="{INK}" stroke="#fff" stroke-width="14" '
                       f'paint-order="stroke" stroke-linejoin="round">{l["en"]}<tspan x="{tx}" dy="62" font-size="48" font-weight="600" fill="{INK2}">{e} m</tspan></text>')
        else:
            ins.append(f'<text x="{l["x"]}" y="{l["y"]}" text-anchor="middle" font-size="58" font-weight="700" fill="{INK}" stroke="#fff" stroke-width="14" '
                       f'paint-order="stroke" stroke-linejoin="round">{l["en"]}<tspan x="{l["x"]}" dy="62" font-size="48" font-weight="600" fill="{INK2}">{e} m</tspan></text>')
    ins.append("</g>" + f'<rect x="2" y="{Y0 + 2}" width="996" height="{ZH - 4}" rx="36" fill="none" stroke="#d1d6db" stroke-width="4"/>')
    IH = 380; IW = round(IH * 1000 / ZH)
    inset_svg = (f'<svg width="{IW}" height="{IH}" viewBox="0 {Y0} 1000 {ZH}" style="flex:0 0 auto" role="img" aria-label="Yonsei–Sinchon: the 30 strongest net '
                 f'connections between 500 m cells over the terrain; most run downhill.">' + "".join(ins) + "</svg>")
    n_down = sum(a["c"] == "down" for a in Z["arrows"]); n_up = sum(a["c"] == "up" for a in Z["arrows"]); n_all = len(Z["arrows"])
    # ---- right top: the share of net flow on sloping ground (whole day)
    sh = {r["cls"]: r["share"] for r in D["vshare"] if r["daytype"] == "day"}
    seg = lambda c, colr_: f'<div style="flex:{sh[c]:.3f};background:{colr_};height:40px"></div>'
    key = lambda colr_, lab: (f'<span style="display:inline-flex;align-items:center;gap:9px"><span style="width:16px;height:16px;border-radius:4px;'
                              f'background:{colr_}"></span>{lab}</span>')
    leg = lambda c, s: f'<span style="display:inline-flex;align-items:center;gap:8px"><span style="width:26px;height:5px;border-radius:3px;background:{c}"></span>{s}</span>'
    return f"""<section id="vec" data-transition="fade">
<p class="eyebrow">FACTORS TOGETHER</p>
<h2>Net bicycle flow runs downhill</h2>
<div style="display:flex;gap:72px;margin-top:30px;align-items:flex-start">
<div style="flex:0 0 {CW}px">
<div style="display:flex;gap:26px;font-size:19px;color:var(--ink2);margin:0 0 8px">{leg(RED, "Downhill")}{leg(BLUE, "Uphill")}{leg("#d1d6db", "Across the slope / flat")}</div>
{city_svg}
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:40px;padding-top:24px">
<div class="v-s1" style="opacity:0">
<p style="margin:0;font-size:92px;line-height:1;font-weight:700;color:var(--red)">{sh["down"]:.0%}</p>
<p style="margin:10px 0 16px;font-size:24px;line-height:1.4;color:var(--ink2)">of the bikes' net movement on sloping ground goes downhill</p>
<div style="display:flex;border-radius:10px;overflow:hidden">{seg("down", RED)}{seg("side", "#E5E8EB")}{seg("up", BLUE)}</div>
<div style="display:flex;gap:28px;margin-top:12px;font-size:20px;color:var(--ink2)">{key(RED, f"Downhill {sh['down']:.0%}")}{key("#E5E8EB", f"Across the slope {sh['side']:.0%}")}{key(BLUE, f"Uphill {sh['up']:.0%}")}</div>
</div>
<div class="v-s2" style="opacity:0;display:flex;gap:30px;align-items:center">
{inset_svg}
<div><p style="margin:0;font-size:26px;font-weight:700;color:var(--ink)">Yonsei–Sinchon up close</p>
<p style="margin:12px 0 0;font-size:56px;line-height:1;font-weight:700;color:var(--red)">{n_down} of {n_all}</p>
<p style="margin:8px 0 0;font-size:21px;line-height:1.45;color:var(--ink2)">strongest local connections run downhill; {n_up} run uphill</p>
<p style="margin:14px 0 0;font-size:18px;line-height:1.45;color:var(--muted)">Darker ground is higher.</p></div>
</div>
</div>
</div>
{FOOT}
{note}
</section>"""


_VEC_JS = """  // ---------- flow field: drawn as static SVG in slides/final_deck_new.py; only the steps here ----------
  (function () {
    const sec = document.getElementById('vec'); if (!sec) return;
    const q = s => sec.querySelector(s);
    const grey = q('.v-grey'), col = q('.v-col'), s1 = q('.v-s1'), s2 = q('.v-s2');
    IX.vec = {
      steps: 3,
      cues: ['Each arrow is the net flow out of a 1 km cell, on an elevation map. Darker ground is higher.',
             'Colour by direction against the terrain. Where the ground slopes, 69% of the flow runs downhill and 7% uphill.',
             'Yonsei–Sinchon: the 30 strongest local net connections; many run downhill.'],
      set(k) { fade(grey, k < 1); fade(col, k >= 1); fade(s1, k >= 1); fade(s2, k >= 2, 600); },
    };
  })();

"""


# speaker notes of current slides that change with the order (data and measures now come before the factors)
NOTES = {
    "factors": "What is it about a station? We listed four candidates. Time of day, because commuting and leisure trips look different. "
               "Weather: rain and temperature. Terrain, because pedalling uphill is hard. And transit, since many people ride to and from the subway. "
               "The first two explain the days we chose; the last two are possible reasons why some stations run out. We look at them one at a time, then together.",
    "hours": "We first considered time of day and weather. On weekdays, usage peaks at 8 am and 6 pm, following the commuting hours. "
             "Weekends and holidays have a broad afternoon peak instead. Weather also affects how much people ride. "
             "We therefore focused on non-holiday weekdays with less than 1 mm of rainfall, especially the 7–9 am commute. "
             "The detailed temperature findings are available in the appendix. Within this scope, we next looked at station characteristics.",
}
WEATHER_LEAD = ("Next, weather, and for now only temperature.",
                "Next, weather. Rain cuts rides sharply, which is why we keep dry days; here we look at temperature.")

# short slide titles (noun phrases; the findings stay in the side numbers and the speaker notes)
TITLES = {
    "intro": "How Ddareungi works",
    "why": "A growing operating deficit",
    "scope": "378 dry weekdays, 2,843 stations",
    "d_measures": "Losing bikes vs running out",
    "hours": "Rides by hour",
    "weather": "Rides by daily high temperature",
    "elev": "Elevation and net outflow",
    "stmap": "Stations that lose bikes, on the map",
    "d_cop_subway": "Elevation × subway distance",
    "d_wx_elev": "Elevation × morning temperature",
    "traits": "Station features and running out",
    "hypo": "Does every hill need a truck?",
    "quad": "Four station groups",
    "tmap": "The four groups on the map",
    "when": "Refill timing on the hills",
    "gumap": "Morning net flow by district",
    "a_pass": "Weekday rides by pass type",
    "a_inc": "District income and station use",
}

# ================= appendix "a_buffer": bikes on hand at 8 am against the empty share, every station (backs up the d_buffer slide)
_pts = []
for r in csv.DictReader(open(R / "data/station_master.csv", encoding="utf-8-sig")):
    if r["parked_08_2025"] and r["am_empty_dry"] and r["elev_bare_m"]:
        _pts.append((float(r["parked_08_2025"]), float(r["am_empty_dry"]), band(float(r["elev_bare_m"]))))
W, H, L, RT, T, B = 1071, 600, 96, 24, 56, 78
XM = 40
x = lambda v: L + min(v, XM) / XM * (W - L - RT)
y = lambda v: H - B - v * (H - T - B)
o = []
for v in (0, .2, .4, .6, .8, 1):
    o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{LINE}"/>' + t(L - 12, y(v) + 6, f"{v:.0%}", 18, MUTED, "end"))
for v in range(0, XM + 1, 10):
    o.append(t(x(v), H - B + 30, v, 18, MUTED, "middle"))
o.append(t((L + W - RT) / 2, H - 14, f"Bikes at the station at 8 am, weekday mean (stations beyond {XM} drawn at the edge)", 19, INK2, "middle"))
o.append(t(L, T - 18, "Empty share, 7–9 am", 20, INK, "start", 700))
_col = {"flat": BLUE, "mid": "#F7A1A8", "hill": RED}
for bnd in ("flat", "mid", "hill"):
    for vx, vy, b in _pts:
        if b == bnd:
            o.append(f'<circle cx="{x(vx):.1f}" cy="{y(vy):.1f}" r="3.2" fill="{_col[b]}" fill-opacity=".45"/>')
_g = np.linspace(0.5, 30, 60)
_fit = np.clip(lowess([p[0] for p in _pts], [p[1] for p in _pts], _g, span=.3), 0, 1)
o.append(f'<polyline points="{" ".join(f"{x(g):.1f},{y(v):.1f}" for g, v in zip(_g, _fit))}" fill="none" stroke="{INK}" stroke-width="4"/>')
for i, (lab, bnd) in enumerate((("below 20 m", "flat"), ("20–40 m", "mid"), ("40 m and above", "hill"))):
    o.append(f'<circle cx="{W - RT - 220}" cy="{T + 22 + i * 30}" r="7" fill="{_col[bnd]}"/>' + t(W - RT - 204, T + 28 + i * 30, lab, 18, INK2))
o.append(t(W - RT - 228, T + 22 + 3 * 30 + 6, "line: LOESS, all stations", 16, MUTED))
c6 = svg(W, H, "Each dot is a station: bikes at 8 am against the empty share. Stations with few bikes run out often, and the hill-top stations are the ones with few bikes.", o)
_med = lambda bnd: float(np.median([p[0] for p in _pts if p[2] == bnd]))
_few = [p[1] for p in _pts if p[0] < 5]; _many = [p[1] for p in _pts if p[0] >= 10]
A_BUFFER = slide("a_buffer", "BIKES ON HAND", "Bikes on hand and running out", c6,
                 sidebox(stat(f"{np.mean(_few):.0%} vs {np.mean(_many):.0%}", "empty share at stations with fewer than 5 bikes at 8 am, against 10 or more", "red"),
                         stat(f"{_med('hill'):.0f} vs {_med('flat'):.0f}", "median bikes at 8 am: hill-top (40 m and above) against flat ground (below 20 m)", "ink"),
                         '<p class="note">Few bikes on hand means a station runs out; the hill-top stations are the ones with few bikes.</p>',
                         note=f"{len(_pts):,} stations. Bikes at 8 am: weekday mean, 2025. Empty share: 7, 8 and 9 am readings, 2025 dry weekdays."),
                 "Backup for the question why losing bikes is not the same as running out. Each dot is a station: how many bikes it has at 8 am "
                 f"on a weekday, against how often it is empty in the morning. Stations with fewer than 5 bikes are empty in {np.mean(_few):.0%} of the "
                 f"readings, those with 10 or more in {np.mean(_many):.0%}. The red hill-top stations sit on the left: a median of {_med('hill'):.0f} bikes "
                 f"against {_med('flat'):.0f} on flat ground.")

SLIDES = {"traits": TRAITS, "why": WHY, "scope": SCOPE, "d_measures": s1, "d_subway": s2, "d_cop_subway": s3, "d_wx_elev": s4,
          "d_buffer": s5, "a_buffer": A_BUFFER}
