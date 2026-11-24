# -*- coding: utf-8 -*-
"""
1) 달별 매핑(mapping/map_YYYYMM.csv)을 합쳐 ST-ID -> 대여소번호 최종 매핑
2) 대여소 마스터(5개 시점)에 거치대 수(LCD + QR)를 다시 넣어 합침
3) station_table.csv = ST-ID, 대여소번호, 이름, 구, 위경도, 거치대 수, 매핑 신뢰도

사용법: python3 build_station_table.py <대여소정보 폴더> <출력폴더>
"""
import sys, os, glob, re
import pandas as pd

st_dir, out_dir = sys.argv[1], sys.argv[2]

# 1) 매핑 합치기 ---------------------------------------------------------
maps = []
for f in sorted(glob.glob(os.path.join(out_dir, "mapping", "map_*.csv"))):
    m = pd.read_csv(f); m["ym"] = re.search(r"(\d{6})", f).group(1); maps.append(m)
maps = pd.concat(maps)

# 매핑이 확실한 경우만 사용: 상관 0.9 이상 + 2등과 0.1 이상 차이
ok = maps[(maps.r >= 0.9) & (maps.r - maps.r_2nd >= 0.1)]
# 달마다 같은 번호로 매핑됐는지 (일관성)
cons = ok.groupby("st_id")["no"].nunique().rename("n_distinct_no")
best = ok.sort_values("r", ascending=False).drop_duplicates("st_id")[["st_id", "no", "r", "od_name"]]
best = best.merge(cons, on="st_id")
best["n_months"] = best["st_id"].map(ok.groupby("st_id").size())
all_ids = pd.DataFrame({"st_id": maps["st_id"].unique()})
mapping = all_ids.merge(best, on="st_id", how="left")
mapping["mapped"] = mapping["no"].notna() & (mapping["n_distinct_no"] == 1)

# 2) 대여소 마스터 + 거치대 수 -------------------------------------------
rows = []
for f in sorted(glob.glob(os.path.join(st_dir, "*.xlsx"))):
    s = re.search(r"(\d\d)\.(\d+)월", f); snap = f"20{s.group(1)}-{int(s.group(2)):02d}"
    d = pd.read_excel(f, header=None, skiprows=5).iloc[:, :10]
    d.columns = ["no", "name", "gu", "addr", "lat", "lon", "installed", "dock_lcd", "dock_qr", "op"]
    d = d[pd.to_numeric(d["no"], errors="coerce").notna()].copy()
    d["no"] = d["no"].astype(int)
    d["name"] = d["name"].astype(str).str.strip()
    d["docks"] = pd.to_numeric(d["dock_lcd"], errors="coerce").fillna(0) + pd.to_numeric(d["dock_qr"], errors="coerce").fillna(0)
    d["snapshot"] = snap
    rows.append(d)
allst = pd.concat(rows)
master = (allst.sort_values("snapshot", ascending=False).drop_duplicates("no")
               [["no", "name", "gu", "addr", "lat", "lon", "installed", "docks", "op", "snapshot"]])
master.to_csv(os.path.join(out_dir, "station_master.csv"), index=False, encoding="utf-8-sig")

# 3) 합치기 -------------------------------------------------------------
tab = mapping.merge(master, on="no", how="left")
tab.to_csv(os.path.join(out_dir, "station_table.csv"), index=False, encoding="utf-8-sig")

print("ST-ID 전체:", len(mapping), "/ 매핑 확정:", mapping.mapped.sum(),
      "/ 달마다 번호가 다른 ST-ID:", (mapping.n_distinct_no > 1).sum())
print("매핑됐지만 마스터에 없는 번호:", (tab.mapped & tab.gu.isna()).sum())
print("거치대 0 또는 결측:", (master.docks <= 0).sum(), "/ 거치대 수 요약:", master.docks.describe().round(1).to_dict())
dup = tab[tab.mapped].no.duplicated(keep=False).sum(); print("같은 번호에 ST-ID 2개 이상:", dup)
print(tab[~tab.mapped].head(10).to_string())
