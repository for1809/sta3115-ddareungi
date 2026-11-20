"""Step 2d: weekday trip counts per (origin station, destination station) for 2025.

Output: raw/derived/od_pairs_weekday_2025.csv  origin, dest, trips, trips_am (07-09 h start)
Kept out of git (size); any elevation source can then be turned into "climb" quickly in R.
Same conventions as 06/10: departures (출발시간 rows) only, weekdays without public holidays.
Run: python scripts/13_od_pairs.py data raw/od_5min raw/derived
"""
import csv
import io
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


def main(data_dir, od_dir, out_dir):
    with open(Path(data_dir) / "station_features.csv", encoding="utf-8", newline="") as fh:
        id2no = {r["station_id"]: r["station_no"] for r in csv.DictReader(fh)}
    pairs = defaultdict(lambda: [0, 0])
    for z in sorted(Path(od_dir).glob("2025??.zip")):
        for r in members(z):
            ix = {EN.get(h, h): i for i, h in enumerate(next(r))}
            for row in r:
                if row[ix["집계_기준"]] != "출발시간":
                    continue
                s = row[ix["기준_날짜"]]
                day = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                if day.year != 2025 or day.weekday() >= 5 or day in HOLIDAYS_2025:
                    continue
                a, b = id2no.get(row[ix["시작_대여소_ID"]]), id2no.get(row[ix["종료_대여소_ID"]])
                if not a or not b:
                    continue
                n = int(row[ix["전체_건수"]])
                p = pairs[(a, b)]
                p[0] += n
                if int(row[ix["기준_시간대"]][:2]) in (7, 8, 9):
                    p[1] += n
        print(f"OD {z.name}: done", flush=True)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(out_dir) / "od_pairs_weekday_2025.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["origin", "dest", "trips", "trips_am"])
        for (a, b), (t, am) in pairs.items():
            w.writerow([a, b, t, am])
    same = sum(v[0] for (a, b), v in pairs.items() if a == b)
    total = sum(v[0] for v in pairs.values())
    print(f"pairs {len(pairs):,}; trips {total:,}; same-station round trips {same:,} ({same / total:.1%})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])
