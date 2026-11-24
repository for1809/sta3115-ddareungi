# -*- coding: utf-8 -*-
"""
STEP 4-1. OD 월별 zip -> 맑은 평일의 (출발 대여소, 도착 대여소) 쌍별 이동 건수
  '출발시간' 행만 사용 (이동 1건을 한 번만 셈), 도착 대여소 'X'(미반납) 제외
  맑은 평일 목록 = out/s0_daily_seoul.csv 의 clear_weekday (STEP 0과 같은 날짜, 결측일 제외)
출력: pairs/od_pairs_YYYYMM.csv.gz (st_o, st_d, n_day, n_am, n_pm)
사용법: python3 step4_od_pairs.py <OD zip> <출력폴더>
"""
import sys, os, re, io, zipfile
import pandas as pd

od_zip, out_dir = sys.argv[1], sys.argv[2]
ym = re.search(r"(\d{6})\.zip$", od_zip).group(1)
here = os.path.dirname(os.path.abspath(__file__))
cal = pd.read_csv(os.path.join(here, "out", "s0_daily_seoul.csv"), dtype={"date": str})
clear = set(cal.loc[cal.clear_weekday, "date"].str.replace("-", ""))

RENAME = {"기준_시간": "기준_시간대", "시작_대여소": "시작_대여소_ID", "종료_대여소": "종료_대여소_ID",
          "전체건수": "전체_건수", "stdr_de": "기준_날짜", "dvcd": "집계_기준", "tmzon": "기준_시간대",
          "start_statn_id": "시작_대여소_ID", "end_statn_id": "종료_대여소_ID", "cnt": "전체_건수"}
cols = ["기준_날짜", "집계_기준", "기준_시간대", "시작_대여소_ID", "종료_대여소_ID", "전체_건수"]

parts = []
with zipfile.ZipFile(od_zip) as z:
    for name in sorted(z.namelist()):
        day = re.search(r"(\d{8})\.csv$", name).group(1)
        if day not in clear:
            continue
        raw = z.read(name)
        for enc in ("cp949", "utf-8-sig"):
            try:
                d = pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str); break
            except UnicodeDecodeError:
                continue
        d.columns = d.columns.str.strip()
        d = d.rename(columns=RENAME)[cols]
        d = d[(d["집계_기준"] == "출발시간") & (d["종료_대여소_ID"] != "X")]
        d["n"] = d["전체_건수"].astype(int)
        h = d["기준_시간대"].astype(int) // 100
        d["n_am"] = d["n"].where(h.between(7, 9), 0)
        d["n_pm"] = d["n"].where(h.between(17, 19), 0)
        parts.append(d.groupby(["시작_대여소_ID", "종료_대여소_ID"])[["n", "n_am", "n_pm"]].sum())

os.makedirs(out_dir, exist_ok=True)
if parts:
    p = pd.concat(parts).groupby(level=[0, 1]).sum().reset_index()
    p.columns = ["st_o", "st_d", "n_day", "n_am", "n_pm"]
    p.to_csv(os.path.join(out_dir, f"od_pairs_{ym}.csv.gz"), index=False, compression="gzip")
    print(ym, "맑은 평일", len(parts), "일, 쌍", len(p), "이동", p.n_day.sum())
else:
    print(ym, "맑은 평일 없음")
