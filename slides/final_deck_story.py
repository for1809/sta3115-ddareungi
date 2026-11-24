"""Storyline of the final deck (agreed 2026-11-25): slide order, eyebrows, and text drafts for slides still to be drawn.

Read by slides/build_final_deck.py after the wording pass. The deck tells one story:
  "Many stations lose bikes every morning; only the hill-top stations cannot get them back."
  Act 1  the question            cover, intro, why, cost (Our Question)
  Act 2  one factor at a time    factors; 1 time of day; what we measure; 2 weather; 3 elevation; 4 subway distance
  Act 3  factors together        elevation x subway, elevation x weather, feature table, downhill flow, stock buffer
  Act 4  what to do              which stations need a truck (2x2), when the trucks come, conclusion, limits
Slides whose id starts with "d_" are drafts: the planned content as text, with the numbers we already have.
Numbers on the drafts: data/station_master.csv (empty share, stock, groups; 2025 dry weekdays) and
data/od_2024_2025/od/s0_station_daily.csv.gz (07-09 h net outflow, rentals minus returns, 2024-2025 dry weekdays).
"""

ORDER = ["cover", "intro", "why", "cost", "factors",
         "hours", "scope", "d_measures", "gumap", "weather", "elev", "stmap", "d_subway",
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
