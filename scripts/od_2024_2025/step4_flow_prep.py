# -*- coding: utf-8 -*-
"""
STEP 4-2. 흐름 지도용 데이터 만들기 (좌표계 EPSG:5179, m)
입력 : in/od_pairs_all_clearweekday.csv.gz, in/station_master_final.csv, 등고선 shp, in/seoul_gu.json
출력 : out/
  s4_vector_1km.csv     1km 격자별 흐름 벡터 (vx, vy), 칸 순유출, 대여소 수
  s4_flow_zoom_500m.csv 서대문·성북 일대 500m 격자 사이 순이동 (상위)
  s4_terrain_100m.csv   100m 격자 지형 (고도, 음영)
정의
  이동량 = 맑은 평일 하루 평균 (378일로 나눔)
  두 칸 i, j 사이 순이동 net_ij = f(i->j) - f(j->i)  (왕복 이동은 상쇄되고 돌아오지 않는 이동만 남음)
  칸 i의 흐름 벡터 V_i = sum_j net_ij * (i->j 단위벡터)  : 이 칸 주변에서 자전거가 순수하게 움직이는 방향
"""
import sys
import numpy as np, pandas as pd, geopandas as gpd, shapely
from scipy.interpolate import LinearNDInterpolator
from shapely import vectorized  # noqa
N_DAYS = 378
CONT = sys.argv[1]

st = pd.read_csv("in/station_master_final.csv").dropna(subset=["st_id"])
g = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.lon, st.lat), crs=4326).to_crs(5179)
st["x"], st["y"] = g.geometry.x.values, g.geometry.y.values
xy = st.set_index("st_id")[["x", "y", "elevation_m", "gu"]]

p = pd.read_csv("in/od_pairs_all_clearweekday.csv.gz")
p = p[(p.st_o != p.st_d) & p.st_o.isin(xy.index) & p.st_d.isin(xy.index)].copy()
for c in ["n_day", "n_am", "n_pm"]:
    p[c] = p[c] / N_DAYS
p[["xo", "yo"]] = xy.loc[p.st_o, ["x", "y"]].values
p[["xd", "yd"]] = xy.loc[p.st_d, ["x", "y"]].values

def cell_flows(p, size, col):
    q = p.assign(ci=(p.xo // size).astype(int), cj=(p.yo // size).astype(int),
                 di=(p.xd // size).astype(int), dj=(p.yd // size).astype(int))
    q = q[(q.ci != q.di) | (q.cj != q.dj)]
    f = q.groupby(["ci", "cj", "di", "dj"])[col].sum().rename("f").reset_index()
    rev = f.rename(columns={"ci": "di", "cj": "dj", "di": "ci", "dj": "cj", "f": "f_rev"})
    f = f.merge(rev, on=["ci", "cj", "di", "dj"], how="left").fillna({"f_rev": 0})
    f["net"] = f.f - f.f_rev
    return f

# 1) 1km 벡터장 ---------------------------------------------------------
S = 1000
for col, tag in [("n_day", "day"), ("n_am", "am")]:
    f = cell_flows(p, S, col)
    dx, dy = (f.di - f.ci) * S, (f.dj - f.cj) * S
    L = np.hypot(dx, dy)
    f["vx"], f["vy"] = f.net * dx / L, f.net * dy / L
    v = f.groupby(["ci", "cj"])[["vx", "vy"]].sum().reset_index()
    outnet = f[f.net > 0].groupby(["ci", "cj"]).net.sum() - f[f.net < 0].groupby(["ci", "cj"]).net.sum().abs()
    v = v.merge(outnet.rename("cell_net").reset_index(), on=["ci", "cj"], how="left").fillna({"cell_net": 0})
    v["x"], v["y"] = (v.ci + 0.5) * S, (v.cj + 0.5) * S
    v["mag"] = np.hypot(v.vx, v.vy)
    v["daytype"] = tag
    if tag == "day":
        V = v
    else:
        V = pd.concat([V, v])
cnt = st.assign(ci=(st.x // S).astype(int), cj=(st.y // S).astype(int)).groupby(["ci", "cj"]).agg(
    n_station=("st_id", "size"), elev=("elevation_m", "mean")).reset_index()
V = V.merge(cnt, on=["ci", "cj"], how="left")
V.to_csv("out/s4_vector_1km.csv", index=False)
print("1km 벡터 칸:", (V.daytype == "day").sum(), "/ 크기 중앙값", V[V.daytype == "day"].mag.median().round(2))

# 2) 서대문·성북 일대 500m 순이동 ----------------------------------------
S2 = 500
zoom = st[st.gu.isin(["서대문구", "성북구", "종로구", "은평구", "중구", "동대문구", "마포구", "강북구"])]
x0, x1 = zoom.x.quantile(0.01) - 500, zoom.x.quantile(0.99) + 500
y0, y1 = zoom.y.quantile(0.01) - 500, zoom.y.quantile(0.99) + 500
pz = p[p.xo.between(x0, x1) & p.yo.between(y0, y1) & p.xd.between(x0, x1) & p.yd.between(y0, y1)]
f = cell_flows(pz, S2, "n_day")
f = f[f.net > 0]
cell = st.assign(ci=(st.x // S2).astype(int), cj=(st.y // S2).astype(int)).groupby(["ci", "cj"]).agg(
    elev=("elevation_m", "mean"), cx=("x", "mean"), cy=("y", "mean")).reset_index()
f = f.merge(cell.rename(columns={"elev": "elev_o", "cx": "xo", "cy": "yo"}), on=["ci", "cj"]) \
     .merge(cell.rename(columns={"ci": "di", "cj": "dj", "elev": "elev_d", "cx": "xd", "cy": "yd"}), on=["di", "dj"])
f["elev_drop"] = f.elev_o - f.elev_d          # 양수 = 내리막으로 이동
f = f.sort_values("net", ascending=False)
f.to_csv("out/s4_flow_zoom_500m.csv", index=False)
top = f.head(200)
print("zoom 순이동 쌍:", len(f), "/ 상위 200개 중 내리막 비율", (top.elev_drop > 0).mean().round(3),
      "/ 순이동 가중 평균 고도차", np.average(f.elev_drop, weights=f.net).round(1))
print("zoom 범위", round(x0), round(x1), round(y0), round(y1))
# 전체(서울) 쌍에서도 순이동의 고도차 방향
fa = cell_flows(p, 500, "n_day"); fa = fa[fa.net > 0]
fa = fa.merge(cell.rename(columns={"elev": "elev_o", "cx": "xo", "cy": "yo"}), on=["ci", "cj"]) \
       .merge(cell.rename(columns={"ci": "di", "cj": "dj", "elev": "elev_d", "cx": "xd", "cy": "yd"}), on=["di", "dj"])
fa["elev_drop"] = fa.elev_o - fa.elev_d
nz = fa[fa.elev_drop.abs() >= 5]
print("서울 전체 500m 순이동 중 고도차 5m 이상:", round(nz.net.sum()), "대/일, 그중 내리막 비율",
      (nz[nz.elev_drop > 0].net.sum() / nz.net.sum()).round(3))
fa.to_csv("out/s4_flow_all_500m.csv", index=False)

# 3) 지형 100m ----------------------------------------------------------
c = gpd.read_file(CONT, encoding="cp949").to_crs(5179)
coords, idx = shapely.get_coordinates(c.geometry.values, return_index=True)
pts = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "h": c["CONT"].values[idx]})
pts = pts.assign(gx=pts.x // 25, gy=pts.y // 25).drop_duplicates(["gx", "gy", "h"])
gu = gpd.read_file("in/seoul_gu.json").to_crs(5179)
seoul = gu.union_all()
bx0, by0, bx1, by1 = seoul.bounds
R = 100
gx, gy = np.meshgrid(np.arange(bx0, bx1, R) + R / 2, np.arange(by0, by1, R) + R / 2)
inside = shapely.contains_xy(seoul, gx, gy)
z = LinearNDInterpolator(pts[["x", "y"]].values, pts.h.values)(gx, gy)
# 음영기복(북서쪽 빛)
zz = np.where(np.isnan(z), np.nanmin(z), z)
dzdy, dzdx = np.gradient(zz, R)
slope = np.arctan(np.hypot(dzdx, dzdy))
aspect = np.arctan2(-dzdx, dzdy)
az, alt = np.radians(315), np.radians(45)
shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
T = pd.DataFrame({"x": gx.ravel(), "y": gy.ravel(), "elev": z.ravel(), "shade": shade.ravel(), "inside": inside.ravel()})
T[T.inside].drop(columns="inside").to_csv("out/s4_terrain_100m.csv", index=False)
print("지형 격자:", T.inside.sum())

# 4) 벡터와 지형 경사 방향 비교 -------------------------------------------
#    지형을 약 500m 규모로 평활화한 뒤 1km 칸 중심의 내리막 방향(-기울기)과 흐름 벡터의 각도 비교
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
zs = gaussian_filter(zz, sigma=5)                       # 100m 격자에서 sigma 5칸 = 약 500m
gy_, gx_ = np.gradient(zs, R)                           # m/m
ax, ay = np.arange(bx0, bx1, R) + R / 2, np.arange(by0, by1, R) + R / 2
fx = RegularGridInterpolator((ay, ax), gx_, bounds_error=False)
fy = RegularGridInterpolator((ay, ax), gy_, bounds_error=False)
V = pd.read_csv("out/s4_vector_1km.csv")
pts_ = np.c_[V.y, V.x]
V["down_x"], V["down_y"] = -fx(pts_), -fy(pts_)         # 내리막 방향
V["slope_pct"] = np.hypot(V.down_x, V.down_y) * 100     # 경사(%)
V["cos_down"] = (V.vx * V.down_x + V.vy * V.down_y) / (V.mag * np.hypot(V.down_x, V.down_y))
V["dir_class"] = np.where(V.slope_pct < 1, "평지",
                 np.where(V.cos_down > 0.5, "내리막", np.where(V.cos_down < -0.5, "오르막", "비스듬")))
V.to_csv("out/s4_vector_1km.csv", index=False)
for tag in ["day", "am"]:
    v = V[(V.daytype == tag) & (V.n_station >= 2)]
    s = v[v.slope_pct >= 1]
    print(tag, "경사 1% 이상 칸", len(s), "/", len(v),
          "| 흐름 크기 가중 비율:", (s.groupby("dir_class").mag.sum() / s.mag.sum()).round(3).to_dict())
