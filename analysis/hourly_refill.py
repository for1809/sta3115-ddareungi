"""When do bikes come back to the hills? Hourly stock and refills by elevation band, 2025 dry weekdays.

For every station-day with stock readings at hour h and h+1:
  rides in (h)  = returns - rentals in hour h (trip records)
  other in (h)  = (stock at h+1 - stock at h) - rides in (h)   > 0: bikes added by something other than riders, mostly trucks
Hour h's reading is taken as the stock at the start of hour h (the raw files do not say), so a refill may sit an hour off.
Days and rain rule as scripts/15_inventory_2x2.py (2025 weekdays without holidays; nearest AWS under 1 mm for the day).
Bands by bare-earth elevation (elev_bare_m, data/station_master.csv); hill40+/G1 and /G2 split the hills by the 2x2 group.

Inputs   data/station_features.csv, data/weather_daily.csv, data/aws_stations.csv, data/station_master.csv,
         raw/od_5min/2025MM.zip, raw/inv_1h/2025Q?.zip
Output   data/hourly_refill_2025.csv  band, hour, readings, stock, empty_share, pairs, rides_in, other_in
         analysis/hourly_refill_log.txt
Run      python analysis/hourly_refill.py
"""
import csv, sys, importlib.util
from collections import defaultdict
from datetime import date
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sp = importlib.util.spec_from_file_location("inv15", R / "scripts/15_inventory_2x2.py"); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
d = R / "data"
feats = M.read(d / "station_features.csv"); id2no = {f["station_id"]: f["station_no"] for f in feats}
rain = {(r["aws_id"], date.fromisoformat(r["date"])): (float(r["rain_day"]) if r["rain_day"] != "" else None) for r in M.read(d / "weather_daily.csv")}
have = {a for a, _ in rain}; aws = [a for a in M.read(d / "aws_stations.csv") if a["aws_id"] in have]
near = {s["station_no"]: min(aws, key=lambda a: M.km(float(s["lat"]), float(s["lon"]), float(a["lat"]), float(a["lon"])))["aws_id"] for s in feats}
band, grp = {}, {}
for r in csv.DictReader(open(d / "station_master.csv", encoding="utf-8-sig")):
    if r["elev_bare_m"]:
        e = float(r["elev_bare_m"]); band[r["station_no"]] = "hill40+" if e >= 40 else ("flat<20" if e < 20 else "mid20-40")
        grp[r["station_no"]] = r["group_2x2"][:2]
def dry(st, day):
    v = rain.get((near[st], day)); return v is not None and v < 1
trips = {}
for z in sorted((R / "raw/od_5min").glob("2025??.zip")):
    for r in M.members(z):
        ix = {M.EN.get(h, h): i for i, h in enumerate(next(r))}
        for row in r:
            s = row[ix["기준_날짜"]]; day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
            if day.year != 2025 or not M.weekday(day): continue
            h, n = int(row[ix["기준_시간대"]][:2]), int(row[ix["전체_건수"]]); out = row[ix["집계_기준"]] == "출발시간"
            st = id2no.get(row[ix["시작_대여소_ID"]] if out else row[ix["종료_대여소_ID"]])
            if not st or st not in band or not dry(st, day): continue
            t = trips.get((st, day))
            if t is None: t = trips[(st, day)] = [0] * 48
            t[h * 2 + (0 if out else 1)] += n
    print("OD", z.name, flush=True)
inv = {}
for z in sorted((R / "raw/inv_1h").glob("2025Q?.zip")):
    for r in M.members(z):
        next(r)
        for row in r:
            if len(row) < 5: continue
            try: day = date.fromisoformat(row[0][:10]); h, c = int(row[3]), int(row[4])
            except ValueError: continue
            if day.year != 2025 or not M.weekday(day): continue
            num = row[1].strip(); st = f"{int(num):05d}" if num.isdigit() else num
            if st not in band or st not in near or not dry(st, day): continue
            v = inv.get((st, day))
            if v is None: v = inv[(st, day)] = [None] * 24
            v[h] = c
    print("INV", z.name, flush=True)
acc = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0])   # n pairs, other, ride net in, stock at h, zero-stock count
for (st, day), v in inv.items():
    t = trips.get((st, day), [0] * 48)
    for key in (band[st], band[st] + "/" + grp[st]):
        for h in range(24):
            if v[h] is not None:
                a = acc[(key, h, "stock")]; a[0] += 1; a[3] += v[h]; a[4] += v[h] == 0
            if h < 23 and v[h] is not None and v[h + 1] is not None:
                ride_in = t[h * 2 + 1] - t[h * 2]
                a = acc[(key, h, "flow")]; a[0] += 1; a[1] += (v[h + 1] - v[h]) - ride_in; a[2] += ride_in
keys = ["flat<20", "mid20-40", "hill40+", "hill40+/G1", "hill40+/G2"]
with open(d / "hourly_refill_2025.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["band", "hour", "readings", "stock", "empty_share", "pairs", "rides_in", "other_in"])
    for k in keys:
        for h in range(24):
            s_, f = acc[(k, h, "stock")], acc[(k, h, "flow")]
            w.writerow([k, h, s_[0], round(s_[3] / s_[0], 3), round(s_[4] / s_[0], 4), f[0],
                        round(f[2] / f[0], 3) if f[0] else "", round(f[1] / f[0], 3) if f[0] else ""])
log = ["station-days (readings at 00 h) by band: " + str({k: acc[(k, 0, 'stock')][0] for k in keys})]
for k in keys:
    o = [acc[(k, h, "flow")] for h in range(23)]
    tot = sum(f[1] / f[0] for f in o if f[0])
    night = sum(o[h][1] / o[h][0] for h in range(1, 7) if o[h][0])
    log.append(f"{k}: other moves over the day {tot:+.2f} bikes; 01-06 h {night:+.2f}; empty at 06 h "
               f"{acc[(k, 6, 'stock')][4] / acc[(k, 6, 'stock')][0]:.1%}, at 09 h {acc[(k, 9, 'stock')][4] / acc[(k, 9, 'stock')][0]:.1%}")
(R / "analysis/hourly_refill_log.txt").write_text(chr(10).join(log) + chr(10), encoding="utf-8")
print(chr(10).join(log))
