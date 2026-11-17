"""Step 1b: university locations.

The Seoul college list (SebcCollegeInfoKor, 64 schools) has names and addresses but no coordinates,
so each school is looked up by name in OpenStreetMap (Nominatim, 1 request per second, Seoul bounding box).
Schools that are not found by name are retried with their address. Output: data/universities.csv
with a `geocode` column saying how each point was found, so misses can be checked by hand.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SEOUL_API = "http://openapi.seoul.go.kr:8088/{key}/json/SebcCollegeInfoKor/1/200/"
NOMINATIM = "https://nominatim.openstreetmap.org/search?"
SEOUL_BOX = "126.76,37.70,127.19,37.41"  # lon_min, lat_max, lon_max, lat_min
UA = {"User-Agent": "sta3115-class-project/0.1"}


def nominatim(q):
    params = {"q": q, "format": "jsonv2", "countrycodes": "kr", "viewbox": SEOUL_BOX, "bounded": 1, "limit": 1}
    req = urllib.request.Request(NOMINATIM + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        hits = json.loads(r.read().decode("utf-8"))
    time.sleep(1.1)
    return hits[0] if hits else None


def main(key_file, out_csv):
    key = Path(key_file).read_text(encoding="utf-8").strip()
    with urllib.request.urlopen(SEOUL_API.format(key=key), timeout=60) as r:
        rows = json.loads(r.read().decode("utf-8"))["SebcCollegeInfoKor"]["row"]
    out = []
    for r in rows:
        name = r["NAME_KOR"].strip()
        hit, how = nominatim(name), "name"
        if not hit and r["ADD_KOR"].strip():
            addr = r["ADD_KOR"].split("(")[0].strip()
            hit, how = nominatim(addr), "address"
        out.append({"name": name, "category": r["CATE1_NAME"], "branch": r["BRANCH"], "gu": r["H_KOR_GU"],
                    "address": r["ADD_KOR"].strip(),
                    "lat": hit["lat"] if hit else "", "lon": hit["lon"] if hit else "",
                    "osm_name": hit["display_name"][:80] if hit else "", "geocode": how if hit else "not_found"})
        print(f"{out[-1]['geocode']:9s} {name} -> {out[-1]['osm_name']}")
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    found = sum(1 for o in out if o["lat"])
    print(f"\nfound {found}/{len(out)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:3])
