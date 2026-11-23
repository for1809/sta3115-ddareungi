"""Step 15: the team's 2x2 of stations, rebuilt from the hourly inventory, plus who refilled the bikes.

Team definition (idea doc "EDA : Where are all the DDareungyi at ?", Step 3), positive = bikes leave:
  morning net outflow  = bikes at 07 h - bikes at 09 h
  daily net outflow    = bikes at 06 h - bikes at 23 h
  G1 "permanent deficit"  morning > 0 and daily > 0
  G2 "self-recovering"    morning > 0 and daily <= 0
  G3                      morning <= 0 and daily > 0
  G4                      morning <= 0 and daily <= 0
Per station the two outflows are averaged over days that have all four snapshots (06, 07, 09, 23 h).

Inventory also moves when trucks rebalance, so the same days are matched with the trip records:
  trip outflow (morning) = rentals - returns in hours 07-08   (between the 07 h and 09 h snapshots)
  trip outflow (daily)   = rentals - returns in hours 06-22   (between the 06 h and 23 h snapshots)
  other moves (daily)    = trip outflow - inventory outflow   (> 0: bikes added by something other than riders,
                           mostly rebalancing trucks; < 0: bikes taken away)
This assumes the h-hour snapshot is taken at the start of hour h; the raw files do not say, so the split is
approximate.

Days: 2025 weekdays without public holidays (same list as 05/06/10). "dry" = the station's nearest KMA AWS
recorded under 1 mm for the whole day (the team's 1 mm rule; missing rain counts as wet), "all" = every weekday.

Inputs   data/station_features.csv, data/aws_stations.csv, data/weather_daily.csv,
         <od_dir>/2025MM.zip (trips), <inv_dir>/2025Q?.zip (hourly bikes per station)
Output   data/station_2x2.csv, data/15_inventory_2x2_log.txt
Run      python scripts/15_inventory_2x2.py data raw/od_5min raw/inv_1h
"""
import csv
import io
import math
import sys
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

HOLIDAYS_2025 = {
    date(2025, 1, 1), date(2025, 1, 27), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30),
    date(2025, 3, 3), date(2025, 5, 5), date(2025, 5, 6), date(2025, 6, 3), date(2025, 6, 6),
    date(2025, 8, 15), date(2025, 10, 3), date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
    date(2025, 10, 9), date(2025, 12, 25),
}
EN = {"stdr_de": "기준_날짜", "dvcd": "집계_기준", "tmzon": "기준_시간대", "start_statn_id": "시작_대여소_ID",
      "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수"}
SNAP = (6, 7, 9, 23)


def weekday(d):
    return d.weekday() < 5 and d not in HOLIDAYS_2025


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def enc_of(raw):
    try:
        raw.decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp949"


def members(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if not info.filename.lower().endswith(".csv"):
                continue
            with zf.open(info) as fh:
                head = fh.read(4096)
            with zf.open(info) as fh:
                yield csv.reader(io.TextIOWrapper(fh, encoding=enc_of(head[: head.rfind(b"\n")] or head),
                                                  errors="replace", newline=""))


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main(data_dir, od_dir, inv_dir):
    d = Path(data_dir)
    log = []
    feats = read(d / "station_features.csv")
    id2no = {f["station_id"]: f["station_no"] for f in feats}
    rain = {}
    for r in read(d / "weather_daily.csv"):
        rain[(r["aws_id"], date.fromisoformat(r["date"]))] = float(r["rain_day"]) if r["rain_day"] != "" else None
    have = {a for a, _ in rain}
    aws = [a for a in read(d / "aws_stations.csv") if a["aws_id"] in have]
    near = {}
    for s in feats:
        near[s["station_no"]] = min(aws, key=lambda a: km(float(s["lat"]), float(s["lon"]), float(a["lat"]), float(a["lon"])))["aws_id"]

    def dry(st, day):
        v = rain.get((near[st], day))
        return v is not None and v < 1

    # ---- hourly inventory: (station, day) -> {hour: bikes}
    snap = defaultdict(dict)
    rows = bad = 0
    for z in sorted(Path(inv_dir).glob("2025Q?.zip")):
        for r in members(z):
            next(r)
            for row in r:
                if len(row) < 5:
                    bad += 1
                    continue
                try:
                    day = date.fromisoformat(row[0][:10])
                    h, c = int(row[3]), int(row[4])
                except ValueError:
                    bad += 1
                    continue
                if day.year != 2025 or not weekday(day) or h not in SNAP:
                    continue
                num = row[1].strip()
                st = f"{int(num):05d}" if num.isdigit() else num
                if st not in near:
                    continue
                rows += 1
                snap[(st, day)][h] = c
        print(f"inventory {z.name}: done", flush=True)
    log.append(f"inventory rows used (weekdays, hours {SNAP}): {rows}; unreadable rows skipped: {bad}")

    # ---- trips: (station, day) -> [rentals 07-08, returns 07-08, rentals 06-22, returns 06-22]
    trips = defaultdict(lambda: [0, 0, 0, 0])
    for z in sorted(Path(od_dir).glob("2025??.zip")):
        for r in members(z):
            ix = {EN.get(h, h): i for i, h in enumerate(next(r))}
            for row in r:
                s = row[ix["기준_날짜"]]
                day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                if day.year != 2025 or not weekday(day):
                    continue
                h, n = int(row[ix["기준_시간대"]][:2]), int(row[ix["전체_건수"]])
                out = row[ix["집계_기준"]] == "출발시간"
                st = id2no.get(row[ix["시작_대여소_ID"]] if out else row[ix["종료_대여소_ID"]])
                if not st:
                    continue
                t = trips[(st, day)]
                if h in (7, 8):
                    t[0 if out else 1] += n
                if 6 <= h <= 22:
                    t[2 if out else 3] += n
        print(f"OD {z.name}: done", flush=True)

    # ---- per station means
    acc = defaultdict(lambda: {"dry": [0, 0.0, 0.0, 0.0, 0.0], "all": [0, 0.0, 0.0, 0.0, 0.0]})
    for (st, day), s in snap.items():
        if not all(h in s for h in SNAP):
            continue
        t = trips.get((st, day), [0, 0, 0, 0])
        vals = (s[7] - s[9], s[6] - s[23], t[0] - t[1], t[2] - t[3])
        for k in ("all", "dry") if dry(st, day) else ("all",):
            a = acc[st][k]
            a[0] += 1
            for j, v in enumerate(vals, 1):
                a[j] += v
    out = []
    for f in feats:
        st = f["station_no"]
        row = {"station_no": st}
        for k in ("dry", "all"):
            n, am_i, day_i, am_t, day_t = acc[st][k] if st in acc else (0, 0, 0, 0, 0)
            m = (lambda v: round(v / n, 3)) if n else (lambda v: "")
            row.update({f"days_{k}": n, f"am_out_inv_{k}": m(am_i), f"day_out_inv_{k}": m(day_i),
                        f"am_out_trip_{k}": m(am_t), f"day_out_trip_{k}": m(day_t),
                        f"other_in_day_{k}": m(day_t - day_i)})
        out.append(row)
    with open(d / "station_2x2.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    days = sorted(r["days_dry"] for r in out if r["days_dry"])
    log.append(f"stations written: {len(out)}; with dry days: {len(days)}; dry days per station median "
               f"{days[len(days) // 2]}, min {days[0]}, max {days[-1]}")
    (d / "15_inventory_2x2_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main(*sys.argv[1:4])
