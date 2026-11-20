"""Step 1g: daily commute-time weather per Seoul AWS station, from the hourly KMA files.

Input : raw/weather/aws_2025MM.csv (KMA 방재기상관측 hourly; 지점, 지점명, 일시, 기온, 풍속, 강수량),
        written by scripts/08_fetch_kma_aws.mjs
Output: data/weather_daily.csv   aws_id, date, rain_day, rain_am, rain_pm, temp_am, wind_am, n_hours, n_missing_rain
        data/09_weather_log.txt  full check of every station-month (rows, missing values, ranges)
KMA hourly precipitation stamped HH:00 is the amount that fell in the hour before, so
  rain_am = 07:00..10:00 stamps (06-10 h), rain_pm = 17:00..20:00 stamps (16-20 h),
  rain_day = 01:00..24:00 (the 00:00 stamp of the next day closes the day; here we use 01..23 plus next 00).
temp_am, wind_am = means over the 07:00..09:00 stamps. Blank cells are missing values, not zeros.
"""
import csv
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


def num(s):
    s = s.strip()
    return float(s) if s not in ("", "-") else None


def main(raw_dir, out_dir):
    rows = defaultdict(dict)                      # (aws, date) -> hour -> (temp, wind, rain)
    names = {}
    log = []
    for p in sorted(Path(raw_dir).glob("aws_2025??.csv")):
        n, miss = 0, [0, 0, 0]
        lo, hi = [1e9] * 3, [-1e9] * 3
        per_stn = defaultdict(int)
        with open(p, encoding="utf-8", newline="") as fh:
            r = csv.reader(fh)
            head = next(r)
            assert head[:3] == ["지점", "지점명", "일시"], head
            for row in r:
                if not row:
                    continue
                n += 1
                stn, nm, ts = row[0], row[1], datetime.strptime(row[2], "%Y-%m-%d %H:%M")
                names[stn] = nm
                per_stn[stn] += 1
                vals = [num(v) for v in row[3:6]]
                for i, v in enumerate(vals):
                    if v is None:
                        miss[i] += 1
                    else:
                        lo[i], hi[i] = min(lo[i], v), max(hi[i], v)
                # the 00:00 stamp closes the previous day for precipitation
                d = (ts - timedelta(hours=1)).date() if ts.hour == 0 else ts.date()
                h = 24 if ts.hour == 0 else ts.hour
                rows[(stn, d)][h] = vals
        log.append(f"{p.name}: {n} rows, {len(per_stn)} stations, rows per station {min(per_stn.values())}-{max(per_stn.values())}; "
                   f"missing temp/wind/rain {miss}; temp {lo[0]}..{hi[0]}, wind {lo[1]}..{hi[1]}, rain {lo[2]}..{hi[2]}")

    out = []
    for (stn, d), hrs in sorted(rows.items()):
        if d.year != 2025:
            continue

        def total(hours):
            # an hour with no row or a blank cell makes the window unknown, never zero
            if any(h not in hrs or hrs[h][2] is None for h in hours):
                return ""
            return round(sum(hrs[h][2] for h in hours), 1)

        def mean(hours, i):
            v = [hrs[h][i] for h in hours if h in hrs and hrs[h][i] is not None]
            return round(sum(v) / len(v), 1) if v else ""

        out.append({"aws_id": stn, "date": d.isoformat(), "rain_day": total(range(1, 25)),
                    "rain_am": total(range(7, 11)), "rain_pm": total(range(17, 21)),
                    "temp_am": mean(range(7, 10), 0), "wind_am": mean(range(7, 10), 1),
                    "n_hours": len(hrs), "n_missing_rain": sum(1 for h in range(1, 25) if h not in hrs or hrs[h][2] is None)})
    Path(out_dir).mkdir(exist_ok=True)
    with open(Path(out_dir) / "weather_daily.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    days = defaultdict(int)
    for o in out:
        days[o["aws_id"]] += 1
    log.append(f"stations: {len(days)} ({', '.join(f'{k} {names[k]}' for k in sorted(days))})")
    log.append(f"station-days: {len(out)}; days per station {min(days.values())}-{max(days.values())}")
    log.append(f"station-days with any rain hour missing: {sum(1 for o in out if o['n_missing_rain'])}")
    wet = [o for o in out if o["rain_day"] != "" and o["rain_day"] >= 1]
    log.append(f"station-days with rain_day >= 1 mm: {len(wet)} ({len(wet) / len(out):.1%})")
    am = [o for o in out if o["rain_am"] != "" and o["rain_am"] > 0]
    log.append(f"station-days with any rain 06-10 h: {len(am)} ({len(am) / len(out):.1%})")
    Path(out_dir, "09_weather_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:3])
