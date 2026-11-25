"""Chart changes for the final deck (read by slides/build_final_deck.py), on top of the teammate's chart script.

STMAP  slide "stmap": the hills first (ground 50 m or higher shaded), then the stations that lose bikes, then those that
       gain them, with a side bar chart of the share of stations that end the day short by elevation (D.bins)
QUAD   slide "quad": the 2x2 as four tiles, each with its count and its typical day (D.prof), instead of a scatter
GUMAP_REVEAL  slide "gumap": the losing and gaining districts appear together on the morning step
STMAP_SIDE    the new side column of "stmap"
cover_map()   the cover: Seoul's contours as a topographic map, instead of the drawn hill and arrows
"""

import math
import re
import json


def classification_wording(html):
    """Describe user-flow signs without inferring empty stock or truck needs."""
    data = json.loads(re.search(r'<script[^>]*id="ixdata"[^>]*>(.*?)</script>', html, re.S)[1])
    count = {r['ty']: r['N'] for r in data['tcount']}
    morning = count['G1'] + count['G2']
    section = re.search(r'<section\b[^>]*id="quad".*?</section>', html, re.S)
    revised = section[0]
    pairs = [
        ('WHICH STATIONS NEED A TRUCK', 'MORNING AND FULL-DAY NET FLOW'),
        ('emptied 7–9 am? still short at night? (net outflow above zero or not, in bikes)',
         'Morning net outflow > 0? Full-day net outflow > 0?'),
        ('G1 stays short and needs a truck; G2 refills by night and does not',
         'G1: morning loss remains over the full day. G2: later net returns offset it.'),
        ('stations are emptied in the morning. Why do fewer than half of them recover?',
         'stations have positive mean morning net outflow. Do later net returns offset it?'),
    ]
    for old, new in pairs:
        assert revised.count(old) == 1, old
        revised = revised.replace(old, new)
    note = (f'We classify stations using two signs: average net outflow during 7–9 am, and average net outflow over the full day. '
            f'Positive means rentals exceed returns. G1 and G2 both lose bikes in the morning. '
            f'For G1, full-day net outflow remains positive; for G2, later net returns offset the morning loss, so the full-day total is zero or negative. '
            f'G3 has no net loss in either window; G4 has no morning net loss but has positive full-day net outflow. '
            f'We focus on G1 and G2: {count["G1"]:,} and {count["G2"]:,} stations. '
            'These groups describe average user flow, not whether a station is empty or needs a truck.')
    revised = re.sub(r'<aside>.*?</aside>', lambda _: f'<aside>{note}</aside>', revised, count=1, flags=re.S)
    html = html[:section.start()] + revised + html[section.end():]
    start = html.index('  // ---------- the 2x2 as four tiles')
    end = html.index('  // ----------', start + 10)
    chart = html[start:end]
    pairs = [
        ('Not emptied in the morning', 'No morning net loss (≤0)'),
        ('Emptied in the morning (7–9 am)', 'Morning net loss (>0)'),
        ("[['Still short', 'at night', 0], ['Back to normal', 'by night', 1]]",
         "[['Net loss', 'over full day', 0], ['No net loss', 'over full day', 1]]"),
        ('fills in the morning, empties during the day', 'no morning net loss; full-day net loss'),
        ('drained in the morning, never refilled', 'morning net loss; full-day net loss'),
        ('gains bikes over the whole day', 'no morning net loss; no full-day net loss'),
        ('drained in the morning, back by evening', 'morning net loss; no full-day net loss'),
        ('txt(TYL[t],', 'txt(t,'),
        ('a typical day: ↑ bikes leave, ↓ bikes arrive', 'hourly mean net outflow: + loss, − gain'),
        ('stations are emptied every morning:', 'have morning net loss:'),
        ('recover by night,', 'offset the loss by day end;'),
        ('Two questions for every station: is it emptied during the 7–9 am commute (columns), and is it still short at the end of the day (rows)?',
         'Is average morning net outflow positive (columns)? Is average full-day net outflow positive (rows)?'),
        ('Each tile shows a typical day for its group: up means bikes leave, down means bikes arrive. The blue band is 7–9 am.',
         'Each tile shows mean hourly net outflow: positive means net loss and negative means net gain. The blue band marks the morning window.'),
        (f'The right column is the {morning:,} stations emptied every morning. {count["G2"]:,} recover by night; {count["G1"]:,} never do. Why?',
         f'The right column has {morning:,} stations with morning net loss. For {count["G2"]:,}, later net returns offset it; for {count["G1"]:,}, they do not.'),
    ]
    for old, new in pairs:
        assert chart.count(old) == 1, old
        chart = chart.replace(old, new)
    return html[:start] + chart + html[end:]


def recovery_wording(html):
    """Keep the recovery charts while distinguishing association from cause."""
    data = json.loads(re.search(r'<script[^>]*id="ixdata"[^>]*>(.*?)</script>', html, re.S)[1])
    groups = {r['ty']: r for r in data['g12']}
    g1, g2 = groups['G1'], groups['G2']
    section = re.search(r'<section\b[^>]*id="g12".*?</section>', html, re.S)
    revised = section[0].replace('WHICH STATIONS NEED A TRUCK', 'EVENING RECOVERY')
    revised = re.sub(r'<h2>.*?</h2>', '<h2>Different evening recovery</h2>', revised, count=1, flags=re.S)
    for group in [g2, g1]:
        old = f'−{-group["pm"]:.1f} bikes'
        assert revised.count(old) == 1, old
        revised = revised.replace(old, f'+{-group["pm"]:.1f} bikes')
    revised = revised.replace('net return to a G2 station in the evening commute, 5–8 pm',
                              'mean net gain at a G2 station, 5–8 pm')
    revised = revised.replace('net return to a G1 station: few people ride back up',
                              'mean net gain at a G1 station, 5–8 pm')
    note = (f'Both groups lose bikes in the morning, but G2 receives more net returns in the evening. '
            f'From 5 to 8 pm, G2 gains an average of {-g2["pm"]:.1f} bikes per station, compared with {-g1["pm"]:.1f} for G1. '
            f'G1 stations also have higher median elevation: {g1["elev"]:.0f} metres versus {g2["elev"]:.0f} for G2. '
            f'Their median subway distances are similar, about {round(g1["sub"], -1):.0f} and {round(g2["sub"], -1):.0f} metres. '
            'This links weaker evening recovery with higher elevation, but does not establish that elevation causes the difference. '
            'The chart describes user net flow; recovery does not mean the station is full or never empty.')
    revised = re.sub(r'<aside>.*?</aside>', lambda _: f'<aside>{note}</aside>', revised, count=1, flags=re.S)
    html = html[:section.start()] + revised + html[section.end():]
    start = html.index('  // ---------- G1 vs G2:')
    end = html.index('  // ----------', start + 10)
    chart = html[start:end]
    cues = [f'G2 loses bikes in the morning and gains {-g2["pm"]:.1f} bikes per station during 5–8 pm.',
            f'G1 also loses bikes in the morning, but gains only {-g1["pm"]:.1f} bikes per station during 5–8 pm.',
            f'Median elevation is {g1["elev"]:.0f} m for G1 and {g2["elev"]:.0f} m for G2; subway distances are similar. This is an association.']
    chart, count = re.subn(r'cues: \[.*?\],', lambda _: 'cues: ' + json.dumps(cues) + ',', chart, count=1, flags=re.S)
    assert count == 1
    return html[:start] + chart + html[end:]


def map_only(html):
    """Simplify the station map after the existing wording and units passes."""
    section = re.search(r'<section\b[^>]*id="stmap".*?</section>', html, re.S)
    assert section, "station map section not found"
    old = section.group(0)
    start = old.index('<div class="body">')
    end = old.index('<div class="foot">', start)
    content = ('<div style="display:flex;justify-content:center;margin-top:20px">'
               '<div id="ix-stmap" style="position:relative;width:1664px;height:730px" '
               'role="img" aria-label="Seoul terrain and stations with net daily bicycle losses or gains"></div>'
               '</div>\n')
    new = old[:start] + content + old[end:]
    new = re.sub(r'<aside>.*?</aside>\s*', '', new, flags=re.S)
    html = html[:section.start()] + new + html[section.end():]

    start = html.index('  // ---------- station map: the hills first')
    end = html.index('  // ----------', start + 10)
    chart = html[start:end]
    assert 'const W = 760' in chart
    chart = chart.replace('const W = 760', 'const W = 820')
    chart = chart.replace("    guLayer(svg,", "    svg.style.display = 'block'; svg.style.margin = '0 auto';\n    guLayer(svg,", 1)
    chart = chart.replace('left:0;top:${Hh + 2}px', 'left:50%;transform:translateX(-50%);top:${Hh + 8}px')
    chart = chart.replace("    guLabels(svg, 14);\n", '')
    chart = re.sub(r'    const nL = .*?;\n', '', chart)
    chart = chart.replace("loses over 1 bike a day (${nL.toLocaleString('en')})", "loses over 1 bike a day")
    chart = chart.replace("gains over 1 (${nG.toLocaleString('en')})", "gains over 1 bike a day")
    bars_start = chart.index("    const bars = document.getElementById('st-bars');")
    bars_end = chart.index('    IX.stmap =', bars_start)
    chart = chart[:bars_start] + chart[bars_end:]
    chart = chart.replace(' On the right: the higher the station, the more of them end the day short.', '')
    chart = chart.replace('        const show = [k >= 1, k >= 1, k >= 2, true];\n'
                          '        side.forEach((n, j) => fade(n, show[j]));\n', '')
    assert 'st-bars' not in chart and 'side.' not in chart
    return html[:start] + chart + html[end:]


STMAP_SIDE = """
<div class="stat"><p class="stat-lab" style="margin:0 0 8px">Share of stations that end the day short of bikes, by station elevation</p><div id="st-bars"></div></div>
<p class="note"><b style="color:var(--red)">Red on the hills</b><br>The northern foothills (Eunpyeong, Gangbuk, Dobong), Gwanak, and the hills of Seodaemun, Seongbuk and Jongno.</p>
<p class="note"><b style="color:var(--blue)">Blue in the valleys</b><br>Along the Han River and its streams, Yeouido, Seongsu and Gangnam’s main roads.</p>
<p class="note muted" style="font-size:20px">Shaded: ground 50 m or higher. Terrain and contours: Seoul 1:5,000 digital topographic map.</p>
"""

STMAP = r"""  // ---------- station map: the hills first, then the stations that lose and gain bikes ----------
  (function () {
    const box = document.getElementById('ix-stmap'); if (!box) return;
    const W = 760, Hh = Math.round(W * F.h / 1000);
    const svg = makeSvg(box, W, Hh, `0 0 1000 ${F.h}`);
    guLayer(svg, '#f7f9fc', '#d1d6db');
    const hill = el('g', {}, svg);
    D.terrain.forEach(t => { if (t.e >= 50) el('rect', { x: t.x, y: t.y, width: F.cell + .4, height: F.cell + .4, fill: t.e >= 100 ? '#d9c6a3' : '#ebe0c9' }, hill); });
    D.contours.filter(c => c.level === 50).forEach(c => el('path', { d: c.d, fill: 'none', stroke: '#a08360', 'stroke-width': 1, 'vector-effect': 'non-scaling-stroke' }, hill));
    D.gu.forEach(u => el('path', { d: u.d, fill: 'none', stroke: '#ffffff', 'stroke-width': 1.3, 'vector-effect': 'non-scaling-stroke' }, svg));
    const P = D.stations;
    const layer = (keep, col, r) => {
      const g = el('g', {}, svg);
      P.filter(keep).sort((a, b) => Math.abs(a.d) - Math.abs(b.d)).forEach(p =>
        el('circle', { cx: p.x, cy: p.y, r, fill: col, stroke: '#fff', 'stroke-width': .6, 'vector-effect': 'non-scaling-stroke' }, g));
      g.style.opacity = 0; return g;
    };
    const gMid = layer(p => Math.abs(p.d) <= 10, '#c4cad1', 2.4);
    const gLose = layer(p => p.d > 10, C.red, 3.8);
    const gGain = layer(p => p.d < -10, C.blue, 3.8);
    guLabels(svg, 14);
    const nL = P.filter(p => p.d > 10).length, nG = P.filter(p => p.d < -10).length;
    const sw = (c, round) => `<span style="display:inline-block;width:16px;height:16px;border-radius:${round ? '50%' : '4px'};background:${c};vertical-align:-2px;margin-right:6px"></span>`;
    const lg = document.createElement('div');
    lg.style.cssText = `position:absolute;left:0;top:${Hh + 2}px;font:18px ${FONT};color:${C.ink2};display:flex;gap:20px;align-items:center;white-space:nowrap`;
    lg.innerHTML = `<span>${sw('#ebe0c9')}ground 50 m or higher</span>` +
      `<span class="lgL">${sw(C.red, 1)}loses over 10% of docks a day (${nL.toLocaleString('en')})</span>` +
      `<span class="lgG">${sw(C.blue, 1)}gains over 10% (${nG.toLocaleString('en')})</span>`;
    box.appendChild(lg);
    const lgL = lg.querySelector('.lgL'), lgG = lg.querySelector('.lgG');
    const bars = document.getElementById('st-bars');
    if (bars) {
      const LAB = { '[0,15)': 'Below 15 m', '[15,25)': '15–25 m', '[25,35)': '25–35 m', '[35,50)': '35–50 m', '[50,1e+03)': '50 m and above' };
      bars.innerHTML = D.bins.map(b => {
        const hot = b.out >= .5, col = hot ? C.red : '#9aa4af';
        return `<div style="display:flex;align-items:center;gap:12px;margin:7px 0;font:22px ${FONT}">` +
          `<span style="width:160px;color:${C.ink2}">${LAB[b.b] || b.b}</span>` +
          `<span style="flex:1;height:22px;background:#f2f4f6;border-radius:11px;overflow:hidden"><span style="display:block;height:100%;width:${Math.round(100 * b.out)}%;background:${col};border-radius:11px"></span></span>` +
          `<span style="width:64px;text-align:right;font-weight:700;color:${hot ? C.red : C.ink2}">${Math.round(100 * b.out)}%</span></div>`;
      }).join('');
    }
    const side = sideItems('stmap');
    IX.stmap = {
      steps: 3,
      cues: ['First the terrain: the shaded areas are ground 50 m or higher.',
             'Now the stations that lose more than 10% of their docks a day, in red. They sit on the shaded hills. On the right: the higher the station, the more of them end the day short.',
             'And the stations that gain bikes, in blue: along the Han River, its streams and the flat business areas.'],
      set(k) {
        fade(gMid, k >= 1); fade(gLose, k >= 1, 600); fade(gGain, k >= 2, 600); fade(lgL, k >= 1); fade(lgG, k >= 2);
        const show = [k >= 1, k >= 1, k >= 2, true];
        side.forEach((n, j) => fade(n, show[j]));
      },
    };
    stop(box);
  })();

"""

QUAD = r"""  // ---------- the 2x2 as four tiles, each with its typical day ----------
  (function () {
    const box = document.getElementById('ix-quad'); if (!box) return;
    const W = 1071, H = 600, L = 150, T = 64, GAP = 18, TW = (W - L - GAP) / 2, TH = (H - T - 44 - GAP) / 2;
    const svg = makeSvg(box, W, H);
    const cnt = {}; D.tcount.forEach(t => { cnt[t.ty] = t.N; });
    const tot = D.stations.length;
    const PR = {}; D.prof.forEach(r => { (PR[r.ty] = PR[r.ty] || [])[r.h] = r.net; });
    const hdr = el('g', {}, svg);
    [['Not emptied in the morning', 0], ['Emptied in the morning (7–9 am)', 1]].forEach(([s, c]) =>
      txt(s, { x: L + c * (TW + GAP) + TW / 2, y: T - 20, 'text-anchor': 'middle', 'font-size': 21, 'font-weight': 700, fill: C.ink }, hdr));
    [['Still short', 'at night', 0], ['Back to normal', 'by night', 1]].forEach(([a, b, r]) => {
      const cy = T + r * (TH + GAP) + TH / 2;
      txt(a, { x: L - 16, y: cy - 4, 'text-anchor': 'end', 'font-size': 20, 'font-weight': 700, fill: C.ink }, hdr);
      txt(b, { x: L - 16, y: cy + 22, 'text-anchor': 'end', 'font-size': 20, 'font-weight': 700, fill: C.ink }, hdr);
    });
    const CELL = { G4: [0, 0, 'fills in the morning, empties during the day'], G1: [1, 0, 'drained in the morning, never refilled'],
                   G3: [0, 1, 'gains bikes over the whole day'], G2: [1, 1, 'drained in the morning, back by evening'] };
    const tiles = {};
    Object.entries(CELL).forEach(([t, [c, r, desc]]) => {
      const x0 = L + c * (TW + GAP), y0 = T + r * (TH + GAP);
      el('rect', { x: x0, y: y0, width: TW, height: TH, rx: 22, fill: '#f7f9fc', stroke: C.grid, 'stroke-width': 1.5 }, svg);
      const card = el('g', {}, svg);
      el('rect', { x: x0, y: y0, width: TW, height: TH, rx: 22, fill: TYC[t], 'fill-opacity': .1, stroke: TYC[t], 'stroke-width': 2 }, card);
      txt(TYL[t], { x: x0 + 24, y: y0 + 40, 'font-size': 24, 'font-weight': 700, fill: TYC[t] }, card);
      txt(desc, { x: x0 + 24, y: y0 + 68, 'font-size': 17, fill: C.ink2 }, card);
      txt(cnt[t].toLocaleString('en'), { x: x0 + TW - 22, y: y0 + 54, 'text-anchor': 'end', 'font-size': 46, 'font-weight': 700, fill: TYC[t] }, card);
      txt(`${Math.round(100 * cnt[t] / tot)}% of stations`, { x: x0 + 24, y: y0 + 92, 'font-size': 16, fill: C.muted }, card);
      const day = el('g', {}, svg);
      const sx = h => x0 + 26 + h / 23 * (TW - 52), z = y0 + TH - 62, sy = v => z - v / 3.3 * 34;
      el('rect', { x: sx(6.5), width: sx(9.5) - sx(6.5), y: z - 36, height: 72, fill: '#dbeafe' }, day);
      el('line', { x1: sx(0), x2: sx(23), y1: z, y2: z, stroke: C.muted, 'stroke-width': 1 }, day);
      el('path', { d: 'M' + PR[t].map((v, h) => sx(h).toFixed(1) + ',' + sy(v).toFixed(1)).join('L'), fill: 'none', stroke: TYC[t], 'stroke-width': 3.5, 'stroke-linejoin': 'round' }, day);
      [0, 6, 12, 18].forEach(h => txt(h + ':00', { x: sx(h), y: y0 + TH - 10, 'text-anchor': 'middle', 'font-size': 13, fill: C.muted }, day));
      txt('a typical day: ↑ bikes leave, ↓ bikes arrive', { x: sx(23), y: z - 40, 'text-anchor': 'end', 'font-size': 13, fill: C.muted }, day);
      [card, day].forEach(g => { g.style.transition = 'opacity 450ms'; g.style.opacity = 0; });
      tiles[t] = { card, day };
    });
    const bal = txt(`Balanced, within ±10% of docks on both counts: ${cnt.B} stations`, { x: L, y: H - 12, 'font-size': 17, fill: C.muted }, svg);
    const call = txt(`${(cnt.G1 + cnt.G2).toLocaleString('en')} stations are emptied every morning: ${cnt.G2} recover by night, ${cnt.G1} do not`,
                     { x: L, y: H - 12, 'font-size': 20, 'font-weight': 700, fill: C.red }, svg);
    const side = sideItems('quad');
    IX.quad = {
      steps: 4,
      cues: ['Two questions for every station: is it emptied during the 7–9 am commute (columns), and is it still short at the end of the day (rows)?',
             'Sorted by their answers, the stations fall into four groups.',
             'Each tile shows a typical day for its group: up means bikes leave, down means bikes arrive. The blue band is 7–9 am.',
             'The right column is the 1,596 stations emptied every morning. 703 recover by night; 893 never do. Why?'],
      set(k) {
        Object.entries(tiles).forEach(([t, o]) => {
          const dim = k === 3 && (t === 'G3' || t === 'G4');
          o.card.style.opacity = k >= 1 ? (dim ? .25 : 1) : 0;
          o.day.style.opacity = k >= 2 ? (dim ? .25 : 1) : 0;
        });
        fade(bal, k >= 1 && k < 3); fade(call, k === 3); reveal(side, k + 1);
      },
    };
    stop(box);
  })();

"""

GUMAP_REVEAL = ("        reveal(side, k + 1);\n      },\n    };\n    stop(box);\n  })();\n\n  // ---------- elevation",
                "        reveal(side, k === 0 ? 1 : k === 1 ? 3 : side.length);   // losing and gaining together on the morning step\n"
                "      },\n    };\n    stop(box);\n  })();\n\n  // ---------- elevation")

# ---------- cover: Seoul's terrain as a quiet topographic map, instead of the drawn hill ----------
COVER_OLD = re.compile(r'<svg class="cover-hill".*?</svg>', re.S)


def cover_map(D):
    """Seoul's elevation from the deck's own 1 km terrain grid, softened, with the 100 and 200 m contours and the
    25 district lines on top."""
    F = D["frame"]
    clip = "".join(f'<path d="{u["d"]}"/>' for u in D["gu"])
    cells = []
    for t in D["terrain"]:
        op = min(1.0, max(0.0, (t["e"] - 25) / 260)) ** 0.75
        if op > 0.02:
            cells.append(f'<rect x="{t["x"] - 1}" y="{t["y"] - 1}" width="{F["cell"] + 2}" height="{F["cell"] + 2}" fill-opacity="{op:.2f}"/>')
    g = [f'<defs><clipPath id="cv-seoul">{clip}</clipPath><filter id="cv-soft" x="-5%" y="-5%" width="110%" height="110%">'
         f'<feGaussianBlur stdDeviation="7"/></filter></defs>',
         f'<g clip-path="url(#cv-seoul)"><rect width="{F["w"]}" height="{F["h"]}" fill="#F4F8FF"/>'
         f'<g fill="#3182F6" filter="url(#cv-soft)">{"".join(cells)}</g>']
    for c in D["contours"]:
        if c["level"] >= 100:
            g.append(f'<path d="{c["d"]}" fill="none" stroke="#1B64DA" stroke-opacity=".35" stroke-width=".8" vector-effect="non-scaling-stroke"/>')
    g.append("</g>")
    for u in D["gu"]:
        g.append(f'<path d="{u["d"]}" fill="none" stroke="#ffffff" stroke-width="1.2" vector-effect="non-scaling-stroke"/>')
    H = 470
    W = round(H * F["w"] / F["h"])
    return (f'<div style="position:absolute;right:128px;top:540px;width:{W}px">'
            f'<svg width="{W}" height="{H}" viewBox="0 0 {F["w"]} {F["h"]}" aria-hidden="true">{"".join(g)}</svg>'
            f'<p style="margin:4px 0 0;font-size:18px;color:var(--muted);text-align:right">Seoul by ground elevation: darker is higher</p></div>'
            + '<div style="position:absolute;left:128px;top:952px;width:900px;border-top:2px solid #e5e8eb;padding-top:18px">'
              '<p style="margin:0;font-size:20px;line-height:1.5;color:var(--muted)">Data: every Seoul Bike trip in 2024 and 2025 (Seoul Open Data), '
              'KMA hourly weather, and the Seoul 1:5,000 digital topographic map</p></div>')

# ---------- slide "weather": each station's rentals by 5 C band of its local daily maximum (2024-2025 weekdays) ----------
# data: data/station_tmax_band.csv from scripts/19_station_tmax.py, injected by build_final_deck.py as __TMAX_BAND__
WEATHER_SIDE = """
<div class="stat"><p class="stat-num">13 → 41</p><p class="stat-lab">median rentals a weekday per station, from highs below 0&nbsp;°C to highs of 20–25&nbsp;°C</p></div>
<div class="stat"><p class="stat-num blue">Flat</p><p class="stat-lab">from 20&nbsp;°C to 35&nbsp;°C (about 40); only above 35&nbsp;°C a small dip, to 36</p></div>
<div class="stat"><p class="stat-lab" style="font-size:20px">Each dot is one station in one band: its mean rentals on the weekdays of 2024 and 2025 whose maximum, at the nearest of 27 KMA weather stations, fell in that band (bands with 5 or more such days; 25,225 dots from 2,878 stations). Dots are spread sideways within the band so they do not overlap.</p></div>
"""

WEATHER = r"""  // ---------- weather: every station, rentals by 5 °C band of its local daily maximum (jittered) ----------
  (function () {
    const box = document.getElementById('ix-wx'); if (!box) return;
    const TB = __TMAX_BAND__, W = 1071, H = 580, L = 96, R = 24, T = 60, B = 80, YMAX = 120;   // the top 5% or so of busy stations are drawn at the top, so the medians stand apart
    const svg = makeSvg(box, W, H);
    const nb = TB.length, bw = (W - L - R) / nb, cx = j => L + bw * (j + .5), y = v => H - B - Math.min(v, YMAX) / YMAX * (H - T - B);
    axisY(svg, L, R, W, y, [0, 30, 60, 90, 120], v => v);
    TB.forEach((b, j) => txt(b.lab, { x: cx(j), y: H - B + 28, 'text-anchor': 'middle', 'font-size': 17, fill: C.muted }, svg));
    txt('Daily maximum temperature at the station (°C, nearest KMA weather station)', { x: (L + W - R) / 2, y: H - B + 60, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, svg);
    ylab(svg, 'Mean rentals per weekday at the station', T, H, B);
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;   // fixed jitter, same every time
    const pg = el('g', {}, svg);
    TB.forEach((b, j) => b.v.forEach(v => el('circle', { cx: cx(j) + (rnd() - .5) * bw * .8, cy: y(v), r: 1.7,
      fill: b.lo >= 20 ? C.blue : C.light, 'fill-opacity': .28 }, pg)));
    const med = el('g', {}, svg);
    TB.forEach((b, j) => {
      el('line', { x1: cx(j) - bw * .42, x2: cx(j) + bw * .42, y1: y(b.med), y2: y(b.med), stroke: C.navy, 'stroke-width': 6, 'stroke-linecap': 'round' }, med);
      halo(txt(Math.round(b.med), { x: cx(j), y: y(b.med) - 14, 'text-anchor': 'middle', 'font-size': 19, 'font-weight': 700, fill: C.navy }, med));
    });
    const top = TB.reduce((a, b) => a + b.v.filter(v => v > YMAX).length, 0), all = TB.reduce((a, b) => a + b.v.length, 0);
    txt(`One dot = one station in one band (${all.toLocaleString('en')}); bar = median. ${top.toLocaleString('en')} dots above ${YMAX} (${(100 * top / all).toFixed(0)}%) are drawn at the top.`,
        { x: L + 8, y: T - 30, 'font-size': 16, fill: C.muted }, svg);
    const side = sideItems('weather');
    IX.weather = {
      steps: 2,
      cues: ['Every station, in every 5-degree band of the day’s maximum temperature where it stands: each dot is its mean rentals on those weekdays.',
             'The bars are the medians: 13 rentals a day on days below zero, rising to 41 at 20 to 25 degrees, then flat up to 35 degrees. Only above 35 a small dip.'],
      set(k) { fade(med, k >= 1, 600); reveal(side, k === 0 ? 0 : side.length); },
    };
    stop(box);
  })();

"""
