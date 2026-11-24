"""Step 1i (part 2): bare-earth station elevation by linear interpolation on a Delaunay triangulation (TIN) of the
contour vertices and spot heights exported by scripts/17_tin_export.R.

Why: the IDW surface of scripts/12_dem_contour.R snaps a station near a contour to that contour's height, so 29% of
stations sit on an exact multiple of 5 m. On a TIN the height changes linearly between neighbouring contours.
Known TIN weakness: a triangle whose three corners are on the same contour is flat (hill tops, valley floors between
two lines of the same height); those stations are counted and reported.

Run from the project root:  python scripts/17_tin_elevation.py
Output: data/station_elevation_tin.csv  station_no, elev_tin_m, flat (1 if the triangle's corners share one height)
"""
import csv
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay

ROOT = Path(__file__).resolve().parent.parent
pts = np.loadtxt(ROOT / "raw/derived/tin_points.csv", delimiter=",", skiprows=1)
xy, z = pts[:, :2], pts[:, 2]
# the same location can come twice (a spot height on a contour vertex); keep the first
_, first = np.unique(np.round(xy, 2), axis=0, return_index=True)
xy, z = xy[np.sort(first)], z[np.sort(first)]
print(f"points {len(z):,}")

with open(ROOT / "raw/derived/tin_stations.csv", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
sxy = np.array([[float(r["x"]), float(r["y"])] for r in rows])

tri = Delaunay(xy)
simp = tri.find_simplex(sxy)
out = []
for k, (r, s) in enumerate(zip(rows, simp)):
    if s < 0:
        out.append((r["station_no"], "", ""))
        continue
    v = tri.simplices[s]
    T = tri.transform[s]
    b = T[:2].dot(sxy[k] - T[2])
    w = np.append(b, 1 - b.sum())
    zz = z[v]
    out.append((r["station_no"], round(float(w.dot(zz)), 2), int(np.ptp(zz) == 0)))

with open(ROOT / "data/station_elevation_tin.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["station_no", "elev_tin_m", "flat"])
    wr.writerows(out)

e = np.array([o[1] for o in out if o[1] != ""], dtype=float)
flat = sum(1 for o in out if o[2] == 1)
mult5 = int(np.sum(np.isclose(e / 5, np.round(e / 5))))
print(f"stations {len(out):,}, outside the triangulation {sum(1 for o in out if o[1] == ''):,}, flat triangles {flat:,}")
print(f"elevation min {e.min():.1f}, median {np.median(e):.1f}, max {e.max():.1f}; exact multiple of 5 m: {mult5:,} ({100 * mult5 / len(e):.1f}%)")
sys.stdout.flush()
