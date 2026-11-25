"""Slides of the storyline written here: five drawn from the data, and the DATA slide (read by slides/build_final_deck.py, step 10).

  scope         DATA: the days, the stations and the sources (text only)
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
import csv, gzip, json, re
from collections import defaultdict
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[1]
N = json.load(open(R / "data/story_numbers.json", encoding="utf-8"))

RED, BLUE, GREY, MUTED, LINE, INK, INK2, TINT = "#F04452", "#3182F6", "#B0B8C1", "#6B7684", "#E5E8EB", "#191F28", "#333D4B", "#F4F8FF"
NAVY = "#1B3A6B"
FOOT = '<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>'


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
o.append(t(x(XM) - 8, y(0.14), f"loses bikes, still has bikes: {len(lose) - len(lose_out):,}", 20, BLUE, "end", 700, HALO))
o.append(t(x(-XM) + 8, T + 28, f"gains bikes: {gain:,}", 20, MUTED, "start", 700))
c1 = svg(W, H, f"Each dot is a station: morning net outflow against empty share. {len(lose):,} of {n_all:,} stations lose bikes each morning; "
         f"only {len(lose_out):,} of them are empty in at least one in five morning readings.", o)
s1 = slide("d_measures", "WHAT WE MEASURE", "Losing bikes is not the same as running out", c1,
           sidebox('<p class="note"><b>Net outflow</b>: rentals minus returns, in bikes. Above 0, the station loses bikes; below 0, it gains them.<br>'
                   '<b>Empty share</b>: how often the station has zero bikes at 7, 8 or 9 am.</p>',
                   stat(f"{len(lose) / n_all:.0%}", f"of stations lose bikes every morning: net outflow above 0 ({len(lose):,} of {n_all:,})", "blue"),
                   stat(f"{len(lose_out) / len(lose):.0%}", f"of those actually run out: empty in at least one in five readings from 7 to 9 am ({len(lose_out):,})", "red"),
                   note="Net outflow: 7 to 9 am, dry weekdays 2024 to 2025 (team table). Empty share: hourly stock, dry weekdays 2025."),
           f"We use two measures. The first is net outflow: rentals minus returns, counted in bikes. When it is positive, the station loses bikes; when "
           f"it is negative, it gains them. We compute it for the whole day and for the morning commute; a daily net outflow of plus 4 means the station "
           f"ends every day four bikes short. Net outflow tells us where bikes leave. But our question is where they run out, so the second measure is the "
           f"empty share: how often the station has no bike at all at 7, 8 or 9 am. Each dot is one station. Everything right of the line loses bikes in the morning: "
           f"{len(lose) / n_all:.0%} of all stations. But only the red ones, above the dashed line, are empty in at least one in five readings, and that is "
           f"just {len(lose_out) / len(lose):.0%} of the stations that lose bikes. Most blue stations lose bikes every morning and still never run out. "
           "We keep both measures from here on. First: where do the bikes leave each morning?")

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
c2 = svg(W, H, "Morning net outflow rises from minus 1.6 near the subway to plus 2.9 far from it, while the empty share only goes from 9.6 to 12.2 percent.", o)
s2 = slide("d_subway", "FACTOR 4. DISTANCE TO THE NEAREST SUBWAY STATION",
           "Far from the subway, stations lose the most bikes, yet they rarely run out", c2,
           sidebox(stat(f"{qnet[3]:+.1f}", f"bikes a morning at stations {cut[2]} m or more from the subway; {qnet[0]:+.1f} within {cut[0]} m".replace("-", "−"), "ink"),
                   stat(f"{qemp[0]:.1%} → {qemp[3]:.1%}", "empty share from the nearest to the farthest quarter: almost the same"),
                   '<p class="note">Subway distance tells us <b>where bikes leave</b>, not <b>where they run out</b>.</p>',
                   note=f"{sum(len(v) for v in byq.values()):,} stations in four equal quarters of distance. Net outflow: trips, 2024–2025 clear weekdays; empty share: hourly stock, 2025 dry weekdays."),
           f"Factor four is the distance to the nearest subway station. In the morning people ride to the subway, so stations within about {cut[0]} metres "
           f"gain bikes and those more than {cut[2]} metres away lose almost three a morning. But the empty share barely moves, from {qemp[0]:.0%} to "
           f"{qemp[3]:.0%}. The stations that lose the most bikes are not the ones that run out. Why? Keep that question for the next part.")

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


# ================= slide "scope" as DATA: the days, the stations and the sources (the measures are defined on d_measures)
SCOPE = f"""<section id="scope" data-transition="fade">
<p class="eyebrow">DATA</p>
<h2>378 dry weekdays, 2,843 stations, every trip</h2>
<div class="cols">
<div class="card">
<p class="card-title">Days</p>
<p class="card-body">Weekdays in 2024 and 2025 that are not public holidays and have under 1 mm of rain: 378 days.</p>
<p class="card-small">We dropped ten days on which rentals and returns did not match.</p>
</div>
<div class="card">
<p class="card-title">Data</p>
<p class="card-body">Every station-to-station trip in 2024–2025 (Seoul Open Data, 5-minute records), hourly bikes at every station (2025), hourly KMA weather, station elevation from 1:5,000 contour maps and subway stations.</p>
<p class="card-small">Stations: the 2,843 with records on at least 50 of those days.</p>
</div>
</div>
{FOOT}
<aside>To answer it, we use every trip between Seoul's bike stations in 2024 and 2025. We keep weekdays that are not public holidays and
have under 1 mm of rain: 378 days. Factors one and two will show why: weekends follow a different pattern from the commute, and rain changes how
many people ride. That leaves 2,843 stations with records on at least 50 of those days. For the stock at each station we also use the hourly
records of 2025. Next: what we measure on those days.</aside>
</section>"""

# ================= slide "intro": the four text cards become one strip (three steps with icons, two numbers); title without a colon
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


def _big(num, lab, color):
    return (f'<div style="flex:1"><p style="font-size:64px;font-weight:700;line-height:1;margin:0;color:{color}">{num}</p>'
            f'<p style="font-size:20px;line-height:1.4;margin:10px 0 0;color:var(--ink2)">{lab}</p></div>')


INTRO_STRIP = ('<div style="display:flex;align-items:center;gap:14px;background:var(--tint);border-radius:24px;padding:26px 36px;margin-top:24px">'
               + _step(_QR, "Scan the QR", "the app unlocks the bike") + _ARROW
               + _step(_BIKE, "Ride", "1,000 won an hour") + _ARROW
               + _step(_LOCK, "Lock at any station", "the return is logged")
               + '<div style="width:2px;align-self:stretch;background:var(--line);margin:0 22px"></div>'
               + '<div style="display:flex;gap:32px;flex:1">'
               + _big("44%", "of weekday rides at 7–9 am and 5–7 pm", BLUE)
               + _big("330", "stations the city watches at commute times, with 33 staff", RED)
               + '</div></div>\n')
INTRO_TITLE = "Rent a bike at one station, return it at any other"


def intro(sec):
    """The built intro slide with the strip in place of the four text cards and a title without a colon."""
    i = sec.index('<div style="display:grid;grid-template-columns:repeat(4,1fr)')
    j = sec.index('<p style="font-size:16px;color:var(--muted)', i)
    sec = sec[:i] + INTRO_STRIP + sec[j:]
    sec, k = re.subn(r"<h2>.*?</h2>", f"<h2>{INTRO_TITLE}</h2>", sec, count=1, flags=re.S)
    assert k == 1
    return sec


# speaker notes of current slides that change with the order (data and measures now come before the factors)
NOTES = {
    "factors": "What is it about a station? We listed four candidates. Time of day, because commuting and leisure trips look different. "
               "Weather: rain and temperature. Terrain, because pedalling uphill is hard. And transit, since many people ride to and from the subway. "
               "The first two explain the days we chose; the last two are possible reasons why some stations run out. We look at them one at a time, then together.",
    "hours": "First, time of day. This chart shows the average number of rides started in each hour. On weekdays there are two sharp peaks, at 8 in "
             "the morning and 6 in the evening: that is commuting. On weekends and holidays there is a single broad peak in the afternoon. This is why "
             "we study weekdays, and especially the morning commute, from 7 to 9 am.",
}
WEATHER_LEAD = ("Next, weather, and for now only temperature.",
                "Next, weather. Rain cuts rides sharply, which is why we keep dry days; here we look at temperature.")

SLIDES = {"scope": SCOPE, "d_measures": s1, "d_subway": s2, "d_cop_subway": s3, "d_wx_elev": s4, "d_buffer": s5}
