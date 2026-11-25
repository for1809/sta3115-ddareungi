"""Numbers for the storyline slides drawn by slides/final_deck_new.py.

1. Hourly stock, 2025 dry weekdays (rules as scripts/15_inventory_2x2.py): mean bikes and share of readings with 0 bikes,
   by hour, for station types = elevation band (bare earth) x subway-distance quarter.
2. Morning net outflow (07-09 h rentals minus returns, team table, 2024-2025 clear weekdays) by morning temperature
   (mean of the 07, 08, 09 h readings at the station's nearest AWS, aws_id in data/station_master.csv) and elevation band.
Output  data/story_numbers.json
Run     python analysis/story_numbers.py
"""
import csv, gzip, json, math, importlib.util
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sp = importlib.util.spec_from_file_location("inv15", R / "scripts/15_inventory_2x2.py"); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
d = R / "data"
master = [r for r in csv.DictReader(open(d / "station_master.csv", encoding="utf-8-sig"))]
ok = [r for r in master if r["subway_m"] and r["elev_bare_m"] and r["am_empty_dry"]]
qs = sorted(float(r["subway_m"]) for r in ok); cut = [qs[len(qs) * k // 4] for k in (1, 2, 3)]
band = lambda e: "hill" if e >= 40 else ("flat" if e < 20 else "mid")
typ, eb_no, eb_id, aws_of = {}, {}, {}, {}
for r in master:
    if r["elev_bare_m"]:
        b = band(float(r["elev_bare_m"]))
        eb_no[r["station_no"]] = b; eb_id[r["station_id"]] = b; aws_of[r["station_id"]] = r["aws_id"]
        if r["subway_m"]:
            typ[r["station_no"]] = (b, sum(float(r["subway_m"]) >= c for c in cut))
out = {"subway_cuts": [round(c) for c in cut]}

# ---- 1. hourly stock
feats = M.read(d / "station_features.csv")
rain = {(r["aws_id"], date.fromisoformat(r["date"])): (float(r["rain_day"]) if r["rain_day"] != "" else None) for r in M.read(d / "weather_daily.csv")}
have = {a for a, _ in rain}; aws = [a for a in M.read(d / "aws_stations.csv") if a["aws_id"] in have]
near = {s["station_no"]: min(aws, key=lambda a: M.km(float(s["lat"]), float(s["lon"]), float(a["lat"]), float(a["lon"])))["aws_id"] for s in feats}
acc = defaultdict(lambda: [0, 0, 0])            # (band, quarter, hour) -> readings, bikes, zero readings
rows = 0
for z in sorted((R / "raw/inv_1h").glob("2025Q?.zip")):
    for r in M.members(z):
        next(r)
        for row in r:
            if len(row) < 5: continue
            try:
                day = date.fromisoformat(row[0][:10]); h, c = int(row[3]), int(row[4])
            except ValueError:
                continue
            if day.year != 2025 or not M.weekday(day): continue
            num = row[1].strip(); st = f"{int(num):05d}" if num.isdigit() else num
            if st not in typ or st not in near: continue
            v = rain.get((near[st], day))
            if v is None or v >= 1: continue
            a = acc[typ[st] + (h,)]; a[0] += 1; a[1] += c; a[2] += c == 0; rows += 1
    print(z.name, "done", flush=True)
out["stock_rows"] = rows
out["stock"] = [{"band": b, "q": q, "hour": h, "n": a[0], "mean": round(a[1] / a[0], 3), "empty": round(a[2] / a[0], 4)}
                for (b, q, h), a in sorted(acc.items())]

# ---- 2. morning temperature x elevation, net outflow
temp = defaultdict(list)
for p in sorted((R / "raw/weather").glob("aws_20[2][45]??.csv")):
    with open(p, encoding="utf-8", newline="") as fh:
        rr = csv.reader(fh); next(rr)
        for row in rr:
            if not row or not row[3].strip() or row[3].strip() == "-": continue
            ts = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
            if ts.hour in (7, 8, 9): temp[(row[0], ts.date().isoformat())].append(float(row[3]))
tm = {k: sum(v) / len(v) for k, v in temp.items() if len(v) >= 2}
BANDS = [(-99, 0, "< 0"), (0, 5, "0–5"), (5, 10, "5–10"), (10, 15, "10–15"), (15, 20, "15–20"), (20, 25, "20–25"), (25, 99, "25+")]
wx = defaultdict(lambda: [0, 0.0, 0.0]); miss = used = 0; days = defaultdict(set)
with gzip.open(d / "od_2024_2025/od/s0_station_daily.csv.gz", "rt", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["clear_weekday"] != "True" or r["st_id"] not in eb_id: continue
        t = tm.get((aws_of[r["st_id"]], r["date"]))
        if t is None: miss += 1; continue
        lab = next(l for lo, hi, l in BANDS if lo <= t < hi)
        a = wx[(eb_id[r["st_id"]], lab)]; a[0] += 1; a[1] += float(r["am_net"]); a[2] += float(r["am_rent"]); used += 1
        days[lab].add(r["date"])
out["wx_rows"] = used; out["wx_missing_temp"] = miss
out["wx"] = [{"band": b, "temp": l, "n": a[0], "net": round(a[1] / a[0], 3), "rent": round(a[2] / a[0], 3)} for (b, l), a in wx.items()]
out["wx_days"] = {l: len(v) for l, v in days.items()}
json.dump(out, open(R / "data/story_numbers.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("stock rows", rows, "wx rows", used, "missing temp", miss)
