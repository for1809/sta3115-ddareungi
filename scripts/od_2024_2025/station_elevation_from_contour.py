# -*- coding: utf-8 -*-
"""
국토지리정보원 연속수치지형도 등고선(N3L_F001, CONT = 높이 m, 5m 간격)으로
따릉이 대여소 고도를 보간한다.

방법: 등고선 꼭짓점(x, y, 높이)을 10m 격자로 솎아낸 뒤 Delaunay 삼각망 선형 보간.
      삼각망 바깥(서울 경계 밖) 대여소는 가장 가까운 꼭짓점 높이로 대체.
사용법: python3 station_elevation_from_contour.py <등고선 shp> <ddareungi_stations.gpkg> <출력 csv>
"""
import sys
import numpy as np, pandas as pd, geopandas as gpd, shapely
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree

cont_shp, st_gpkg, out_csv = sys.argv[1:4]

c = gpd.read_file(cont_shp, encoding="cp949").to_crs(5179)
coords, idx = shapely.get_coordinates(c.geometry.values, return_index=True)
h = c["CONT"].values[idx]
pts = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "h": h})
pts = pts.assign(gx=(pts.x // 10), gy=(pts.y // 10)).drop_duplicates(["gx", "gy", "h"])
print("보간에 쓰는 꼭짓점:", len(pts))

st = gpd.read_file(st_gpkg).to_crs(5179)
sx, sy = st.geometry.x.values, st.geometry.y.values

interp = LinearNDInterpolator(pts[["x", "y"]].values, pts["h"].values)
elev = interp(sx, sy)

tree = cKDTree(pts[["x", "y"]].values)
d_near, i_near = tree.query(np.c_[sx, sy])
outside = np.isnan(elev)
elev[outside] = pts["h"].values[i_near[outside]]

# 대여소 주변 고저차(반경 300m 안 꼭짓점 높이의 최대 - 최소): '언덕 위/아래' 맥락 변수
nb = tree.query_ball_point(np.c_[sx, sy], r=300)
hv = pts["h"].values
relief = np.array([hv[i].max() - hv[i].min() if len(i) else 0 for i in nb])

out = pd.DataFrame({"no": st["no"], "st_id": st["st_id"], "name": st["name"], "gu": st["gu"],
                    "elevation_m": elev.round(1), "relief_300m": relief,
                    "dist_nearest_contour_m": d_near.round(0), "outside_hull": outside})
out.to_csv(out_csv, index=False, encoding="utf-8-sig")
print("삼각망 밖(최근접 대체):", outside.sum())
print(out["elevation_m"].describe().round(1).to_string())
