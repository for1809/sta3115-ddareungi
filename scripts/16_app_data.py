"""Step 16: small data files for the Shiny app (app/), cut from the same tables and code as the final talk deck.

Run from the project root:  python -I scripts/16_app_data.py > data/16_app_data_log.txt
Writes
  app/data/stations.csv      one row per station: the 2,843 trip-data stations (2024-2025 clear weekdays) and every
                             station with a 2025 dry-weekday empty share; net outflow always in bikes, never per dock
  app/data/station_hour.csv  hourly rentals, returns and net outflow per station, 2024-2025 clear weekdays
  app/data/stock_hour.csv    mean hourly bikes on hand and empty share by elevation band x subway-distance quarter (2025 dry weekdays)
  app/data/curves.csv        the deck's LOESS curves (daily net outflow on elevation; empty share on bikes at 8 am)
Same definitions as slides/final_deck_nodocks.py (sign-based groups G1-G4, deck LOESS) and slides/final_deck_new.py
(empty share, subway quarters, stock, logistic model inputs). The numbers the deck shows are checked at the end.
"""
import csv, gzip, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "slides"))
from final_deck_nodocks import sign_type, lowess  # noqa: E402  the deck's own group rule and LOESS

sys.stdout.reconfigure(encoding="utf-8")
OD = R / "data/od_2024_2025/od"
OUT = R / "app/data"
OUT.mkdir(parents=True, exist_ok=True)
N = json.load(open(R / "data/story_numbers.json", encoding="utf-8"))
CUT = N["subway_cuts"]
GU = {"강남": "Gangnam", "강동": "Gangdong", "강북": "Gangbuk", "강서": "Gangseo", "관악": "Gwanak", "광진": "Gwangjin",
      "구로": "Guro", "금천": "Geumcheon", "노원": "Nowon", "도봉": "Dobong", "동대문": "Dongdaemun", "동작": "Dongjak",
      "마포": "Mapo", "서대문": "Seodaemun", "서초": "Seocho", "성동": "Seongdong", "성북": "Seongbuk", "송파": "Songpa",
      "양천": "Yangcheon", "영등포": "Yeongdeungpo", "용산": "Yongsan", "은평": "Eunpyeong", "종로": "Jongno", "중": "Jung",
      "중랑": "Jungnang"}
gu_en = lambda g: GU.get(g[:-1] if g.endswith("구") else g, "")
fnum = lambda v: float(v) if v not in ("", None) else None
band = lambda e: None if e is None else ("hill" if e >= 40 else ("flat" if e < 20 else "mid"))
q_of = lambda d: None if d is None else sum(d >= c for c in CUT)

# ---- station master (empty share, bikes at 8 am, bare-earth elevation, subway distance): 2025 hourly stock
master = {}
for r in csv.DictReader(open(R / "data/station_master.csv", encoding="utf-8-sig")):
    master[r["station_id"]] = r

# ---- trip summary, 2024-2025 clear weekdays (the deck's 2,843 stations are those with enough days)
summ = {r["st_id"]: r for r in csv.DictReader(open(OD / "s0_station_summary.csv", encoding="utf-8-sig"))}

# ---- morning net outflow per station from the daily table, as slides/final_deck_new.py does
amd = defaultdict(lambda: [0.0, 0])
with gzip.open(OD / "s0_station_daily.csv.gz", "rt", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["clear_weekday"] == "True":
            a = amd[r["st_id"]]; a[0] += float(r["am_net"]); a[1] += 1

ids = sorted(set(summ) | {k for k, r in master.items() if r["am_empty_dry"]}, key=lambda s: int(s.split("-")[1]))
rows = []
for sid in ids:
    s, m = summ.get(sid), master.get(sid)
    enough = bool(s) and s["enough_days"] == "True"
    a = amd.get(sid)
    sub_m = fnum(m["subway_m"]) if m else None
    elev_b = fnum(m["elev_bare_m"]) if m else None
    am, day = (fnum(s["cw_am_net"]), fnum(s["cw_net"])) if s else (None, None)
    rows.append(dict(
        st_id=sid, station_no=(m["station_no"] if m else ""),
        name=(s["name"] if s else m["name"]).strip(),
        gu=gu_en((s["gu"] if s else m["gu"]) or ""),
        lat=round(float((s or m)["lat"]), 6), lon=round(float((s or m)["lon"]), 6),
        trip=int(enough),                                     # 1 = one of the deck's 2,843 trip-data stations
        elev=fnum(s["elevation_m"]) if s else None,           # deck elevation (trip summary), used with trip data
        relief=fnum(s["relief_300m"]) if s else None,
        sub_dist=fnum(s["subway_dist_m"]) if s else None,
        subway=(s["subway_nearest"] if s else (m["subway_name"] if m else "")),
        rides=round(float(s["cw_rent"]) + float(s["cw_ret"]), 1) if s and s["cw_rent"] else None,
        rent=round(float(s["cw_rent"]), 2) if s and s["cw_rent"] else None,
        ret=round(float(s["cw_ret"]), 2) if s and s["cw_ret"] else None,
        day_net=round(day, 3) if day is not None else None,   # bikes a day (rentals minus returns)
        am_net=round(am, 3) if am is not None else None,      # bikes per morning, 7-9 am
        pm_net=round(fnum(s["cw_pm_net"]), 3) if s and s["cw_pm_net"] else None,  # bikes, 5-8 pm
        group=sign_type(am, day) if enough else "",
        am_net_d=round(a[0] / a[1], 3) if a and a[1] else None,  # morning net outflow from the daily table (slides d_measures, d_subway)
        empty=fnum(m["am_empty_dry"]) if m and m["am_empty_dry"] else None,  # share of 7/8/9 am readings with no bike, 2025 dry weekdays
        bikes8=fnum(m["parked_08_2025"]) if m and m["parked_08_2025"] else None,
        elev_bare=elev_b, subway_m=sub_m,
        band=band(elev_b) or "", subq=q_of(sub_m) if sub_m is not None else ""))

cols = list(rows[0])
with open(OUT / "stations.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, cols); w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})

# ---- hourly profile per station
keep = {r["st_id"] for r in rows}
hp = []
with gzip.open(OD / "s0_station_hour_profile.csv.gz", "rt", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["daytype"] == "clear_weekday" and r["st_id"] in keep:
            hp.append((r["st_id"], int(r["hour"]), round(float(r["rent"]), 3), round(float(r["ret"]), 3), round(float(r["net"]), 3)))
with open(OUT / "station_hour.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["st_id", "hour", "rent", "ret", "net"]); w.writerows(hp)

# ---- stock by band x quarter x hour (story_numbers.json, as the deck)
with open(OUT / "stock_hour.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["band", "q", "hour", "n", "mean", "empty"])
    for r in N["stock"]:
        w.writerow([r["band"], r["q"], r["hour"], r["n"], r["mean"], r["empty"]])

# ---- the deck's LOESS curves
T = [r for r in rows if r["trip"]]
xs = [r["elev"] for r in T]; ys = [r["day_net"] for r in T]
grid = list(range(0, 101, 2))
fit = lowess(xs, ys, grid)
pts = [(r["bikes8"], r["empty"]) for r in rows if r["bikes8"] is not None and r["empty"] is not None and r["elev_bare"] is not None]
g8 = np.linspace(0.5, 30, 60)
fit8 = np.clip(lowess([p[0] for p in pts], [p[1] for p in pts], g8, span=.3), 0, 1)
with open(OUT / "curves.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["curve", "x", "y"])
    for g, f in zip(grid, fit):
        if g >= min(xs) + 4:
            w.writerow(["elev_day_net", g, round(float(f), 3)])
    for g, f in zip(g8, fit8):
        w.writerow(["bikes8_empty", round(float(g), 3), round(float(f), 4)])
    for k, c in enumerate(CUT):                                # subway-distance quarter cuts (m)
        w.writerow(["subway_cut", k + 1, c])

# ---------------------------------------------------------------- checks against the deck
mean = lambda v: sum(v) / len(v)
print(f"stations written {len(rows):,}; trip-data stations {len(T):,}; with empty share {sum(r['empty'] is not None for r in rows):,}")
print(f"hourly rows {len(hp):,}; stock rows {len(N['stock'])}")
# slide d_measures
allst = [(r["am_net_d"], r["empty"]) for r in rows if r["empty"] is not None and r["am_net_d"] is not None]
lose = [p for p in allst if p[0] > 0]; out = [p for p in lose if p[1] >= .2]
print(f"d_measures: {len(allst):,} stations; lose bikes {len(lose):,} ({len(lose) / len(allst):.0%}); of those run out {len(out):,} ({len(out) / len(lose):.0%})")
# slide elev
for lo, hi in ((0, 20), (20, 40), (40, 1e9)):
    v = [r["day_net"] for r in T if lo <= r["elev"] < hi]
    print(f"elev [{lo},{hi}): n {len(v)}, mean {mean(v):+.1f} bikes a day, losing {sum(x > 0 for x in v) / len(v):.0%}")
# slide d_subway
sub = [r for r in rows if r["subway_m"] is not None and r["elev_bare"] is not None and r["empty"] is not None]
for q in range(4):
    g = [r for r in sub if r["subq"] == q]
    print(f"subway q{q}: n {len(g)}, am net {mean([r['am_net_d'] for r in g if r['am_net_d'] is not None]):+.1f}, empty {mean([r['empty'] for r in g]):.1%}")
# groups
cnt = defaultdict(list)
for r in T:
    cnt[r["group"]].append(r)
for t in ("G1", "G2", "G3", "G4"):
    g = cnt[t]
    print(f"{t}: {len(g):,}; 5-8 pm net gain {-mean([r['pm_net'] for r in g]):+.1f}; median elevation {np.median([r['elev'] for r in g]):.0f} m")
# stock, far from the subway
st = {(r["band"], r["q"], r["hour"]): r for r in N["stock"]}
def stock_of(b, q, h, k="mean"):
    r = st[(b, q, h)]; return r[k]
for b in ("flat", "hill"):
    print(f"stock {b}, q3: {stock_of(b, 3, 7):.1f} -> {stock_of(b, 3, 9):.1f}, empty {mean([stock_of(b, 3, h, 'empty') for h in (7, 8, 9)]):.0%}")
lg = [r for r in T if r["empty"] is not None and r["elev"] is not None and r["relief"] is not None and r["sub_dist"] and r["sub_dist"] > 0]
print(f"logistic inputs: {len(lg):,} stations, {sum(r['empty'] >= .2 for r in lg)} run out at 20%")
