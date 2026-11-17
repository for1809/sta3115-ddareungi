"""Step 2: build the small aggregate files the analysis and the Shiny app read (October 2025 weekdays).

Outputs (data/)
  stations.csv      one row per station: Y1 use_day, Y2 net_day, Y3 am_empty, explanatory variables, roles
  station_hour.csv  station x hour x daytype: departures, arrivals, net (per day)
  district_hour.csv gu x hour (weekdays): bikes parked, bikes being ridden
  monthly_age.csv   month x age band: trips, from the monthly usage files (2022-01 .. 2026-06)

Conventions
  - weekdays exclude 2025-10-03 and 2025-10-06..09 (public holidays); those count as weekend/holiday
  - departures are counted on 집계_기준=출발시간 rows, arrivals on 도착시간 rows (each trip once each way)
  - Y3 am_empty = share of weekday 07-09h hourly inventory snapshots with 0 bikes
  - roles use citywide thresholds: low use = bottom 20% of use_day, near = another station within 300 m,
    commute core = use at or above the median and >= 50% of departures in 07-09h or 17-19h,
    morning gap = am_empty >= 0.3
"""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

HOLIDAYS = {date(2025, 10, 3), date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8), date(2025, 10, 9)}
COMMUTE = {7, 8, 9, 17, 18, 19}
AGE = {"~10대": "10대"}


def daytype(d):
    return "weekday" if d.weekday() < 5 and d not in HOLIDAYS else "weekend"


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def enc_of(raw):
    try:
        raw.decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp949"


def od_counts(od_zip, id2no):
    dep = defaultdict(lambda: defaultdict(lambda: [0] * 24))
    arr = defaultdict(lambda: defaultdict(lambda: [0] * 24))
    minutes = defaultdict(lambda: [0] * 24)  # station -> trip minutes started per hour (weekdays)
    days = defaultdict(set)
    with zipfile.ZipFile(od_zip) as zf:
        for info in zf.infolist():
            if not info.filename.endswith(".csv"):
                continue
            with zf.open(info) as fh:
                head = fh.read(4096)
            with zf.open(info) as fh:
                r = csv.reader(io.TextIOWrapper(fh, encoding=enc_of(head), errors="replace", newline=""))
                ix = {h: i for i, h in enumerate(next(r))}
                for row in r:
                    d = row[ix["기준_날짜"]]
                    day = date(int(d[:4]), int(d[4:6]), int(d[6:8]))
                    k = daytype(day)
                    days[k].add(day)
                    h = int(row[ix["기준_시간대"]][:2])
                    n = int(row[ix["전체_건수"]])
                    if row[ix["집계_기준"]] == "출발시간":
                        s = id2no.get(row[ix["시작_대여소_ID"]])
                        if s:
                            dep[s][k][h] += n
                            if k == "weekday":
                                minutes[s][h] += int(row[ix["전체_이용_분"]] or 0)
                    else:
                        e = id2no.get(row[ix["종료_대여소_ID"]])
                        if e:
                            arr[e][k][h] += n
    return dep, arr, minutes, {k: len(v) for k, v in days.items()}


def inventory(inv_zip, month_suffix):
    parked = defaultdict(lambda: [0] * 24)
    am = defaultdict(lambda: [0, 0])
    days = set()
    with zipfile.ZipFile(inv_zip) as zf:
        member = next(i for i in zf.infolist() if i.filename.endswith(month_suffix))
        with zf.open(member) as fh:
            r = csv.reader(io.TextIOWrapper(fh, encoding="cp949", errors="replace", newline=""))
            next(r)
            for d, num, _, h, cnt in r:
                day = date.fromisoformat(d)
                if daytype(day) != "weekday":
                    continue
                days.add(day)
                h, c = int(h), int(cnt)
                parked[num][h] += c
                if h in (7, 8, 9):
                    am[num][0] += c == 0
                    am[num][1] += 1
    return parked, am, len(days)


def monthly_age(folder, out_csv):
    trips = defaultdict(lambda: defaultdict(float))
    for p in sorted(Path(folder).glob("*.csv")):
        raw = p.read_bytes()[:400_000]
        with open(p, encoding=enc_of(raw[: raw.rfind(b"\n")]), errors="replace", newline="") as fh:
            r = csv.reader(fh)
            h = next(r)
            ix = {k: i for i, k in enumerate(h)}
            acol = next(k for k in h if k.startswith("연령대"))
            ncol = next(k for k in h if k.startswith("이용건수"))
            for row in r:
                if len(row) != len(h):
                    continue
                try:
                    n = float(row[ix[ncol]])
                except ValueError:
                    continue
                a = row[ix[acol]].strip()
                trips[row[0].replace("-", "")[:6]][AGE.get(a, a)] += n
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["month", "age", "trips"])
        for m in sorted(trips):
            for a, n in sorted(trips[m].items()):
                w.writerow([f"{m[:4]}-{m[4:]}", a, round(n)])
    print(f"monthly_age: {len(trips)} months")


def main(data_dir, od_zip, inv_zip, usage_folder):
    d = Path(data_dir)
    feats = read(d / "station_features.csv")
    id2no = {f["station_id"]: f["station_no"] for f in feats}
    dep, arr, minutes, nd = od_counts(od_zip, id2no)
    parked, am, ni = inventory(inv_zip, "data_2510.csv")
    print(f"days: {nd}; inventory weekdays: {ni}")

    rows = []
    for f in feats:
        s = f["station_no"]
        wd_dep = sum(dep[s]["weekday"])
        wd_arr = sum(arr[s]["weekday"])
        com = sum(dep[s]["weekday"][h] for h in COMMUTE)
        rows.append(dict(f, use_day=round((wd_dep + wd_arr) / nd["weekday"], 1),
                         dep_day=round(wd_dep / nd["weekday"], 1), arr_day=round(wd_arr / nd["weekday"], 1),
                         net_day=round((wd_arr - wd_dep) / nd["weekday"], 2),
                         commute_share=round(com / wd_dep, 3) if wd_dep else "",
                         am_empty=round(am[s][0] / am[s][1], 3) if am[s][1] else "",
                         parked_08=round(parked[s][8] / ni, 1) if s in parked else ""))
    uses = sorted(r["use_day"] for r in rows)
    q20, q50 = uses[int(len(uses) * 0.2)], uses[int(len(uses) * 0.5)]
    for r in rows:
        low_near = r["use_day"] <= q20 and int(r["nearest_station_m"]) <= 300
        gap = r["am_empty"] != "" and r["am_empty"] >= 0.3
        core = r["use_day"] >= q50 and r["commute_share"] != "" and r["commute_share"] >= 0.5
        r["role"] = ("supply_gap_suspect" if low_near and gap else "consolidate" if low_near
                     else "morning_gap" if gap else "commute_core" if core else "other")
    with open(d / "stations.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"stations.csv: {len(rows):,} rows; low-use threshold {q20} trips/day, median {q50}")
    roles = defaultdict(int)
    for r in rows:
        roles[r["role"]] += 1
    print("roles:", dict(roles))

    with open(d / "station_hour.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["station_no", "daytype", "hour", "dep", "arr", "net"])
        for f in feats:
            s = f["station_no"]
            for k in ("weekday", "weekend"):
                for h in range(24):
                    a, b = dep[s][k][h] / nd[k], arr[s][k][h] / nd[k]
                    w.writerow([s, k, h, round(a, 2), round(b, 2), round(b - a, 2)])

    gu_of = {f["station_no"]: f["gu"] for f in feats}
    park_g = defaultdict(lambda: [0.0] * 24)
    ride_g = defaultdict(lambda: [0.0] * 24)
    for s, v in parked.items():
        g = gu_of.get(s, "")
        for h in range(24):
            park_g[g][h] += v[h] / ni
    for s, v in minutes.items():
        g = gu_of.get(s, "")
        for h in range(24):
            ride_g[g][h] += v[h] / 60 / nd["weekday"]
    with open(d / "district_hour.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gu", "hour", "parked", "riding"])
        for g in sorted(set(park_g) | set(ride_g)):
            for h in range(24):
                w.writerow([g or "(미상)", h, round(park_g[g][h]), round(ride_g[g][h])])
    print("district_hour.csv written")
    monthly_age(usage_folder, d / "monthly_age.csv")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:5])
