"""Step 1c: clean the geocoded university list (every row was checked by eye, see notes below).

- online schools (사이버대학, 방송통신대학) are dropped: few students come to campus
- duplicates in the 2013 source list (가톨릭대학교, 서울과학기술대학교) are kept once
- 그리스도대학교 is now 강서대학교 (formerly KC대학교); its point comes from a lookup by the current name
- 적십자간호대학 merged into 중앙대학교 in 2011 and is dropped
- 국제예술대학 matched only to a neighbourhood centre, 한국폴리텍 서울강서캠퍼스 and 한영신학대학교 were not found:
  these three are left out and listed in the log
"""
import csv
import sys
from pathlib import Path

ONLINE = {"사이버대학(대학)", "방송통신대학"}
MANUAL = {"그리스도대학교": ("37.5483053", "126.8545934", "강서대학교 (현재 이름으로 검색)")}
DROP = {"적십자간호대학": "2011년 중앙대학교에 통합", "국제예술대학": "동 단위로만 찾아져 위치가 부정확"}


def main(src, dst):
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    out, seen, left_out = [], set(), []
    for r in rows:
        name = r["name"]
        if r["category"] in ONLINE:
            left_out.append((name, "원격 대학"))
            continue
        if name in DROP:
            left_out.append((name, DROP[name]))
            continue
        if name in MANUAL:
            r["lat"], r["lon"], r["osm_name"] = MANUAL[name]
            r["geocode"] = "manual_current_name"
        if not r["lat"]:
            left_out.append((name, "좌표를 찾지 못함"))
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "category": r["category"], "gu": r["gu"], "lat": r["lat"], "lon": r["lon"],
                    "geocode": r["geocode"]})
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"kept {len(out)} campuses")
    for n, why in left_out:
        print(f"   left out: {n} ({why})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:3])
