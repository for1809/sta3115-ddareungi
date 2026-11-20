"""Step 1i: residential index per administrative dong from Seoul living population (내국인, 행정동 단위).

Source: 서울 열린데이터광장 OpenAPI SPOP_LOCAL_RESD_DONG (행정동 단위 서울 생활인구, 내국인). The API serves only
recent dates, so this uses 10 ordinary weekdays (Tue/Wed) in June-July 2026; a dong's residential character changes
little from year to year.
Output: data/dong_living_pop.csv  adm_cd (8 digits), pop_night (mean of 02-04 h), pop_day (mean of 13-15 h),
        res_index = pop_night / pop_day (> 1: more people at night than by day, i.e. residential), n_dates
The API key is read from a file and never printed.
Run: python scripts/14_living_population.py <key file> data
"""
import csv
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

DATES = ["20260609", "20260610", "20260616", "20260617", "20260623",
         "20260624", "20260707", "20260708", "20260714", "20260715"]
NIGHT, DAY = {"02", "03", "04"}, {"13", "14", "15"}


def fetch(key, date):
    rows, start = [], 1
    while True:
        url = f"http://openapi.seoul.go.kr:8088/{key}/json/SPOP_LOCAL_RESD_DONG/{start}/{start + 999}/{date}"
        for attempt in range(4):
            try:
                body = json.load(urllib.request.urlopen(url, timeout=60))["SPOP_LOCAL_RESD_DONG"]
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"failed {date} from row {start}")
        rows += body["row"]
        if start + 999 >= int(body["list_total_count"]):
            return rows
        start += 1000
        time.sleep(0.3)


def main(key_file, out_dir):
    key = Path(key_file).read_text().strip()
    acc = defaultdict(lambda: {"night": [], "day": []})
    for date in DATES:
        rows = fetch(key, date)
        for r in rows:
            h, code, v = r["TMZON_PD_SE"], r["ADSTRD_CODE_SE"], float(r["TOT_LVPOP_CO"])
            if h in NIGHT:
                acc[code]["night"].append(v)
            elif h in DAY:
                acc[code]["day"].append(v)
        print(f"{date}: {len(rows)} rows", flush=True)
    out = []
    for code, v in sorted(acc.items()):
        n, d = sum(v["night"]) / len(v["night"]), sum(v["day"]) / len(v["day"])
        out.append({"adm_cd": code, "pop_night": round(n, 1), "pop_day": round(d, 1),
                    "res_index": round(n / d, 4) if d else "", "n_dates": len(v["night"]) // len(NIGHT)})
    with open(Path(out_dir) / "dong_living_pop.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    idx = sorted(o["res_index"] for o in out if o["res_index"] != "")
    print(f"dongs {len(out)}; res_index min {idx[0]}, median {idx[len(idx) // 2]}, max {idx[-1]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:3])
