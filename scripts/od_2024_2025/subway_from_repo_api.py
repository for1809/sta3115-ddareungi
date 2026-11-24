# -*- coding: utf-8 -*-
"""Replace the subway columns of the 2024-2025 station tables with ones computed from the repo's API list
(data/subway_stations.csv, Seoul subway master API, 784 station-line rows), and drop the land-use zone columns.
subway_nearest: nearest station name; subway_dist_m: metres to it; subway_lines: lines at that station;
subway_n_500m: distinct station names within 500 m. Distances in EPSG:5179."""
import pandas as pd, geopandas as gpd, numpy as np
from scipy.spatial import cKDTree
sub = pd.read_csv("data/subway_stations.csv", dtype=str)
sub[["lat", "lon"]] = sub[["lat", "lon"]].astype(float)
g = gpd.GeoSeries(gpd.points_from_xy(sub.lon, sub.lat), crs=4326).to_crs(5179)
sub["x"], sub["y"] = g.x.values, g.y.values
nlines = sub.groupby("name").line.nunique()
tree = cKDTree(sub[["x", "y"]].values)
def fix(path):
    t = pd.read_csv(path, dtype={"no": str, "st_id": str})
    p = gpd.GeoSeries(gpd.points_from_xy(t.lon, t.lat), crs=4326).to_crs(5179)
    xy = np.c_[p.x.values, p.y.values]
    d, i = tree.query(xy)
    t["subway_nearest"] = sub.name.values[i]
    t["subway_dist_m"] = d.round(0)
    t["subway_lines"] = nlines.reindex(t.subway_nearest).values
    t["subway_n_500m"] = [sub.name.iloc[j].nunique() for j in tree.query_ball_point(xy, r=500)]
    t = t.drop(columns=[c for c in t.columns if c.startswith("zone_")])
    t.to_csv(path, index=False, encoding="utf-8-sig")
    return t
for f in ["data/od_2024_2025/master/station_master_final.csv", "data/od_2024_2025/od/s0_station_summary.csv"]:
    t = fix(f); print(f, len(t), "median subway m:", t.subway_dist_m.median())
