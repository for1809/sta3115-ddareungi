"""Step 2b: weather-aware commute aggregation for 2025 (dry weekdays, morning and evening, uphill trips).

Inputs
  data/station_features.csv   bike stations (station_id, station_no, lat, lon)
  data/station_terrain.csv    elev30_m per station (scripts/07_terrain.R)
  data/aws_stations.csv       KMA AWS stations with coordinates (aws_id, name, lat, lon)
  data/weather_daily.csv      daily commute weather per AWS station (scripts/09_weather_daily.py)
  <od_dir>/2025MM.zip, <inv_dir>/2025Q?.zip   same raw files as scripts/06_aggregate_year.py
Output
  data/stations_dry.csv       one row per bike station (see COLUMNS below)
  data/10_aggregate_dry_log.txt
Rules
  - weekdays exclude the 2025 public holidays (same list as 06)
  - each bike station takes the weather of its nearest AWS station that has data
  - a weekday is wet in the morning for a station if its AWS recorded any rain 06-10 h (rain_am > 0),
    wet in the evening if any rain 16-20 h; a day with missing rain data in that window counts as wet
    (dropped), so "dry" always means observed dry
  - am_* uses the 07, 08, 09 h inventory snapshots, pm_* the 17, 18, 19 h snapshots
  - use_commute_dry: rentals + returns in 07-09 h and 17-19 h per dry weekday (dry = dry morning and evening)
  - climb_in_m: mean of (elevation here - elevation at the origin) over all weekday trips that end here;
    drop_am_out_m: mean of (elevation here - elevation at the destination) over weekday trips leaving here 07-09 h
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
      "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수", "trip_time": "전체_이용_분"}
AM, PM = (7, 8, 9), (17, 18, 19)


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
    elev = {r["station_no"]: float(r["elev30_m"]) for r in read(d / "station_terrain.csv")}
    id2no = {f["station_id"]: f["station_no"] for f in feats}

    # weather: (aws, date) -> rain_am, rain_pm (None = missing)
    wx = {}
    for r in read(d / "weather_daily.csv"):
        f = lambda k: float(r[k]) if r[k] != "" else None
        wx[(r["aws_id"], date.fromisoformat(r["date"]))] = (f("rain_am"), f("rain_pm"), f("rain_day"))
    have = {a for a, _ in wx}
    aws = [a for a in read(d / "aws_stations.csv") if a["aws_id"] in have]
    near = {}
    for s in feats:
        dist, a = min(((km(float(s["lat"]), float(s["lon"]), float(a["lat"]), float(a["lon"])), a) for a in aws),
                      key=lambda t: t[0])
        near[s["station_no"]] = (a["aws_id"], round(dist * 1000))
    log.append(f"AWS stations with data: {len(aws)}; bike-station to AWS distance median "
               f"{sorted(v[1] for v in near.values())[len(near) // 2]} m, max {max(v[1] for v in near.values())} m")

    def dry(st, day, part):
        w = wx.get((near[st][0], day))
        if w is None:
            return False
        v = w[0] if part == "am" else w[1] if part == "pm" else w[2]
        return v is not None and (v == 0 if part in ("am", "pm") else v < 1)

    # ---- inventory snapshots
    inv = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # station -> key -> [empty, total]
    for z in sorted(Path(inv_dir).glob("2025Q?.zip")):
        for r in members(z):
            next(r)
            for row in r:
                if len(row) < 5:
                    continue
                day = date.fromisoformat(row[0][:10])
                if day.year != 2025 or not weekday(day):
                    continue
                num = row[1].strip()
                st = f"{int(num):05d}" if num.isdigit() else num
                if st not in near:
                    continue
                h, c = int(row[3]), int(row[4])
                part = "am" if h in AM else "pm" if h in PM else None
                if not part:
                    continue
                keys = [part + "_all"]
                if dry(st, day, part):
                    keys.append(part + "_dry")
                if dry(st, day, "day"):
                    keys.append(part + "_dryday")
                for k in keys:
                    inv[st][k][0] += c == 0
                    inv[st][k][1] += 1
        print(f"inventory {z.name}: done", flush=True)

    # ---- trips
    use = defaultdict(float)                     # station -> commute rentals + returns on dry weekdays
    climb = defaultdict(lambda: [0.0, 0])        # station -> [sum of elevation gain, trips] for trips ending here
    drop = defaultdict(lambda: [0.0, 0])         # station -> [sum of drop, trips] for 07-09 h trips leaving here
    dry_days = defaultdict(set)
    for z in sorted(Path(od_dir).glob("2025??.zip")):
        for r in members(z):
            ix = {EN.get(h, h): i for i, h in enumerate(next(r))}
            for row in r:
                s = row[ix["기준_날짜"]]
                day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                if day.year != 2025 or not weekday(day):
                    continue
                h, n = int(row[ix["기준_시간대"]][:2]), int(row[ix["전체_건수"]])
                a, b = id2no.get(row[ix["시작_대여소_ID"]]), id2no.get(row[ix["종료_대여소_ID"]])
                if row[ix["집계_기준"]] == "출발시간":
                    if a and b and a in elev and b in elev:
                        climb[b][0] += n * (elev[b] - elev[a])
                        climb[b][1] += n
                        if h in AM:
                            drop[a][0] += n * (elev[a] - elev[b])
                            drop[a][1] += n
                    st = a
                else:
                    st = b
                if st and st in near and (h in AM or h in PM) and dry(st, day, "am") and dry(st, day, "pm"):
                    use[st] += n
                    dry_days[st].add(day)
        print(f"OD {z.name}: done", flush=True)

    out = []
    for f in feats:
        st = f["station_no"]
        iv = inv[st]
        rate = lambda k: round(iv[k][0] / iv[k][1], 3) if iv[k][1] else ""
        nd = len(dry_days[st])
        out.append({"station_no": st, "aws_id": near[st][0], "aws_m": near[st][1],
                    "am_empty_all": rate("am_all"), "am_empty_dry": rate("am_dry"), "am_empty_dryday": rate("am_dryday"),
                    "pm_empty_all": rate("pm_all"), "pm_empty_dry": rate("pm_dry"), "pm_empty_dryday": rate("pm_dryday"),
                    "am_snapshots_dry": iv["am_dry"][1], "pm_snapshots_dry": iv["pm_dry"][1],
                    "dry_days_used": nd, "use_commute_dry": round(use[st] / nd, 1) if nd else "",
                    "climb_in_m": round(climb[st][0] / climb[st][1], 2) if climb[st][1] else "",
                    "trips_in": climb[st][1],
                    "drop_am_out_m": round(drop[st][0] / drop[st][1], 2) if drop[st][1] else "",
                    "trips_am_out": drop[st][1]})
    with open(d / "stations_dry.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    filled = lambda k: sum(1 for o in out if o[k] != "")
    log.append(f"stations: {len(out)}; with am_empty_dry {filled('am_empty_dry')}, pm_empty_dry {filled('pm_empty_dry')}, "
               f"climb_in_m {filled('climb_in_m')}, drop_am_out_m {filled('drop_am_out_m')}")
    snaps = sorted(o["am_snapshots_dry"] for o in out if o["am_snapshots_dry"])
    log.append(f"dry-morning snapshots per station: median {snaps[len(snaps) // 2]}, min {snaps[0]}")
    (d / "10_aggregate_dry_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])
