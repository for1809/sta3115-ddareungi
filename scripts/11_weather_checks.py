"""Step 2c: two weather checks for 2025 weekdays.

  python scripts/11_weather_checks.py inv data raw/inv_1h
      -> data/stations_wet.csv: per bike station, morning (07-09 h) shortage on wet mornings vs dry mornings,
         and on dry mornings after a wet day vs after a dry day (does yesterday's rain carry over?)
  python scripts/11_weather_checks.py od data raw/od_5min
      -> data/daily_aws_rentals.csv: rentals per weekday x AWS zone (bike stations grouped by nearest AWS station),
         all hours, 07-09 h and 17-19 h, to relate daily use to that zone's weather
Weather comes from data/weather_daily.csv; the station-to-AWS match is the aws_id column of data/stations_dry.csv.
wet morning = rain_am > 0 (06-10 h); dry morning = rain_am == 0; missing rain = neither (dropped).
wet day = rain_day >= 1 mm; the "previous day" is the previous calendar day.
"""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HOLIDAYS_2025 = {
    date(2025, 1, 1), date(2025, 1, 27), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30),
    date(2025, 3, 3), date(2025, 5, 5), date(2025, 5, 6), date(2025, 6, 3), date(2025, 6, 6),
    date(2025, 8, 15), date(2025, 10, 3), date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
    date(2025, 10, 9), date(2025, 12, 25),
}
EN = {"stdr_de": "기준_날짜", "dvcd": "집계_기준", "tmzon": "기준_시간대", "start_statn_id": "시작_대여소_ID",
      "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수", "trip_time": "전체_이용_분"}


def weekday(d):
    return d.weekday() < 5 and d not in HOLIDAYS_2025


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


def load(d):
    aws_of = {r["station_no"]: r["aws_id"] for r in read(d / "stations_dry.csv")}
    wx = {}
    for r in read(d / "weather_daily.csv"):
        f = lambda k: float(r[k]) if r[k] != "" else None
        wx[(r["aws_id"], date.fromisoformat(r["date"]))] = (f("rain_am"), f("rain_day"))
    return aws_of, wx


def inv(data_dir, inv_dir):
    d = Path(data_dir)
    aws_of, wx = load(d)
    c = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # station -> group -> [empty, total]
    for z in sorted(Path(inv_dir).glob("2025Q?.zip")):
        for r in members(z):
            next(r)
            for row in r:
                if len(row) < 5:
                    continue
                day = date.fromisoformat(row[0][:10])
                h = int(row[3])
                if day.year != 2025 or not weekday(day) or h not in (7, 8, 9):
                    continue
                num = row[1].strip()
                st = f"{int(num):05d}" if num.isdigit() else num
                a = aws_of.get(st)
                if not a or (a, day) not in wx:
                    continue
                ram = wx[(a, day)][0]
                if ram is None:
                    continue
                groups = ["wet" if ram > 0 else "dry"]
                prev = wx.get((a, day - timedelta(days=1)), (None, None))[1]
                if ram == 0 and prev is not None:
                    groups.append("dry_after_wet" if prev >= 1 else "dry_after_dry")
                for g in groups:
                    c[st][g][0] += int(row[4]) == 0
                    c[st][g][1] += 1
        print(f"inventory {z.name}: done", flush=True)
    out = []
    for st in sorted(aws_of):
        row = {"station_no": st}
        for g in ("wet", "dry", "dry_after_wet", "dry_after_dry"):
            e, t = c[st][g]
            row[f"am_empty_{g}"] = round(e / t, 4) if t else ""
            row[f"n_{g}"] = t
        out.append(row)
    with open(d / "stations_wet.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"stations_wet.csv: {len(out)} stations; median wet snapshots "
          f"{sorted(o['n_wet'] for o in out)[len(out) // 2]}")


def od(data_dir, od_dir):
    d = Path(data_dir)
    aws_of, _ = load(d)
    id2no = {f["station_id"]: f["station_no"] for f in read(d / "station_features.csv")}
    n = defaultdict(lambda: [0, 0, 0])        # (date, aws) -> [all, 07-09, 17-19] rentals
    for z in sorted(Path(od_dir).glob("2025??.zip")):
        for r in members(z):
            ix = {EN.get(h, h): i for i, h in enumerate(next(r))}
            for row in r:
                if row[ix["집계_기준"]] != "출발시간":
                    continue
                s = row[ix["기준_날짜"]]
                day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                if day.year != 2025 or not weekday(day):
                    continue
                st = id2no.get(row[ix["시작_대여소_ID"]])
                a = aws_of.get(st) if st else None
                if not a:
                    continue
                h, k = int(row[ix["기준_시간대"]][:2]), int(row[ix["전체_건수"]])
                v = n[(day, a)]
                v[0] += k
                if h in (7, 8, 9):
                    v[1] += k
                if h in (17, 18, 19):
                    v[2] += k
        print(f"OD {z.name}: done", flush=True)
    with open(d / "daily_aws_rentals.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "aws_id", "rentals", "rentals_am", "rentals_pm"])
        for (day, a), v in sorted(n.items()):
            w.writerow([day.isoformat(), a, *v])
    print(f"daily_aws_rentals.csv: {len(n)} rows, {len({k[0] for k in n})} weekdays")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    mode, data_dir, src = sys.argv[1:4]
    (inv if mode == "inv" else od)(data_dir, src)
