"""Step 1: collect station-level explanatory variables.

Inputs
  - station list from the realtime bike API (stationId, number, name, docks, lat, lon)
  - Seoul OpenAPI key file (read, never printed)
Outputs (data/)
  - stations_base.csv   : one row per station with coordinates and docks
  - subway_stations.csv : subway station name, line, lat, lon (subwayStationMaster)
  - station_elevation.csv : elevation (m) per station from Open-Meteo (Copernicus DEM, 90 m)
"""
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ELEV_API = "https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
SEOUL_API = "http://openapi.seoul.go.kr:8088/{key}/json/{svc}/{a}/{b}/"


def get_json(url, tries=6):
    req = urllib.request.Request(url, headers={"User-Agent": "sta3115-class-project/0.1"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(15 * (attempt + 1))


def seoul_rows(key, svc, page=1000):
    rows, a = [], 1
    while True:
        try:
            body = next(iter(get_json(SEOUL_API.format(key=key, svc=svc, a=a, b=a + page - 1)).values()))
        except Exception as e:  # never echo the url, it contains the key
            raise SystemExit(f"{svc} {a}: {type(e).__name__}")
        rows.extend(body.get("row", []))
        if a + page - 1 >= int(body.get("list_total_count", 0)):
            return rows
        a += page


def main(bikelist_csv, key_file, out_dir):
    out = Path(out_dir)
    key = Path(key_file).read_text(encoding="utf-8").strip()

    stations = []
    with open(bikelist_csv, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["number"] and float(r["lat"]) > 0:
                stations.append({"station_id": r["stationId"], "station_no": r["number"],
                                 "name": r["stationName"].split(".", 1)[-1].strip(),
                                 "docks": int(r["rackTotCnt"] or 0),
                                 "lat": float(r["lat"]), "lon": float(r["lon"])})
    with open(out / "stations_base.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(stations[0]))
        w.writeheader()
        w.writerows(stations)
    print(f"stations with coordinates: {len(stations):,}")

    subway = seoul_rows(key, "subwayStationMaster")
    with open(out / "subway_stations.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["subway_id", "name", "line", "lat", "lon"])
        for r in subway:
            w.writerow([r["BLDN_ID"], r["BLDN_NM"], r["ROUTE"], r["LAT"], r["LOT"]])
    print(f"subway stations: {len(subway):,}")

    elev = []
    for i in range(0, len(stations), 100):
        chunk = stations[i:i + 100]
        url = ELEV_API.format(lat=",".join(f"{s['lat']:.5f}" for s in chunk),
                              lon=",".join(f"{s['lon']:.5f}" for s in chunk))
        elev.extend(get_json(url)["elevation"])
        time.sleep(3)
    with open(out / "station_elevation.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["station_no", "elev_m"])
        for s, z in zip(stations, elev):
            w.writerow([s["station_no"], z])
    print(f"elevations: {len(elev):,} (min {min(elev)}, max {max(elev)})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])
