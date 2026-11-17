"""Step 1d: station-level explanatory variables.

For every bike station: elevation, distance (m) to the nearest subway station and its name,
distance to the nearest university campus and its name, distance to the nearest other bike station,
and the borough (gu) from the station info file. Output: data/station_features.csv
"""
import csv
import math
import sys
from pathlib import Path


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def nearest(lat, lon, points, skip=None):
    best = (float("inf"), None)
    for p in points:
        if p is skip:
            continue
        d = km(lat, lon, p["lat"], p["lon"])
        if d < best[0]:
            best = (d, p)
    return best


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main(data_dir, gu_csv):
    d = Path(data_dir)
    st = read(d / "stations_base.csv")
    for s in st:
        s["lat"], s["lon"] = float(s["lat"]), float(s["lon"])
    elev = {r["station_no"]: float(r["elev_m"]) for r in read(d / "station_elevation.csv")}
    subway = [{"name": r["name"], "line": r["line"], "lat": float(r["lat"]), "lon": float(r["lon"])}
              for r in read(d / "subway_stations.csv") if r["lat"]]
    univ = [{"name": r["name"], "lat": float(r["lat"]), "lon": float(r["lon"])} for r in read(d / "universities_clean.csv")]
    gu = {}
    with open(gu_csv, encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh):
            if r and r[0].strip().isdigit():
                gu[f"{int(r[0]):05d}"] = r[2].strip()

    out = []
    for s in st:
        ds, sub = nearest(s["lat"], s["lon"], subway)
        du, uni = nearest(s["lat"], s["lon"], univ)
        db, _ = nearest(s["lat"], s["lon"], st, skip=s)
        out.append({"station_no": s["station_no"], "station_id": s["station_id"], "name": s["name"],
                    "gu": gu.get(s["station_no"], ""), "lat": s["lat"], "lon": s["lon"], "docks": s["docks"],
                    "elev_m": elev.get(s["station_no"], ""),
                    "subway_m": round(ds * 1000), "subway_name": f"{sub['name']}({sub['line']})",
                    "univ_m": round(du * 1000), "univ_name": uni["name"],
                    "nearest_station_m": round(db * 1000)})
    # 13 stations opened after the 2026-06 station info file have no gu: take the gu of the nearest station that has one
    known = [o for o in out if o["gu"]]
    for o in out:
        o["gu_filled"] = 0
        if not o["gu"]:
            _, nb = nearest(o["lat"], o["lon"], known)
            o["gu"], o["gu_filled"] = nb["gu"], 1
    with open(d / "station_features.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    def med(k):
        v = sorted(o[k] for o in out if o[k] != "")
        return v[len(v) // 2]
    print(f"stations: {len(out):,}; with gu: {sum(1 for o in out if o['gu']):,}; with elevation: "
          f"{sum(1 for o in out if o['elev_m'] != ''):,}")
    print(f"median distance to subway {med('subway_m')} m, to university {med('univ_m')} m, "
          f"to nearest bike station {med('nearest_station_m')} m, median elevation {med('elev_m')} m")
    print(f"within 300 m of a subway station: {sum(1 for o in out if o['subway_m'] <= 300):,}; "
          f"within 500 m of a campus: {sum(1 for o in out if o['univ_m'] <= 500):,}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:3])
