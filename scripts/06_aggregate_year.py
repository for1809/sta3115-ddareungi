"""Step 2 (full year): rebuild the aggregate files from all of 2025 instead of one month.

Inputs: 12 monthly OD zips (5-minute station-to-station counts) and 4 quarterly hourly-inventory zips for 2025.
Outputs (data/)
  coverage_2025.csv  month: OD days, inventory days, stations seen, hours per inventory day (for checking gaps)
  station_month.csv  station x month (weekdays): use_day, net_day, am_empty, commute_share
  stations.csv       station (all 2025 weekdays): Y1 use_day, Y2 net_day, Y3 am_empty, features, role
  station_hour.csv   station x daytype x hour (all 2025): dep, arr, net per day
  district_hour.csv  gu x hour (2025 weekdays): bikes parked, bikes being ridden
Conventions are the same as 05_aggregate.py: weekdays exclude public holidays, departures from 출발시간 rows,
arrivals from 도착시간 rows, Y3 = share of weekday 07-09h snapshots with 0 bikes, citywide role thresholds.
"""
import csv
import io
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HOLIDAYS_2025 = {
    date(2025, 1, 1), date(2025, 1, 27), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30),
    date(2025, 3, 3), date(2025, 5, 5), date(2025, 5, 6), date(2025, 6, 3), date(2025, 6, 6),
    date(2025, 8, 15), date(2025, 10, 3), date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
    date(2025, 10, 9), date(2025, 12, 25),
}
COMMUTE = {7, 8, 9, 17, 18, 19}
EN = {"stdr_de": "기준_날짜", "dvcd": "집계_기준", "tmzon": "기준_시간대", "start_statn_id": "시작_대여소_ID",
      "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수", "trip_time": "전체_이용_분"}


def daytype(d):
    return "weekday" if d.weekday() < 5 and d not in HOLIDAYS_2025 else "weekend"


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
    feats = read(d / "station_features.csv")
    id2no = {f["station_id"]: f["station_no"] for f in feats}
    gu_of = {f["station_no"]: f["gu"] for f in feats}

    # ---- OD: per station, month and daytype
    dep = defaultdict(lambda: defaultdict(lambda: [0] * 24))   # (station, month, daytype) -> hours
    arr = defaultdict(lambda: defaultdict(lambda: [0] * 24))
    ride_min = defaultdict(lambda: [0] * 24)                   # station -> weekday trip minutes by start hour
    od_days = defaultdict(set)
    for z in sorted(Path(od_dir).glob("2025??.zip")):
        for r in members(z):
            ix = {EN.get(h, h): i for i, h in enumerate(next(r))}
            for row in r:
                s = row[ix["기준_날짜"]]
                day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                if day.year != 2025:
                    continue
                k, m = daytype(day), day.month
                od_days[m].add(day)
                h, n = int(row[ix["기준_시간대"]][:2]), int(row[ix["전체_건수"]])
                if row[ix["집계_기준"]] == "출발시간":
                    st = id2no.get(row[ix["시작_대여소_ID"]])
                    if st:
                        dep[st][(m, k)][h] += n
                        if k == "weekday":
                            ride_min[st][h] += int(row[ix["전체_이용_분"]] or 0)
                else:
                    st = id2no.get(row[ix["종료_대여소_ID"]])
                    if st:
                        arr[st][(m, k)][h] += n
        print(f"OD {z.name}: done", flush=True)

    # ---- inventory: weekday snapshots
    am = defaultdict(lambda: [0, 0])          # (station, month) -> [empty, total] at 07-09h
    parked = defaultdict(lambda: [0] * 24)    # station -> weekday parked sum by hour
    inv_days = defaultdict(set)
    inv_hours = defaultdict(Counter)          # month -> Counter(date -> distinct hours)
    inv_station = defaultdict(set)
    for z in sorted(Path(inv_dir).glob("2025Q?.zip")):
        for r in members(z):
            next(r)
            seen_hours = defaultdict(set)
            for row in r:
                if len(row) < 5:
                    continue
                day = date.fromisoformat(row[0][:10])
                if day.year != 2025:
                    continue
                num = row[1].strip()
                num = f"{int(num):05d}" if num.isdigit() else num
                h, c = int(row[3]), int(row[4])
                m = day.month
                inv_days[m].add(day)
                inv_station[m].add(num)
                seen_hours[day].add(h)
                if daytype(day) != "weekday":
                    continue
                parked[num][h] += c
                if h in (7, 8, 9):
                    am[(num, m)][0] += c == 0
                    am[(num, m)][1] += 1
            for day, hs in seen_hours.items():
                inv_hours[day.month][day] = len(hs)
        print(f"inventory {z.name}: done", flush=True)

    # ---- coverage report
    with open(d / "coverage_2025.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["month", "od_days", "od_weekdays", "inv_days", "inv_weekdays", "inv_stations",
                    "inv_days_with_24_hours"])
        for m in range(1, 13):
            w.writerow([m, len(od_days[m]), sum(1 for x in od_days[m] if daytype(x) == "weekday"),
                        len(inv_days[m]), sum(1 for x in inv_days[m] if daytype(x) == "weekday"),
                        len(inv_station[m]), sum(1 for v in inv_hours[m].values() if v == 24)])
    print(open(d / "coverage_2025.csv", encoding="utf-8").read())

    wd_days = {m: sum(1 for x in od_days[m] if daytype(x) == "weekday") for m in range(1, 13)}
    we_days = {m: sum(1 for x in od_days[m] if daytype(x) == "weekend") for m in range(1, 13)}
    n_wd, n_we = sum(wd_days.values()), sum(we_days.values())
    inv_wd = sum(1 for m in inv_days for x in inv_days[m] if daytype(x) == "weekday")

    # ---- station x month
    with open(d / "station_month.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["station_no", "month", "use_day", "net_day", "am_empty", "commute_share"])
        for f in feats:
            s = f["station_no"]
            for m in range(1, 13):
                if not wd_days[m]:
                    continue
                a, b = dep[s][(m, "weekday")], arr[s][(m, "weekday")]
                e, t = am[(s, m)]
                w.writerow([s, m, round((sum(a) + sum(b)) / wd_days[m], 2), round((sum(b) - sum(a)) / wd_days[m], 2),
                            round(e / t, 3) if t else "", round(sum(a[h] for h in COMMUTE) / sum(a), 3) if sum(a) else ""])

    # ---- station (whole year)
    rows = []
    for f in feats:
        s = f["station_no"]
        a = [sum(dep[s][(m, "weekday")][h] for m in range(1, 13)) for h in range(24)]
        b = [sum(arr[s][(m, "weekday")][h] for m in range(1, 13)) for h in range(24)]
        e = sum(am[(s, m)][0] for m in range(1, 13))
        t = sum(am[(s, m)][1] for m in range(1, 13))
        months_used = sum(1 for m in range(1, 13) if sum(dep[s][(m, "weekday")]) + sum(arr[s][(m, "weekday")]) > 0)
        rows.append(dict(f, use_day=round((sum(a) + sum(b)) / n_wd, 1), dep_day=round(sum(a) / n_wd, 1),
                         arr_day=round(sum(b) / n_wd, 1), net_day=round((sum(b) - sum(a)) / n_wd, 2),
                         commute_share=round(sum(a[h] for h in COMMUTE) / sum(a), 3) if sum(a) else "",
                         am_empty=round(e / t, 3) if t else "",
                         parked_08=round(parked[s][8] / inv_wd, 1) if s in parked else "",
                         months_active=months_used))
    uses = sorted(r["use_day"] for r in rows if r["months_active"] > 0)
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
    print(f"weekdays {n_wd}, weekend/holiday days {n_we}, inventory weekdays {inv_wd}")
    print(f"stations.csv: low-use threshold {q20}, median {q50}; roles {dict(Counter(r['role'] for r in rows))}")
    print(f"stations active all 12 months: {sum(1 for r in rows if r['months_active'] == 12)}, "
          f"never active: {sum(1 for r in rows if r['months_active'] == 0)}")

    # ---- station x hour (whole year)
    with open(d / "station_hour.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["station_no", "daytype", "hour", "dep", "arr", "net"])
        for f in feats:
            s = f["station_no"]
            for k, nd in (("weekday", n_wd), ("weekend", n_we)):
                for h in range(24):
                    a = sum(dep[s][(m, k)][h] for m in range(1, 13)) / nd
                    b = sum(arr[s][(m, k)][h] for m in range(1, 13)) / nd
                    w.writerow([s, k, h, round(a, 2), round(b, 2), round(b - a, 2)])

    # ---- district x hour (whole year, weekdays)
    park_g, ride_g = defaultdict(lambda: [0.0] * 24), defaultdict(lambda: [0.0] * 24)
    for s, v in parked.items():
        for h in range(24):
            park_g[gu_of.get(s, "(미상)")][h] += v[h] / inv_wd
    for s, v in ride_min.items():
        for h in range(24):
            ride_g[gu_of.get(s, "(미상)")][h] += v[h] / 60 / n_wd
    with open(d / "district_hour.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gu", "hour", "parked", "riding"])
        for g in sorted(set(park_g) | set(ride_g)):
            for h in range(24):
                w.writerow([g, h, round(park_g[g][h]), round(ride_g[g][h])])
    print("done")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])
