# -*- coding: utf-8 -*-
"""
OD 데이터의 대여소ID(ST-xxx) <-> 이용정보/대여소마스터의 대여소번호 매핑
방법: 같은 달의 '대여소 x 날짜 x 시간 대여건수' 패턴을 두 데이터에서 만들고,
      ST-ID마다 패턴이 가장 비슷한(상관계수 최대) 대여소번호를 고름.

사용법: python3 station_id_mapping.py <OD zip> <이용정보 시간대별 csv> <출력 csv>
"""
import sys, zipfile, io
import numpy as np, pandas as pd

od_zip, use_csv, out_csv = sys.argv[1:4]

# 1) OD: 출발시간 기준 행만 -> ST-ID x (날짜, 시간) 대여건수
parts, name_parts = [], []
with zipfile.ZipFile(od_zip) as z:
    for name in sorted(z.namelist()):
        d = pd.read_csv(io.BytesIO(z.read(name)), encoding="cp949", dtype=str,
                        usecols=["기준_날짜", "집계_기준", "기준_시간대", "시작_대여소_ID", "시작_대여소명", "전체_건수"])
        d = d[d["집계_기준"] == "출발시간"]
        d["hour"] = d["기준_시간대"].astype(int) // 100
        d["n"] = d["전체_건수"].astype(int)
        parts.append(d.groupby(["시작_대여소_ID", "기준_날짜", "hour"], as_index=False)["n"].sum())
        name_parts.append(d[["시작_대여소_ID", "시작_대여소명"]].drop_duplicates())
od = pd.concat(parts)
od["date"] = pd.to_datetime(od["기준_날짜"]).dt.strftime("%Y-%m-%d")
od_names = pd.concat(name_parts).drop_duplicates("시작_대여소_ID")

# 2) 이용정보: 대여소번호 x (날짜, 시간) 대여건수
u = pd.read_csv(use_csv, encoding="cp949", dtype=str, usecols=["대여일자", "대여시간", "대여소번호", "이용건수"])
u["no"] = pd.to_numeric(u["대여소번호"], errors="coerce")
u = u.dropna(subset=["no"])
u["hour"] = u["대여시간"].astype(int)
u["n"] = pd.to_numeric(u["이용건수"])
u = u.groupby(["no", "대여일자", "hour"], as_index=False)["n"].sum().rename(columns={"대여일자": "date"})

# 3) 같은 (날짜, 시간) 격자 위의 벡터로 만들고 상관계수 행렬
keys = sorted(set(zip(od["date"], od["hour"])) | set(zip(u["date"], u["hour"])))
kidx = {k: i for i, k in enumerate(keys)}
def matrix(df, idcol):
    ids = sorted(df[idcol].unique())
    M = np.zeros((len(ids), len(keys)), dtype=np.float32)
    r = {s: i for i, s in enumerate(ids)}
    M[df[idcol].map(r).values, [kidx[k] for k in zip(df["date"], df["hour"])]] = df["n"].values
    return ids, M
st_ids, A = matrix(od, "시작_대여소_ID")
nos, B = matrix(u, "no")
def zscore(M):
    M = M - M.mean(1, keepdims=True)
    return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
C = zscore(A) @ zscore(B).T                      # ST-ID x 대여소번호 상관계수

best = C.argmax(1)
best_r = C.max(1)
C2 = C.copy(); C2[np.arange(len(best)), best] = -1
second_r = C2.max(1)                              # 2등과의 차이로 신뢰도 판단

res = pd.DataFrame({"st_id": st_ids, "no": np.array(nos)[best].astype(int),
                    "r": best_r.round(4), "r_2nd": second_r.round(4),
                    "od_total": A.sum(1).astype(int), "use_total": B[best].sum(1).astype(int)})
res = res.merge(od_names.rename(columns={"시작_대여소_ID": "st_id", "시작_대여소명": "od_name"}), on="st_id", how="left")
# 같은 대여소번호를 두 ST-ID가 가져간 경우 표시
res["dup_no"] = res.duplicated("no", keep=False)
res.to_csv(out_csv, index=False, encoding="utf-8-sig")

print("ST-ID", len(st_ids), "/ 대여소번호", len(nos))
print("r >= 0.9:", (res.r >= 0.9).mean().round(4), " r >= 0.7:", (res.r >= 0.7).mean().round(4))
print("중복 배정:", res.dup_no.sum())
print(res.sort_values("r").head(8).to_string())
