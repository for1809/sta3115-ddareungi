"""Builds viz/gu_hourly_map.html: Seoul districts (gu) shaded by 2025 weekday average rentals per hour.

Inputs : data/stations.csv (gu, lat, lon, months_active), data/station_hour.csv (weekday dep per station x hour)
Template: viz/gu_hourly_map.template.html (the /*__DATA__*/ marker is replaced by the JSON below)
Rentals = departures (집계_기준 = 출발시간 rows), averaged over the 244 weekdays of 2025 (holidays excluded).
District shapes are drawn in the page from the bike stations themselves (Voronoi cells clipped to 650 m),
so no boundary file is needed; areas without stations (mountains, the river) stay blank.
Run from the project folder: python viz/build_gu_hourly_map.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


st = [r for r in read("data/stations.csv") if int(r["months_active"]) > 0]
gus = sorted({r["gu"] for r in st})
gi = {g: i for i, g in enumerate(gus)}
gu_of = {r["station_no"]: r["gu"] for r in st}

dep = defaultdict(lambda: [0.0] * 24)
for r in read("data/station_hour.csv"):
    if r["daytype"] == "weekday" and r["station_no"] in gu_of:
        dep[gu_of[r["station_no"]]][int(r["hour"])] += float(r["dep"])

count = defaultdict(int)
for r in st:
    count[r["gu"]] += 1

data = {
    "gus": [{"name": g, "short": g[:-1] if len(g) > 2 else g, "stations": count[g],
             "dep": [round(v, 1) for v in dep[g]]} for g in gus],
    # [lon, lat, gu index] per station, 5 decimals is about 1 m
    "pts": [[round(float(r["lon"]), 5), round(float(r["lat"]), 5), gi[r["gu"]]] for r in st],
    "weekdays": 244,
}
tpl = Path("viz/gu_hourly_map.template.html").read_text(encoding="utf-8")
out = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
Path("viz/gu_hourly_map.html").write_text(out, encoding="utf-8")
total = sum(sum(g["dep"]) for g in data["gus"])
print(f"districts {len(gus)}, stations {len(st)}, weekday rentals per day {total:,.0f}, html {len(out) / 1e3:.0f} kB")
