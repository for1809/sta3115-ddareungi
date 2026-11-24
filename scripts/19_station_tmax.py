"""Step 19: rides against the day's maximum temperature where each station is, 2024-2025 weekdays.

The deck's earlier temperature chart used one citywide daily MEAN (KMA ASOS 108), which the night hours pull down.
Here every station gets the daily maximum of its nearest KMA AWS (29 Seoul stations, hourly), and its rentals
that day come from the team's station x date table.

Inputs  raw/weather/aws_2024MM.csv, aws_2025MM.csv (KMA AWS hourly: 지점, 지점명, 일시, 기온, 풍속, 강수량;
        scripts/08_fetch_kma_aws.mjs with KMA_YEAR=2024 / 2025)
        data/aws_stations.csv (AWS coordinates), data/od_2024_2025/master/station_master_final.csv (station coordinates),
        data/od_2024_2025/od/s0_station_daily.csv.gz (station x date rentals; 10 bad days already dropped)
Outputs data/aws_daily_2024_2025.csv  aws_id, date, tmax, tmin, tmean, rain_day, wind_mean, n_temp (hours with a temperature)
        data/station_tmax_bins.csv     weekday station-days by 1 C bin of local daily maximum: n, mean / median rentals per station
        data/station_tmax_band.csv     one row per station and 5 C band of local daily maximum (band = lower edge; < 0 C is -5,
                                       35 C and above is 35): weekdays in the band and the station's mean rentals on them
                                       (bands with at least 5 weekdays)
        data/19_station_tmax_log.txt   checks (rows, missing hours, how many station-days had a nearest AWS with data)
Rules   weekday = not a weekend or public holiday (offday False in the team table). A day's maximum and mean use the
        00:00-23:00 stamps of that date and need at least 20 hours; otherwise the next-nearest AWS with a valid day is used.
        rain_day sums the 01:00..23:00 stamps plus the next day's 00:00 (KMA rain at HH:00 fell in the hour before).
Run from the project root:  python scripts/19_station_tmax.py
"""
import csv
import gzip
import math
import statistics as S
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
log = []


def num(s):
    s = (s or "").strip()
    return float(s) if s not in ("", "-") else None


# ---- AWS hourly -> daily
hours = defaultdict(dict)                        # (aws, date) -> hour -> (temp, wind, rain)
rain_next = {}                                   # (aws, date) -> rain stamped 00:00 of that date (belongs to the day before)
for p in sorted((ROOT / "raw/weather").glob("aws_20[2][45]??.csv")):
    n = miss_t = 0
    with open(p, encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        head = next(r)
        assert head[:3] == ["지점", "지점명", "일시"], head
        for row in r:
            if not row:
                continue
            n += 1
            ts = datetime.strptime(row[2], "%Y-%m-%d %H:%M")
            t, w, rn = num(row[3]), num(row[4]), num(row[5])
            miss_t += t is None
            d = ts.date().isoformat()
            hours[(row[0], d)][ts.hour] = (t, w, rn)
            if ts.hour == 0:
                rain_next[(row[0], d)] = rn
    log.append(f"{p.name}: {n:,} rows, temperature missing {miss_t:,}")

daily = {}
with open(ROOT / "data/aws_daily_2024_2025.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["aws_id", "date", "tmax", "tmin", "tmean", "rain_day", "wind_mean", "n_temp"])
    for (aws, d), hh in sorted(hours.items()):
        ts = [v[0] for v in hh.values() if v[0] is not None]
        ws = [v[1] for v in hh.values() if v[1] is not None]
        nxt = (datetime.fromisoformat(d) + timedelta(days=1)).date().isoformat()
        rs = [hh[h][2] for h in range(1, 24) if h in hh and hh[h][2] is not None] + \
             ([rain_next[(aws, nxt)]] if rain_next.get((aws, nxt)) is not None else [])
        row = [aws, d, max(ts) if ts else "", min(ts) if ts else "", round(sum(ts) / len(ts), 2) if ts else "",
               round(sum(rs), 1) if rs else "", round(sum(ws) / len(ws), 2) if ws else "", len(ts)]
        wr.writerow(row)
        if len(ts) >= 20:
            daily[(aws, d)] = max(ts)
log.append(f"AWS-days {len(hours):,}; with >= 20 temperature hours {len(daily):,}")

# ---- station -> AWS stations ordered by distance
aws_xy = {r["aws_id"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(ROOT / "data/aws_stations.csv", encoding="utf-8"))}
aws_ids = sorted({a for a, _ in hours})
missing_xy = [a for a in aws_ids if a not in aws_xy]
log.append(f"AWS in the weather files {len(aws_ids)}, without coordinates {missing_xy}")


def dist(a, b):
    k = math.cos(math.radians(37.55))
    return math.hypot((a[0] - b[0]) * 111.0, (a[1] - b[1]) * 111.0 * k)


order = {}
for r in csv.DictReader(open(ROOT / "data/od_2024_2025/master/station_master_final.csv", encoding="utf-8-sig")):
    if r["st_id"] and r["lat"]:
        p = (float(r["lat"]), float(r["lon"]))
        order[r["st_id"]] = sorted((a for a in aws_ids if a in aws_xy), key=lambda a: dist(p, aws_xy[a]))

# ---- weekday station-days: rentals by local daily maximum (1 C bins)
bins = defaultdict(list)
per = defaultdict(list)                         # (station, 5 C band) -> rentals
n_all = n_nostn = n_first = n_later = n_none = 0
days = set()
with gzip.open(ROOT / "data/od_2024_2025/od/s0_station_daily.csv.gz", "rt", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["offday"] != "False":
            continue
        n_all += 1
        days.add(r["date"])
        cand = order.get(r["st_id"])
        if not cand:
            n_nostn += 1
            continue
        t = None
        for j, a in enumerate(cand):
            if (a, r["date"]) in daily:
                t = daily[(a, r["date"])]
                n_first += j == 0
                n_later += j > 0
                break
        if t is None:
            n_none += 1
            continue
        bins[math.floor(t)].append(int(r["rent"]))
        per[(r["st_id"], min(35, max(-5, 5 * math.floor(t / 5))))].append(int(r["rent"]))
log.append(f"weekday station-days {n_all:,} on {len(days)} weekdays; station without coordinates {n_nostn:,}; "
           f"nearest AWS {n_first:,}; a farther AWS (nearest had no valid day) {n_later:,}; no AWS {n_none:,}")

with open(ROOT / "data/station_tmax_bins.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["tmax_bin", "station_days", "mean_rent", "median_rent"])
    for b in sorted(bins):
        v = bins[b]
        wr.writerow([b, len(v), round(sum(v) / len(v), 2), S.median(v)])
tot = sum(len(v) for v in bins.values())
log.append(f"binned station-days {tot:,}; bins {min(bins)} to {max(bins)} C")
for lo, hi in [(-99, 0), (0, 10), (10, 20), (20, 25), (25, 30), (30, 33), (33, 99)]:
    v = [x for b in bins if lo <= b < hi for x in bins[b]]
    if v:
        log.append(f"  max {lo:>3} to {hi:<3} C: {len(v):>8,} station-days, mean rentals {sum(v) / len(v):.2f}")
with open(ROOT / "data/station_tmax_band.csv", "w", encoding="utf-8", newline="") as fh:
    wr = csv.writer(fh)
    wr.writerow(["st_id", "band", "days", "mean_rent"])
    kept = 0
    for (st, b), v in sorted(per.items()):
        if len(v) >= 5:
            wr.writerow([st, b, len(v), round(sum(v) / len(v), 2)])
            kept += 1
log.append(f"station x 5 C band rows with >= 5 weekdays: {kept:,} of {len(per):,}; stations {len({k[0] for k in per}):,}")
(ROOT / "data/19_station_tmax_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
print("\n".join(log))
