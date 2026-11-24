# -*- coding: utf-8 -*-
"""Station x age group x (weekday/offday) x hour rentals from the hourly usage files (OA-15245), 2024-2025.
Run inside the folder with the 24 monthly files '서울특별시 공공자전거 이용정보(시간대별)_YYYYMM.csv' (CP949).
Needs t3_days.csv (date, offday). Output: age_station_hour.csv (sum = 80,387,987 rentals)."""
import pandas as pd, glob, os
days = pd.read_csv("t3_days.csv")
off = dict(zip(days.date, days.offday.astype(str).str.lower() == "true"))
parts = []
for f in sorted(glob.glob("*.csv")):
    if "이용정보" not in f: continue
    d = pd.read_csv(f, encoding="cp949", usecols=["대여일자", "대여시간", "대여소번호", "연령대코드", "이용건수"], dtype={"대여소번호": str})
    d["off"] = d["대여일자"].map(off).fillna(True)
    parts.append(d.groupby(["대여소번호", "연령대코드", "off", "대여시간"], as_index=False)["이용건수"].sum())
pd.concat(parts).groupby(["대여소번호", "연령대코드", "off", "대여시간"], as_index=False)["이용건수"].sum().to_csv("age_station_hour.csv", index=False)
