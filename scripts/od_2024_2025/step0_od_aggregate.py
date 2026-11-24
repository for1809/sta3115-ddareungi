# -*- coding: utf-8 -*-
"""
STEP 0-1. OD 월별 zip -> 대여소(ST-ID) x 날짜 x 시간 대여/반납 건수
  대여 = '출발시간' 행, 시작_대여소_ID, 기준_시간대(출발 시각)
  반납 = '도착시간' 행, 종료_대여소_ID, 기준_시간대(도착 시각). 종료 대여소 'X'(미반납) 제외
사용법: python3 step0_od_aggregate.py <OD zip> <출력폴더>
"""
import sys, os, re, io, zipfile
import pandas as pd

od_zip, out_dir = sys.argv[1], sys.argv[2]
ym = re.search(r"(\d{6})\.zip$", od_zip).group(1)
cols = ["기준_날짜", "집계_기준", "기준_시간대", "시작_대여소_ID", "종료_대여소_ID", "전체_건수"]

# 일부 일별 파일은 칼럼 이름이 다르거나(2024-07) UTF-8로 저장돼 있음(2024-11) -> 통일
RENAME = {"기준_시간": "기준_시간대", "시작_대여소": "시작_대여소_ID",
          "종료_대여소": "종료_대여소_ID", "전체건수": "전체_건수",
          # 2025-01-01~08, 2025-07-01~02 파일은 영어 칼럼명
          "stdr_de": "기준_날짜", "dvcd": "집계_기준", "tmzon": "기준_시간대",
          "start_statn_id": "시작_대여소_ID", "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수"}
# 2024-11-27 파일은 비어 있음(행 0개) -> 그 날은 결측

def read_day(raw):
    for enc in ("cp949", "utf-8-sig"):
        try:
            d = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    d.columns = d.columns.str.strip()
    return d.rename(columns=RENAME)[cols]

rent_parts, ret_parts, n_x = [], [], 0
with zipfile.ZipFile(od_zip) as z:
    for name in sorted(z.namelist()):
        d = read_day(z.read(name))
        d["n"] = d["전체_건수"].astype(int)
        d["hour"] = d["기준_시간대"].astype(int) // 100
        a = d[d["집계_기준"] == "출발시간"]
        rent_parts.append(a.groupby(["시작_대여소_ID", "기준_날짜", "hour"])["n"].sum())
        b = d[d["집계_기준"] == "도착시간"]
        n_x += b.loc[b["종료_대여소_ID"] == "X", "n"].sum()
        b = b[b["종료_대여소_ID"] != "X"]
        ret_parts.append(b.groupby(["종료_대여소_ID", "기준_날짜", "hour"])["n"].sum())

rent = pd.concat(rent_parts); rent.index.names = ["st_id", "date", "hour"]
ret = pd.concat(ret_parts); ret.index.names = ["st_id", "date", "hour"]
t = pd.concat([rent.groupby(level=[0, 1, 2]).sum().rename("rent"),
               ret.groupby(level=[0, 1, 2]).sum().rename("ret")], axis=1).fillna(0).astype(int).reset_index()
t["date"] = pd.to_datetime(t["date"]).dt.strftime("%Y-%m-%d")

os.makedirs(out_dir, exist_ok=True)
t.to_csv(os.path.join(out_dir, f"od_hour_{ym}.csv.gz"), index=False, compression="gzip")
print(ym, "rows", len(t), "rent", t.rent.sum(), "ret", t.ret.sum(), "미반납X", n_x, "days", t.date.nunique())
