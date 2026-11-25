"""Storyline of the final deck (agreed 2026-11-25): slide order, eyebrows, and text drafts for slides still to be drawn.

Read by slides/build_final_deck.py after the wording pass. The deck tells one story:
  "Many stations lose bikes every morning; only the hill-top stations cannot get them back."
  Act 1  the question            cover, intro, why, cost (Our Question)
  Act 2  one factor at a time    factors; 1 time of day; 2 weather; what we measure; 3 elevation; 4 subway distance
  Act 3  factors together        elevation x subway, elevation x weather, feature table, downhill flow, stock buffer
  Act 4  what to do              which stations need a truck (2x2), when the trucks come, conclusion, limits
Slides whose id starts with "d_" are drawn by slides/final_deck_new.py; DRAFTS below keeps their first text versions.
Numbers on the drafts: data/station_master.csv (empty share, stock, groups; 2025 dry weekdays) and
data/od_2024_2025/od/s0_station_daily.csv.gz (07-09 h net outflow, rentals minus returns, 2024-2025 dry weekdays).
"""

ORDER = ["cover", "intro", "why", "cost", "factors",
         "hours", "weather", "scope", "d_measures", "gumap", "elev", "stmap", "d_subway",
         "d_cop_subway", "d_wx_elev", "traits", "vec", "d_buffer",
         "hypo", "quad", "tmap", "g12", "when", "conclusion", "limits", "thanks",
         "appendix", "a_pass", "a_inc"]

EYEBROWS = {"scope": "WHAT WE MEASURE", "gumap": "WHAT WE MEASURE",
            "elev": "FACTOR 3. ELEVATION", "stmap": "FACTOR 3. ELEVATION",
            "traits": "FACTORS TOGETHER", "vec": "FACTORS TOGETHER",
            "quad": "WHICH STATIONS NEED A TRUCK", "tmap": "WHICH STATIONS NEED A TRUCK", "g12": "WHICH STATIONS NEED A TRUCK",
            "when": "WHEN THE TRUCKS COME"}

QUESTION = ('<p style="margin:0;font-size:72px;line-height:1.25;font-weight:700;letter-spacing:-1.5px;text-align:center;color:var(--ink)">'
            'Many stations lose bikes every morning.<br>Why do only <span style="color:var(--blue)">some</span> run out?</p>')
QUESTION_NOTE = ("Where does the money go? According to Bike Magazine, 53% of the operating cost is staff time spent redistributing bikes: "
                 "the trucks you see on the street. Every weekday morning, many stations lose bikes. But only some of them actually run out. "
                 "So our question is: why do only some stations run out? If we know that, the trucks can go to the right place at the right time.")

FOOT = '<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>'
PILL = ('<span style="display:inline-block;font-size:20px;font-weight:700;letter-spacing:.5px;color:var(--muted);'
        'border:2px dashed var(--line);border-radius:999px;padding:4px 14px;margin-left:16px;vertical-align:middle">DRAFT</span>')
BOX = "flex:1;border:3px dashed var(--line);border-radius:28px;padding:36px 40px;display:flex;flex-direction:column;gap:18px"
R = ' style="text-align:right"'


def _table(head, rows, hl=()):
    h = "<tr>" + "".join(f"<th{'' if i == 0 else R}>{c}</th>" for i, c in enumerate(head)) + "</tr>"
    hlc = ' class="hl"'
    b = "".join(f"<tr{hlc if j in hl else ''}>" + "".join(f"<td{'' if i == 0 else R}>{c}</td>" for i, c in enumerate(r)) + "</tr>"
                for j, r in enumerate(rows))
    return f'<table class="tbl small">{h}{b}</table>'


def draft(sid, eyebrow, title, chart, table, points, note):
    pts = "".join(f'<p class="text" style="font-size:24px">{p}</p>' for p in points)
    return f"""<section id="{sid}" data-transition="fade">
<p class="eyebrow">{eyebrow}{PILL}</p>
<h2>{title}</h2>
<div style="display:flex;gap:32px;margin-top:36px;align-items:stretch">
<div style="{BOX}"><p class="card-small" style="font-weight:700;color:var(--blue)">PLANNED CHART</p><p class="text" style="font-size:26px">{chart}</p>{table}</div>
<div style="flex:0 0 560px;display:flex;flex-direction:column;gap:18px;padding-top:8px">{pts}</div>
</div>
{FOOT}
<aside>{note}</aside>
</section>
"""


DRAFTS = {
    "d_measures": draft(
        "d_measures", "WHAT WE MEASURE", "Two measures: where bikes leave, and where they run out",
        "Two panels, one station each: hourly stock from 6 am to midnight. A flat station drops from 16 bikes to 12 and never "
        "reaches zero; a hill-top station drops from 5 to 0 and stays there.",
        _table(["Measure", "Source", "Period"],
               [["Net outflow, 7–9 am<br><span class='card-small'>rentals minus returns; &gt; 0 means the station loses bikes</span>", "trip records", "2024–2025 dry weekdays"],
                ["Empty share, 7–9 am<br><span class='card-small'>share of hourly stock readings with 0 bikes</span>", "hourly stock", "2025 dry weekdays"]]),
        ["<b>Net outflow</b> tells us where bikes leave.", "<b>Empty share</b> tells us where riders find no bike.",
         "They are not the same thing: a station that starts the morning with many bikes can lose some and still never run out."],
        "We use two measures. Net outflow is rentals minus returns between 7 and 9 in the morning: if it is positive, the station loses bikes. "
        "Empty share is how often the station has zero bikes in those hours. These are different. A station that starts the day with plenty "
        "of bikes can lose a few and never run out. Keep that in mind, because it is the key to the rest of the talk."),

    "d_subway": draft(
        "d_subway", "FACTOR 4. DISTANCE TO THE NEAREST SUBWAY STATION",
        "Far from the subway, stations lose the most bikes in the morning, yet they rarely run out",
        "Two bar panels over the four quarters of subway distance: morning net outflow (diverging, blue gains and red losses) "
        "and empty share. The first rises steeply; the second barely moves.",
        _table(["Distance to subway", "Stations", "Net outflow (bikes/day)", "Empty share"],
               [["under 209 m", "677", "−1.6", "9.6%"], ["209–418 m", "679", "−0.8", "9.9%"],
                ["418–661 m", "677", "+0.1", "10.9%"], ["661 m and over", "680", "+2.9", "12.2%"]], hl=(3,)),
        ["People ride <b>to</b> the subway in the morning: stations near it gain bikes, those far from it lose them.",
         "Over the whole day this evens out (ρ = 0.08 with daily net outflow): the evening ride home brings the bikes back.",
         "So subway distance explains <b>where bikes leave</b>, but hardly <b>where they run out</b>."],
        "Our fourth factor is the distance to the nearest subway station. In the morning it matters a lot for the flow: stations within about "
        "200 metres of a subway station gain one or two bikes, while those more than 660 metres away lose almost three. People ride to the "
        "subway. But look at the empty share: it only goes from about 10 to 12 percent. Stations far from the subway lose the most bikes, "
        "and yet they rarely run out. Why? That is the question for the next part."),

    "d_cop_subway": draft(
        "d_cop_subway", "FACTORS TOGETHER", "Near the subway or far from it, the hill-top stations run out",
        "Coplot: empty share against elevation, one panel for each quarter of subway distance, LOESS curve in each. "
        "(Or a mosaic: elevation band × subway quarter, tile area = stations, colour = empty share.)",
        _table(["Distance to subway", "Below 20 m", "20–40 m", "40 m and over"],
               [["under 209 m", "4.8%", "10.3%", "30.8%"], ["209–418 m", "4.9%", "12.1%", "24.3%"],
                ["418–661 m", "5.5%", "13.7%", "29.9%"], ["661 m and over", "5.0%", "11.9%", "28.3%"]]),
        ["In every quarter of subway distance, the same step: about 5% on flat ground, 25–31% on the hills.",
         "Subway distance moves the flow, not the shortage.", "Hill-top stations: 67, 67, 66 and 118 in the four quarters."],
        "Now we put two factors together. Each panel is one quarter of subway distance, from the closest to the farthest. In every panel the "
        "picture is the same: about 5 percent empty on flat ground, and 25 to 30 percent on the hills. So whether a station is near the subway "
        "or far from it, what decides if it runs out is the hill."),

    "d_wx_elev": draft(
        "d_wx_elev", "FACTORS TOGETHER", "At every temperature, the hills lose bikes and the flat ground gains them",
        "Lines of morning net outflow by morning temperature band, one line per elevation band (hill, middle, flat). "
        "The lines move up and down a little with temperature but never cross zero.",
        _table(["Morning temperature", "&lt; 0", "0–5", "5–10", "10–15", "15–20", "20–25", "25+"],
               [["40 m and over", "+1.1", "+1.4", "+1.8", "+2.0", "+2.0", "+1.8", "+1.9"],
                ["20–40 m", "+0.3", "+0.4", "+0.6", "+0.7", "+0.7", "+0.6", "+0.7"],
                ["Below 20 m", "−0.3", "−0.5", "−0.6", "−0.7", "−0.8", "−0.8", "−0.8"]], hl=(0,)),
        ["Weather changes <b>how many</b> bikes move, not <b>which way</b>.",
         "Even on the coldest mornings, the hills still lose bikes.",
         "Draft numbers (bikes per station per morning); to be recomputed for the final chart."],
        "Earlier we saw that weather changes how many people ride. Does it change where the bikes go? No. At every temperature, from below "
        "zero to over 25 degrees, the hill-top stations lose bikes and the flat stations gain them. A warm morning moves more bikes, a cold one "
        "fewer, but always in the same direction."),

    "d_buffer": draft(
        "d_buffer", "FACTORS TOGETHER", "Flat stations lose bikes but keep a buffer; hill-top stations have none",
        "Dot or bar chart for four kinds of station (flat or hill, near or far from the subway): bikes lost between 7 and 9 am, "
        "bikes parked at 8 am, and empty share side by side.",
        _table(["Station", "Lost 7→9 am", "Parked at 8 am", "Empty share"],
               [["Flat, far from subway", "3.8", "16", "5%"], ["Flat, near subway", "−1.4 (gains)", "16", "5%"],
                ["Hill, far from subway", "0.5", "5", "28%"], ["Hill, near subway", "0.6", "4", "31%"]], hl=(2, 3)),
        ["Flat stations lose the most bikes, but bikes ride down to them all day, so they keep about 16.",
         "Hill-top stations keep only 4 or 5: losing even one or two empties them.",
         "That is why the hills run out, and why the trucks already go up there (next part)."],
        "So why do the stations far from the subway lose the most bikes and still not run out? Because they keep a buffer. Bikes ride down "
        "to the flat ground all day, so at 8 am a flat station still has about 16 bikes. A hill-top station has only 4 or 5, because the bikes "
        "that went down never come back up. Losing one or two is enough to empty it. Many stations lose bikes in the morning; only the hills "
        "cannot get them back."),
}


# ---- STEP "WHEN", redrawn from the hourly stock (analysis/hourly_refill.py -> data/hourly_refill_2025.csv):
#      when are the hill-top stations empty, and when do bikes other than riders' arrive there, hour by hour
def when_slide(csv_path):
    import csv
    rows = {(r["band"], int(r["hour"])): r for r in csv.DictReader(open(csv_path, encoding="utf-8"))}
    hill, flat = "hill40+", "flat<20"
    g = lambda b, h, k: float(rows[(b, h)][k])
    W, H, L, RT = 1071, 557, 78, 16
    bw = (W - L - RT) / 24
    x = lambda h: L + h * bw
    t1, b1 = 46, 236                          # empty share panel, 0 to 35 %
    t2, b2 = 300, 512                         # refill panel, -0.4 to +0.8 bikes an hour
    y1 = lambda v: b1 - v / 0.35 * (b1 - t1)
    y2 = lambda v: t2 + (0.8 - v) / 1.2 * (b2 - t2)
    RED, BLUE, GREY, MUTED, LINE = "#F04452", "#3182F6", "#B0B8C1", "#6B7684", "#E5E8EB"
    o = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Hill-top stations by hour on 2025 dry weekdays: '
         f'share of stock readings with zero bikes, and bikes added by moves other than rides. No refill between 1 and 6 am; refills start at 8 am." '
         f'style="font-family:inherit">']
    o.append(f'<rect x="{x(7):.1f}" y="{t1 - 30}" width="{2 * bw:.1f}" height="{b2 - t1 + 30}" fill="#F4F8FF"/>')
    o.append(f'<text x="{x(8):.1f}" y="{t1 - 12}" text-anchor="middle" font-size="18" font-weight="700" fill="{MUTED}">Morning rush</text>')
    for v in (0, 0.1, 0.2, 0.3):
        o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y1(v):.1f}" y2="{y1(v):.1f}" stroke="{LINE}"/>'
                 f'<text x="{L - 10}" y="{y1(v) + 6:.1f}" text-anchor="end" font-size="18" fill="{MUTED}">{int(v * 100)}%</text>')
    for v in (-0.4, 0, 0.4, 0.8):
        o.append(f'<line x1="{L}" x2="{W - RT}" y1="{y2(v):.1f}" y2="{y2(v):.1f}" stroke="{"#8B95A1" if v == 0 else LINE}"/>'
                 f'<text x="{L - 10}" y="{y2(v) + 6:.1f}" text-anchor="end" font-size="18" fill="{MUTED}">{"0" if v == 0 else f"{v:+.1f}"}</text>')
    o.append(f'<text x="{L}" y="{t1 - 12}" font-size="20" font-weight="700" fill="#191F28">Stations with zero bikes</text>')
    o.append(f'<text x="{L}" y="{t2 - 16}" font-size="20" font-weight="700" fill="#191F28">Bikes added by trucks and other moves, per station per hour</text>')
    for b, c, w in ((flat, GREY, 3), (hill, RED, 5)):
        pts = " ".join(f"{x(h):.1f},{y1(g(b, h, 'empty_share')):.1f}" for h in range(24))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linejoin="round"/>')
    o.append(f'<text x="{x(23) - 4:.1f}" y="{y1(g(hill, 23, "empty_share")) - 12:.1f}" text-anchor="end" font-size="18" font-weight="700" fill="{RED}">40 m and above</text>')
    o.append(f'<text x="{x(23) - 4:.1f}" y="{y1(g(flat, 23, "empty_share")) - 10:.1f}" text-anchor="end" font-size="18" fill="{MUTED}">below 20 m</text>')
    for h in range(23):
        for b, c, dx in ((hill, BLUE, 0.12), (flat, GREY, 0.52)):
            v = g(b, h, "other_in")
            y0, yv = y2(0), y2(v)
            o.append(f'<rect x="{x(h) + dx * bw:.1f}" y="{min(y0, yv):.1f}" width="{0.36 * bw:.1f}" height="{max(abs(yv - y0), 0.6):.1f}" fill="{c}" rx="2"/>')
    o.append(f'<rect x="{W - RT - 330}" y="{t2 - 2}" width="16" height="16" fill="{BLUE}" rx="2"/><text x="{W - RT - 308}" y="{t2 + 12}" font-size="18" fill="#191F28">40 m and above</text>'
             f'<rect x="{W - RT - 140}" y="{t2 - 2}" width="16" height="16" fill="{GREY}" rx="2"/><text x="{W - RT - 118}" y="{t2 + 12}" font-size="18" fill="{MUTED}">below 20 m</text>')
    o.append(f'<text x="{(x(1) + x(7)) / 2:.1f}" y="{y2(0) - 14:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="{BLUE}">no refill overnight</text>')
    for h in range(0, 25, 3):
        o.append(f'<text x="{x(h):.1f}" y="{b2 + 32}" text-anchor="middle" font-size="18" fill="{MUTED}">{h % 24} h</text>')
    o.append("</svg>")
    night = sum(g(hill, h, "other_in") for h in range(1, 7))
    morning = sum(g(hill, h, "other_in") for h in (8, 9, 10))
    day = sum(g(hill, h, "other_in") for h in range(23))
    e6, e9 = g(hill, 6, "empty_share"), g(hill, 9, "empty_share")
    side = f"""<div class="side" style="gap:18px">
<div class="stat"><p class="stat-num ink">{abs(night):.1f}</p><p class="stat-lab">bikes added to a hill-top station between 1 and 6 am: nobody refills the hills overnight</p></div>
<div class="stat"><p class="stat-num blue">+{morning:.1f}</p><p class="stat-lab">of the {day:.1f} added each day arrive from 8 to 11 am, after the rush has started</p></div>
<div class="stat"><p class="stat-num">{e6:.0%}</p><p class="stat-lab">of hill-top stations already empty at 6 am, {e9:.0%} by 9 am</p></div>
<p class="note muted" style="font-size:20px">2025 dry weekdays, stations at 40 m and above (bare-earth elevation); hourly stock matched with trips. A reading is taken as the stock at the start of the hour.</p>
</div>"""
    note = (f"Do the trucks already fill the hills before the morning? We checked the stock at every station hour by hour. The red line is the share "
            f"of hill-top stations with no bikes; the blue bars are bikes that arrive by something other than a ride, mostly trucks. Between 1 and 6 "
            f"in the morning, almost nothing arrives: {abs(night):.1f} bikes. So already at 6 am, {e6:.0%} of the hill-top stations are empty, "
            f"and by 9 it is {e9:.0%}. The trucks do come, about {day:.1f} bikes a day, but the first big refill is from 8 to 11, once the rush "
            f"has already started, and the next one is in the afternoon. The hills are refilled every day, just not in time.")
    return f"""<section id="when" data-transition="fade">
<p class="eyebrow">WHEN THE TRUCKS COME</p>
<h2>Nobody refills the hills overnight: the trucks arrive after 8 am</h2>
<div class="body">
<div class="figcard">{''.join(o)}</div>
{side}
</div>
{FOOT}
<aside>{note}</aside>
</section>
"""
