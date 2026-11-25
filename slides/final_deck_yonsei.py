"""Yonsei–Sinchon flow inset, using the agreed rectangle and existing assets.

Bounds: longitude 126.925–126.955, latitude 37.550–37.585.
Keep trips with BOTH endpoints inside; aggregate to EPSG:5179 500 m cells,
subtract reverse flows, and display the largest 30 positive whole-day flows.
Divide trip totals by the existing 378 selected weekdays. Cell locations and
elevations use all stations in each cell, matching step4_flow_prep.py.
The local example is not used to recompute citywide percentages.
"""
import csv
import gzip
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = (126.925, 126.955, 37.550, 37.585)


def project(lon, lat):
    """GRS80 transverse Mercator series for EPSG:5179 (metres).

    Central meridian 127.5°, origin 38°, scale .9996, false easting/northing
    1,000,000/2,000,000. Series through A^6; Seoul is near the central meridian.
    """
    a, f, scale = 6378137.0, 1 / 298.257222101, .9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    phi, lam = math.radians(lat), math.radians(lon - 127.5)

    def meridian(p):
        return a * ((1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * p
                    - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * p)
                    + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * p)
                    - 35 * e2**3 / 3072 * math.sin(6 * p))

    n = a / math.sqrt(1 - e2 * math.sin(phi)**2)
    t, c, aa = math.tan(phi)**2, ep2 * math.cos(phi)**2, math.cos(phi) * lam
    x = 1e6 + scale * n * (aa + (1 - t + c) * aa**3 / 6
                          + (5 - 18*t + t*t + 72*c - 58*ep2) * aa**5 / 120)
    y = 2e6 + scale * (meridian(phi) - meridian(math.radians(38))
                      + n * math.tan(phi) * (aa*aa / 2 + (5 - t + 9*c + 4*c*c) * aa**4 / 24
                                             + (61 - 58*t + t*t + 600*c - 330*ep2) * aa**6 / 720))
    return x, y


def inset(data):
    with open(ROOT / 'data/od_2024_2025/master/station_master_final.csv', encoding='utf-8-sig') as fh:
        stations = {r['st_id']: r for r in csv.DictReader(fh) if r['st_id']}
    cells = defaultdict(list)
    for row in stations.values():
        row['x'], row['y'] = project(float(row['lon']), float(row['lat']))
        row['cell'] = (int(row['x'] // 500), int(row['y'] // 500))
        cells[row['cell']].append(row)

    # Recover the embedded map's linear projected-coordinate frame. Verify it
    # against thousands of station positions before reusing its terrain paths.
    with open(ROOT / 'data/od_2024_2025/od/s0_station_summary.csv', encoding='utf-8-sig') as fh:
        ordered = [r for r in csv.DictReader(fh) if r['enough_days'] == 'True']
    assert len(ordered) == len(data['stations'])
    matches = [(stations[r['st_id']], p) for r, p in zip(ordered, data['stations'])]
    fitted = []
    for coord in ('x', 'y'):
        design = np.array([[r[coord], 1] for r, _ in matches])
        target = np.array([p[coord] for _, p in matches])
        coef = np.linalg.lstsq(design, target, rcond=None)[0]
        residual = np.abs(design @ coef - target)
        assert residual.max() < .2, (coord, residual.max())
        fitted.append(coef)
    (ax, bx), (ay, by) = fitted
    lo, hi, bottom, top = BOUNDS
    selected = {k for k, r in stations.items()
                if lo <= float(r['lon']) <= hi and bottom <= float(r['lat']) <= top}
    flows = defaultdict(int)
    trip_total = 0
    with gzip.open(ROOT / 'data/od_2024_2025/od/od_pairs_all_clearweekday.csv.gz', 'rt') as fh:
        for r in csv.DictReader(fh):
            if r['st_o'] not in selected or r['st_d'] not in selected or r['st_o'] == r['st_d']:
                continue
            origin, dest = stations[r['st_o']]['cell'], stations[r['st_d']]['cell']
            trip_total += int(r['n_day'])
            if origin != dest:
                flows[(origin, dest)] += int(r['n_day'])

    centers = {}
    for key, rows in cells.items():
        centers[key] = (np.mean([r['x'] for r in rows]), np.mean([r['y'] for r in rows]),
                        np.mean([float(r['elevation_m']) for r in rows if r['elevation_m']]))
    edges = sorted(((n - flows.get((dest, origin), 0), origin, dest)
                    for (origin, dest), n in flows.items()
                    if n > flows.get((dest, origin), 0)), key=lambda e: (-e[0], e[1], e[2]))[:30]

    corners = [project(lon, lat) for lon in (lo, hi) for lat in (bottom, top)]
    # Include selected cell centroids so arrows remain within the visible inset.
    points = corners + [(centers[k][0], centers[k][1]) for _, a, b in edges for k in (a, b)]
    x0, x1 = min(x for x, _ in points) - 100, max(x for x, _ in points) + 100
    y0, y1 = min(y for _, y in points) - 100, max(y for _, y in points) + 100
    unit = 1000 / (x1 - x0)
    xy = lambda x, y: (round((x - x0) * unit, 1), round((y1 - y) * unit, 1))
    arrows = []
    for total, origin, dest in edges:
        xo, yo, eo = centers[origin]
        xd, yd, ed = centers[dest]
        px, py = xy(xo, yo)
        qx, qy = xy(xd, yd)
        arrows.append(dict(x1=px, y1=py, x2=qx, y2=qy, net=round(total / 378, 3),
                           c='down' if eo-ed >= 5 else 'up' if eo-ed <= -5 else 'side'))

    number = r'-?\d+(?:\.\d+)?'
    pair = re.compile(f'({number}),({number})')

    def remap(path):
        def point(m):
            px, py = xy((float(m[1]) - bx) / ax, (float(m[2]) - by) / ay)
            return f'{px},{py}'
        return pair.sub(point, path)

    labels = []
    # Yonsei coordinate from data/universities_clean.csv; station-derived Sinchon.
    with open(ROOT / 'data/universities_clean.csv', encoding='utf-8-sig') as fh:
        university = next(r for r in csv.DictReader(fh) if '연세대학교' in r.values())
    # The CSV's known schema uses lat/lon; avoid dependence on external geocoding.
    ux, uy = project(float(university['lon']), float(university['lat']))
    px, py = xy(ux, uy)
    labels.append(dict(en='Yonsei University', x=px, y=py))
    sinchon = [r for k, r in stations.items() if k in selected and '신촌역' in r['name']]
    assert sinchon, 'Sinchon station landmark missing'
    px, py = xy(np.mean([r['x'] for r in sinchon]), np.mean([r['y'] for r in sinchon]))
    labels.append(dict(en='Sinchon Station', x=px, y=py))
    terrain = []
    for r in data['terrain']:
        px, py = xy((r['x'] - bx) / ax, (r['y'] - by) / ay)
        terrain.append(dict(x=px, y=py, e=r['e']))
    return dict(h=round((y1-y0)*unit), arrows=arrows,
                contours=[dict(level=r['level'], d=remap(r['d'])) for r in data['contours']],
                gu=[dict(en=r['en'], d=remap(r['d'])) for r in data['gu']], labels=labels,
                terrain=terrain, cell=round(data['frame']['cell'] / ax * unit, 2),
                meta=dict(bounds=list(BOUNDS), stations=len(selected), internal_trips=trip_total,
                          selection='top 30 positive net flows between 500 m cells; both endpoints inside bounds',
                          classification='cell mean elevation difference >=5 m downhill, <=-5 m uphill, otherwise similar elevation'))


def apply(html):
    m = re.search(r'(<script[^>]*id="ixdata"[^>]*>)(.*?)(</script>)', html, re.S)
    data = json.loads(m[2])
    data['zoom'] = inset(data)
    html = html[:m.start(2)] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + html[m.end(2):]
    section = re.search(r'<section\b[^>]*id="vec".*?</section>', html, re.S)
    revised = re.sub(r'<h2>.*?</h2>', '<h2>Net bicycle flow runs downhill</h2>', section[0], count=1, flags=re.S)
    revised, count = re.subn(r'<div class="stat"><p class="stat-num">1% uphill</p>.*?</div>', '', revised, count=1, flags=re.S)
    assert count == 1
    note = ('Each citywide arrow summarizes net bicycle movement around a 1 km cell. On sloping ground, '
            '69% of the reported whole-day net-flow magnitude points downhill and 7% uphill. '
            'On the right, we zoom into the familiar Yonsei–Sinchon area. The red arrows show net movement toward lower ground, '
            'while blue arrows point toward higher ground. Many of the strongest connections here also run downhill. '
            'This is net movement, not the share of individual trips or evidence of how individual riders return home.')
    revised = re.sub(r'<aside>.*?</aside>', lambda _: f'<aside>{note}</aside>', revised, count=1, flags=re.S)
    html = html[:section.start()] + revised + html[section.end():]
    old = "    Z.contours.forEach(c =>"
    html = html.replace(old, "    Z.terrain.forEach(t => el('rect', { x: t.x, y: t.y, width: Z.cell, height: Z.cell, fill: ramp(t.e) }, right));\n" + old, 1)
    html = html.replace('Zoom: Seodaemun, Jongno, Seongbuk. The 120 biggest net flows between 500 m cells',
                        'Yonsei–Sinchon · 30 strongest net connections')
    html = html.replace('Zoom into Seodaemun, Jongno and Seongbuk: the biggest net flows pour down from the hills to the valleys. Uphill: 1%.',
                        'Yonsei–Sinchon: compare the net-flow directions with the terrain. Both trip endpoints are inside the selected rectangle.')
    start = html.index('  // ---------- flow field (whole city) and the zoom')
    end = html.index('  // ----------', start + 10)
    chart = html[start:end]
    chart = chart.replace('x: W - ZWW, y: 40', 'x: MW + (W - MW - ZWW) / 2, y: 40', 1)
    chart = chart.replace('x: W - ZWW, y: 26', 'x: MW + 100, y: 26', 1)
    chart = chart.replace("'font-size': 30, 'font-weight': 700, fill: C.ink2", "'font-size': 48, 'font-weight': 700, fill: C.ink2")
    chart = chart.replace('height: Z.cell, fill: ramp(t.e)', 'height: Z.cell, fill: ramp(t.e), opacity: .45')
    chart = chart.replace("'stroke-opacity': .7", "'stroke-opacity': .35")
    chart = chart.replace("'stroke-dasharray': '7 5'", "'stroke-dasharray': '7 5', 'stroke-opacity': .3")
    arrow_start = chart.index('    Z.arrows.slice().reverse().forEach(a => {')
    arrow_end = chart.index('    Z.labels.forEach', arrow_start)
    # Paint every halo before the colored marks, then all filled heads on top.
    # Keep the existing flows, direction colors and magnitude-based line widths.
    arrow_js = r"""    const arrowHalos = el('g', {}, right), arrowLines = el('g', {}, right), arrowHeads = el('g', {}, right);
    Z.arrows.slice().reverse().forEach(a => {
      const dx = a.x2 - a.x1, dy = a.y2 - a.y1, n = Math.hypot(dx, dy);
      if (!n) return;
      const ux = dx / n, uy = dy / n, hx = -uy, hy = ux;
      const head = Math.min(32, n * .3), half = head * .52;
      const x1 = a.x1 + ux * 6, y1 = a.y1 + uy * 6;
      const tipX = a.x2 - ux * 8, tipY = a.y2 - uy * 8;
      const baseX = tipX - ux * head, baseY = tipY - uy * head;
      const color = a.c === 'down' ? C.red : a.c === 'up' ? C.blue : '#687585';
      const width = 2.2 + 4.8 * a.net / zmax;
      const shaft = { x1, y1, x2: baseX, y2: baseY, 'stroke-linecap': 'round', 'vector-effect': 'non-scaling-stroke' };
      el('line', { ...shaft, stroke: '#fff', 'stroke-width': width + 2.5, 'stroke-opacity': .95 }, arrowHalos);
      el('line', { ...shaft, stroke: color, 'stroke-width': width }, arrowLines);
      el('polygon', { points: `${tipX},${tipY} ${baseX + hx * half},${baseY + hy * half} ${baseX - hx * half},${baseY - hy * half}`,
        fill: color, stroke: '#fff', 'stroke-width': .8, 'stroke-linejoin': 'round', 'vector-effect': 'non-scaling-stroke' }, arrowHeads);
    });
"""
    chart = chart[:arrow_start] + arrow_js + chart[arrow_end:]
    return html[:start] + chart + html[end:]
