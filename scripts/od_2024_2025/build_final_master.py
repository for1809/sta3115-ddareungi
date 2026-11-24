# -*- coding: utf-8 -*-
"""
따릉이 대여소 최종 마스터 (station_master_final.csv / .gpkg)

합치는 것
  station_table.csv      : 대여소번호, OD ST-ID 매핑, 이름, 구, 위경도, 거치대 수
  station_elevation.csv  : 고도(등고선 보간), 반경 300m 고저차
  서울시_지하철역.shp     : 가장 가까운 역, 거리(m), 반경 500m 안 역 수
  서울시_용도지역.gpkg    : 대여소 위치의 용도지역 (대/중/소분류)

사용법:
python3 build_final_master.py <station_table.csv> <station_elevation.csv> <지하철역.shp> <용도지역.gpkg> <출력폴더>
"""
import sys, os
import numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree

tab_csv, elev_csv, subway_shp, zoning_gpkg, out_dir = sys.argv[1:6]

# 1) 기본: 대여소 마스터 + 매핑 ------------------------------------------
tab = pd.read_csv(tab_csv)
base = tab.dropna(subset=["no"]).copy()
base["no"] = base["no"].astype(int)
base = base[base["mapped"]]                                       # 매핑 확정 ST-ID만
master = pd.read_csv(os.path.join(os.path.dirname(tab_csv), "station_master.csv"))
m = master.merge(base[["no", "st_id", "r"]].rename(columns={"r": "map_r"}), on="no", how="left")

# 2) 고도 ----------------------------------------------------------------
el = pd.read_csv(elev_csv)[["no", "elevation_m", "relief_300m", "dist_nearest_contour_m"]]
m = m.merge(el, on="no", how="left")

g = gpd.GeoDataFrame(m, geometry=gpd.points_from_xy(m.lon, m.lat), crs=4326).to_crs(5179)
xy = np.c_[g.geometry.x, g.geometry.y]

# 3) 지하철역: 같은 역사명(환승역)은 하나로 묶음 ---------------------------
sub = gpd.read_file(subway_shp).to_crs(5179)
sub_st = (sub.assign(x=sub.geometry.x, y=sub.geometry.y)
             .groupby("역사명").agg(x=("x", "mean"), y=("y", "mean"), n_lines=("호선", "nunique"))
             .reset_index())
tree = cKDTree(sub_st[["x", "y"]].values)
d, i = tree.query(xy)
g["subway_nearest"] = sub_st["역사명"].values[i]
g["subway_dist_m"] = d.round(0)
g["subway_lines"] = sub_st["n_lines"].values[i]                    # 가장 가까운 역의 노선 수(환승역 여부)
g["subway_n_500m"] = [len(x) for x in tree.query_ball_point(xy, r=500)]

# 4) 용도지역: 점이 속한 폴리곤, 없으면 50m 안 가장 가까운 폴리곤 ---------
z = gpd.read_file(zoning_gpkg).to_crs(5179)
z["geometry"] = z.geometry.make_valid()
m_map = {"UQA110": "전용주거", "UQA120": "일반주거", "UQA130": "준주거", "UQA190": "주거기타",
         "UQA210": "중심상업", "UQA220": "일반상업", "UQA230": "근린상업", "UQA240": "유통상업",
         "UQA330": "준공업", "UQA410": "보전녹지", "UQA420": "생산녹지", "UQA430": "자연녹지"}
s_map = {"UQA111": "1종전용주거", "UQA112": "2종전용주거", "UQA121": "1종일반주거", "UQA122": "2종일반주거",
         "UQA123": "3종일반주거", "UQA124": "2종일반주거(7층이하)"}
l_map = {"1": "주거", "2": "상업", "3": "공업", "4": "녹지"}
z["zone_m"] = z["MLSFC_CL"].map(m_map)
z["zone_l"] = z["MLSFC_CL"].str[3].map(l_map)                       # 중분류 코드(UQA120)의 숫자 첫 자리로 대분류
z["zone_s"] = z["SCLAS_CL"].map(s_map).fillna(z["zone_m"])
z = z[["zone_l", "zone_m", "zone_s", "geometry"]]

pts = g[["no", "geometry"]]
j = gpd.sjoin(pts, z, how="left", predicate="within").drop_duplicates("no")
miss = j["zone_l"].isna()
if miss.any():
    near = gpd.sjoin_nearest(pts[pts["no"].isin(j.loc[miss, "no"])], z, how="left",
                             max_distance=50, distance_col="zone_dist_m").drop_duplicates("no")
    j = j.set_index("no"); near = near.set_index("no")
    for c in ["zone_l", "zone_m", "zone_s"]:
        j.loc[near.index, c] = near[c]
    j["zone_dist_m"] = 0.0; j.loc[near.index, "zone_dist_m"] = near["zone_dist_m"]
    j = j.reset_index()
g = g.merge(j[["no", "zone_l", "zone_m", "zone_s", "zone_dist_m"]], on="no", how="left")

# 5) 저장 ----------------------------------------------------------------
cols = ["no", "st_id", "map_r", "name", "gu", "addr", "lat", "lon", "installed", "docks", "op", "snapshot",
        "elevation_m", "relief_300m", "dist_nearest_contour_m",
        "subway_nearest", "subway_dist_m", "subway_lines", "subway_n_500m",
        "zone_l", "zone_m", "zone_s", "zone_dist_m"]
g[cols].to_csv(os.path.join(out_dir, "station_master_final.csv"), index=False, encoding="utf-8-sig")
g[cols + ["geometry"]].to_crs(4326).to_file(os.path.join(out_dir, "station_master_final.gpkg"),
                                            layer="stations", driver="GPKG")

print("대여소:", len(g), "/ ST-ID 매핑:", g.st_id.notna().sum())
print("결측 - 고도:", g.elevation_m.isna().sum(), "/ 용도지역:", g.zone_l.isna().sum())
print("역 거리(m):", g.subway_dist_m.describe().round(0).to_dict())
print(g.zone_l.value_counts(dropna=False).to_string())
print(g.zone_m.value_counts(dropna=False).to_string())
