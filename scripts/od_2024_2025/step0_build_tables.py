# -*- coding: utf-8 -*-
"""
STEP 0-2. 대여소 순유출 테이블 만들기
입력 : in/od_hour_YYYYMM.csv.gz (step0_od_aggregate.py 결과), in/station_master_final.csv, in/weather_daily.csv
출력 : out/
  s0_station_daily.csv.gz   대여소 x 날짜: 대여, 반납, 순유출(하루/출근/퇴근), 날짜 유형
  s0_station_summary.csv    대여소별 요약 (맑은 평일 / 휴일 / 2025-03 맑은 평일) + 유형(G1~G4, 균형)
  s0_station_hour_profile.csv  대여소 x 시간 x (맑은 평일/휴일) 평균 대여·반납·순유출
  s0_daily_seoul.csv        날짜별 서울 전체 불균형(유출 합, 유입 합)
  s0_qa.txt                 검증 기록

정의 (기본값)
  순유출 = 대여 - 반납 (양수 = 자전거가 빠져나감)
  하루 = 00~23시, 출근 = 07~09시, 퇴근 = 17~19시
  맑은 평일 = 주말·공휴일이 아니고 일강수 1mm 미만
  비율(%) = 순유출 / 거치대 수 x 100
  균형 구간 = |출근 비율| < TH 이고 |하루 비율| < TH (기본 TH = 10%)
  대여소의 운영 기간(첫 이용일 ~ 마지막 이용일) 안에서 이용이 없던 날은 0으로 채움
"""
import glob, os
import numpy as np, pandas as pd

IN, OUT = "in", "out"
AM, PM = [7, 8, 9], [17, 18, 19]
HOLIDAYS = {
    "2024-01-01", "2024-02-09", "2024-02-10", "2024-02-11", "2024-02-12", "2024-03-01",
    "2024-04-10", "2024-05-05", "2024-05-06", "2024-05-15", "2024-06-06", "2024-08-15",
    "2024-09-16", "2024-09-17", "2024-09-18", "2024-10-01", "2024-10-03", "2024-10-09", "2024-12-25",
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-03-01", "2025-03-03",
    "2025-05-05", "2025-05-06", "2025-06-03", "2025-06-06", "2025-08-15", "2025-10-03",
    "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-12-25"}
qa = []

# 1) 시간 단위 OD 집계 + 대여소 매핑 ------------------------------------
h = pd.concat(pd.read_csv(f, dtype={"st_id": str, "date": str}) for f in sorted(glob.glob(f"{IN}/od_hour_*.csv.gz")))
st = pd.read_csv(f"{IN}/station_master_final.csv")
st = st[st.st_id.notna()]
tot = h[["rent", "ret"]].sum()
h = h[h.st_id.isin(st.st_id)]
qa.append(f"OD 전체 대여 {tot.rent:,} / 반납 {tot.ret:,}")
qa.append(f"매핑된 대여소만 남긴 뒤 대여 {h.rent.sum():,} ({h.rent.sum()/tot.rent:.4%}), 반납 {h.ret.sum():,} ({h.ret.sum()/tot.ret:.4%})")

# 원본 일부가 잘린 날 제외: 정상일은 (대여-반납)/대여 가 약 0.4%(미반납분). 1%를 넘으면 결측 처리
chk = h.groupby("date")[["rent", "ret"]].sum()
bad = chk[((chk.rent - chk.ret) / chk.rent).abs() > 0.01].index.tolist()
qa.append(f"대여·반납 불일치로 제외한 날 {len(bad)}개: {', '.join(bad)}")
h = h[~h.date.isin(bad)]

dates = sorted(h.date.unique())
qa.append(f"분석 날짜 수 {len(dates)} (2024-11-27은 원본 파일이 비어 있음)")

# 2) 대여소 x 날짜 (운영 기간 안에서 0 채움) ------------------------------
h["am"] = h.hour.isin(AM); h["pm"] = h.hour.isin(PM)
g = h.groupby(["st_id", "date"])
d = pd.DataFrame({
    "rent": g.rent.sum(), "ret": g.ret.sum(),
    "am_rent": h[h.am].groupby(["st_id", "date"]).rent.sum(),
    "am_ret": h[h.am].groupby(["st_id", "date"]).ret.sum(),
    "pm_rent": h[h.pm].groupby(["st_id", "date"]).rent.sum(),
    "pm_ret": h[h.pm].groupby(["st_id", "date"]).ret.sum()}).fillna(0)
span = d.reset_index().groupby("st_id").date.agg(["min", "max"])
full = []
for sid, r in span.iterrows():
    for dt in dates:
        if r["min"] <= dt <= r["max"]:
            full.append((sid, dt))
d = d.reindex(pd.MultiIndex.from_tuples(full, names=["st_id", "date"])).fillna(0).astype(int).reset_index()
d["net"] = d.rent - d.ret
d["am_net"] = d.am_rent - d.am_ret
d["pm_net"] = d.pm_rent - d.pm_ret

w = pd.read_csv(f"{IN}/weather_daily.csv")[["date", "temp_day", "rain_day"]]
cal = pd.DataFrame({"date": dates})
dt = pd.to_datetime(cal.date)
cal["weekend"] = dt.dt.dayofweek >= 5
cal["holiday"] = cal.date.isin(HOLIDAYS)
cal["offday"] = cal.weekend | cal.holiday
cal = cal.merge(w, on="date", how="left")
cal["rain"] = cal.rain_day >= 1
cal["clear_weekday"] = ~cal.offday & ~cal.rain
cal["ym"] = dt.dt.strftime("%Y%m")
d = d.merge(cal[["date", "ym", "offday", "clear_weekday", "rain"]], on="date")
d = d.merge(st[["st_id", "no", "docks"]], on="st_id")
d.to_csv(f"{OUT}/s0_station_daily.csv.gz", index=False, compression="gzip")
qa.append(f"대여소 x 날짜 행 {len(d):,}, 대여소 {d.st_id.nunique()}")
qa.append(f"맑은 평일 {cal.clear_weekday.sum()}일, 휴일 {cal.offday.sum()}일, 비 온 평일 {(~cal.offday & cal.rain).sum()}일")

# 3) 대여소 요약 + 유형 ---------------------------------------------------
def summarize(sub, tag):
    s = sub.groupby("st_id").agg(n_days=("date", "size"), rent=("rent", "mean"), ret=("ret", "mean"),
                                 net=("net", "mean"), am_net=("am_net", "mean"), pm_net=("pm_net", "mean"),
                                 am_rent=("am_rent", "mean"), am_ret=("am_ret", "mean"))
    return s.add_prefix(f"{tag}_")

S = pd.concat([summarize(d[d.clear_weekday], "cw"),
               summarize(d[d.offday], "off"),
               summarize(d[d.clear_weekday & (d.ym == "202503")], "m2503")], axis=1).reset_index()
S = st.merge(S, on="st_id", how="inner")
for tag in ["cw", "off", "m2503"]:
    S[f"{tag}_net_rate"] = S[f"{tag}_net"] / S.docks * 100
    S[f"{tag}_am_rate"] = S[f"{tag}_am_net"] / S.docks * 100

def classify(am, day, th):
    lab = np.where((am > 0) & (day > 0), "G1 영구 결손형",
          np.where((am > 0) & (day <= 0), "G2 자가 회복형",
          np.where((am <= 0) & (day <= 0), "G3 영구 적체형", "G4 주간 활동형")))
    return np.where((np.abs(am) < th) & (np.abs(day) < th), "균형", lab)

for th in [5, 10, 20]:
    S[f"type_th{th}"] = classify(S.cw_am_rate, S.cw_net_rate, th)
S["type"] = S["type_th10"]
S["type_m2503_raw"] = classify(S.m2503_am_net, S.m2503_net, 0)       # 팀 방식(대수, 균형 구간 없음) 대조용
# 맑은 평일 50일 미만 대여소(신설·폐쇄)는 요약에서 표시
S["enough_days"] = S.cw_n_days >= 50
S.to_csv(f"{OUT}/s0_station_summary.csv", index=False, encoding="utf-8-sig")
qa.append(f"요약 대여소 {len(S)}, 맑은 평일 50일 이상 {S.enough_days.sum()}")
qa.append("유형(TH=10%):\n" + S[S.enough_days].type.value_counts().to_string())

# 4) 시간 프로파일: 대여소 x 시간 x (맑은 평일 / 휴일) --------------------
h2 = h.merge(cal[["date", "clear_weekday", "offday"]], on="date")
prof = []
for tag, col in [("clear_weekday", "clear_weekday"), ("offday", "offday")]:
    x = h2[h2[col]].groupby(["st_id", "hour"])[["rent", "ret"]].sum().reset_index()
    ndays = d[d[col]].groupby("st_id").size().rename("n_days")
    x = x.merge(ndays, on="st_id")
    x["rent"] = x.rent / x.n_days; x["ret"] = x.ret / x.n_days
    x["net"] = x.rent - x.ret; x["daytype"] = tag
    prof.append(x)
prof = pd.concat(prof)
prof.to_csv(f"{OUT}/s0_station_hour_profile.csv", index=False)

# 5) 날짜별 서울 전체 불균형 --------------------------------------------
ds = d.groupby("date").agg(rent=("rent", "sum"),
                           out_sum=("net", lambda v: v[v > 0].sum()),
                           in_sum=("net", lambda v: -v[v < 0].sum()),
                           n_station=("st_id", "size")).reset_index().merge(cal, on="date")
ds.to_csv(f"{OUT}/s0_daily_seoul.csv", index=False)

open(f"{OUT}/s0_qa.txt", "w").write("\n".join(qa))
print("\n".join(qa))
