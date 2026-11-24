# -*- coding: utf-8 -*-
"""
따릉이 시간대별 이용정보(2024-01 ~ 2025-12) 전처리
  T1: 구 x 연월
  T2: 구 x 날짜 x 시간 (+ 요일/휴일/시간대/계절 파생변수)
  T3: 구 x 날짜 x 시간 x 성별 x 연령대 x 권종

사용법
  python3 preprocess_ddareungi.py master  <대여소정보 폴더> <출력폴더>
  python3 preprocess_ddareungi.py month   <월별 csv 파일> <출력폴더>
  python3 preprocess_ddareungi.py combine <출력폴더>
(월별 파일이 커서 한 달씩 따로 돌리고, 마지막에 combine으로 합침)
"""
import sys, os, glob, re
import pandas as pd

# ---------------------------------------------------------------
# 1. 대여소 마스터: 5개 시점 xlsx를 합쳐(union) 대여소번호 -> 자치구, 위경도
# ---------------------------------------------------------------
def build_master(st_dir, out_dir):
    rows = []
    for f in sorted(glob.glob(os.path.join(st_dir, "*.xlsx"))):
        snap = re.search(r"(\d\d)\.(\d+)월", f)
        snap = f"20{snap.group(1)}-{int(snap.group(2)):02d}"
        d = pd.read_excel(f, header=None, skiprows=5).iloc[:, [0, 1, 2, 4, 5, 6]]
        d.columns = ["no", "name", "gu", "lat", "lon", "installed"]
        d = d[pd.to_numeric(d["no"], errors="coerce").notna()].copy()
        d["no"] = d["no"].astype(int)
        d["name"] = d["name"].astype(str).str.strip()
        d["snapshot"] = snap
        rows.append(d)
    allst = pd.concat(rows)

    # 시점별 구별 대여소 수 (분석 1의 대여소 불균형 변수)
    cnt = allst.groupby(["snapshot", "gu"]).size().unstack("snapshot").reset_index()
    cnt.to_csv(os.path.join(out_dir, "station_count_by_gu.csv"), index=False, encoding="utf-8-sig")

    # 최신 시점 정보 우선으로 번호당 1행
    master = (allst.sort_values("snapshot", ascending=False)
                   .drop_duplicates("no")
                   .sort_values("no"))
    master.to_csv(os.path.join(out_dir, "station_master.csv"), index=False, encoding="utf-8-sig")
    print("대여소 마스터:", len(master), "개 /", master["gu"].nunique(), "개 구")


# ---------------------------------------------------------------
# 2. 월별 정제 + 집계
# ---------------------------------------------------------------
def clean_chunk(d):
    d.columns = d.columns.str.strip()
    # 2025-01~06 파일은 '이동거리'로 되어있고 '이용시간(분)'이 없음
    d = d.rename(columns={"이동거리": "dist", "이동거리(M)": "dist",
                          "이용시간(분)": "min", "연령대": "연령대코드"})
    if "min" not in d:
        d["min"] = float("nan")
    d["no"] = pd.to_numeric(d["대여소번호"], errors="coerce")
    d["n"] = pd.to_numeric(d["이용건수"], errors="coerce").fillna(0)
    d["dist"] = pd.to_numeric(d["dist"], errors="coerce")
    d["min"] = pd.to_numeric(d["min"], errors="coerce")
    d["hour"] = pd.to_numeric(d["대여시간"], errors="coerce").astype("Int64")
    d["date"] = d["대여일자"]

    d["sex"] = d["성별"].fillna("").str.upper().replace({"": "미상"})
    d["age"] = d["연령대코드"].fillna("기타").replace({"기타": "미상"})
    d["pass"] = d["대여구분코드"].map({"정기권": "정기권", "일일권": "일일권"}).fillna("기타")
    return d[["date", "hour", "no", "sex", "age", "pass", "n", "dist", "min"]]


def process_month(csv_path, out_dir):
    ym = re.search(r"(\d{6})\.csv$", csv_path).group(1)
    master = pd.read_csv(os.path.join(out_dir, "station_master.csv"))[["no", "gu"]]

    t2_parts, t3_parts, st_parts = [], [], []
    raw_rows, raw_n, unmatched = 0, 0, []
    reader = pd.read_csv(csv_path, encoding="cp949", encoding_errors="replace",
                         dtype=str, chunksize=1_000_000)
    for ch in reader:
        d = clean_chunk(ch)
        raw_rows += len(d); raw_n += d["n"].sum()
        d = d.merge(master, on="no", how="left")
        unmatched.append(d[d["gu"].isna()])
        d = d[d["gu"].notna()]

        t2_parts.append(d.groupby(["gu", "date", "hour"], as_index=False)[["n", "dist", "min"]]
                         .sum(min_count=1))
        t3_parts.append(d.groupby(["gu", "date", "hour", "sex", "age", "pass"], as_index=False)["n"].sum())
        st_parts.append(d[["gu", "no"]].drop_duplicates())

    # 청크 경계에서 같은 key가 나뉠 수 있으므로 한번 더 합침
    t2 = pd.concat(t2_parts).groupby(["gu", "date", "hour"], as_index=False)[["n", "dist", "min"]].sum(min_count=1)
    t3 = pd.concat(t3_parts).groupby(["gu", "date", "hour", "sex", "age", "pass"], as_index=False)["n"].sum()
    st = pd.concat(st_parts).drop_duplicates().groupby("gu").size().rename("active_station").reset_index()
    st["ym"] = ym

    part = os.path.join(out_dir, "parts"); os.makedirs(part, exist_ok=True)
    t2.to_csv(os.path.join(part, f"T2_{ym}.csv"), index=False)
    t3.to_csv(os.path.join(part, f"T3_{ym}.csv"), index=False)
    st.to_csv(os.path.join(part, f"ST_{ym}.csv"), index=False)

    um = pd.concat(unmatched)
    qa = pd.DataFrame([{"ym": ym, "raw_rows": raw_rows, "raw_n": raw_n,
                        "matched_n": t2["n"].sum(), "unmatched_n": um["n"].sum(),
                        "unmatched_station": ";".join(map(str, sorted(um["no"].dropna().astype(int).unique())[:20])),
                        "has_min": t2["min"].notna().any()}])
    qa.to_csv(os.path.join(part, f"QA_{ym}.csv"), index=False)
    print(qa.to_string(index=False))


# ---------------------------------------------------------------
# 3. 결합 + 파생변수
# ---------------------------------------------------------------
HOLIDAYS = [
    # 2024
    "2024-01-01", "2024-02-09", "2024-02-10", "2024-02-11", "2024-02-12", "2024-03-01",
    "2024-04-10", "2024-05-05", "2024-05-06", "2024-05-15", "2024-06-06", "2024-08-15",
    "2024-09-16", "2024-09-17", "2024-09-18", "2024-10-01", "2024-10-03", "2024-10-09", "2024-12-25",
    # 2025
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-03-01", "2025-03-03",
    "2025-05-05", "2025-05-06", "2025-06-03", "2025-06-06", "2025-08-15", "2025-10-03",
    "2025-10-05", "2025-10-06", "2025-10-07", "2025-10-08", "2025-10-09", "2025-12-25",
]

def add_calendar(d):
    dt = pd.to_datetime(d["date"])
    d["ym"] = dt.dt.strftime("%Y%m")
    d["month"] = dt.dt.month
    d["quarter"] = dt.dt.quarter
    d["season"] = d["month"].map({12: "겨울", 1: "겨울", 2: "겨울", 3: "봄", 4: "봄", 5: "봄",
                                  6: "여름", 7: "여름", 8: "여름", 9: "가을", 10: "가을", 11: "가을"})
    d["wday"] = dt.dt.dayofweek.map(dict(enumerate(["월", "화", "수", "목", "금", "토", "일"])))
    d["weekend"] = dt.dt.dayofweek >= 5
    d["holiday"] = d["date"].isin(HOLIDAYS)
    d["offday"] = d["weekend"] | d["holiday"]          # 주말 or 공휴일
    d["daytype"] = d["weekend"].map({True: "weekend", False: "weekday"})   # 주중/주말 binary (요일 기준)
    return d

def time_band(h):
    if 7 <= h <= 9:   return "출근(07-09)"
    if 17 <= h <= 19: return "퇴근(17-19)"
    if 0 <= h <= 5:   return "심야(00-05)"
    return "기타"

def combine(out_dir):
    part = os.path.join(out_dir, "parts")
    qa = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(os.path.join(part, "QA_*.csv"))))
    qa.to_csv(os.path.join(out_dir, "QA_monthly.csv"), index=False, encoding="utf-8-sig")

    t2 = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(os.path.join(part, "T2_*.csv"))))
    # 이용 0건인 (구, 날짜, 시간)은 원자료에 행이 없음 -> 전체 격자를 만들고 0으로 채움
    grid = pd.MultiIndex.from_product([sorted(t2["gu"].unique()), sorted(t2["date"].unique()), range(24)],
                                      names=["gu", "date", "hour"]).to_frame(index=False)
    t2 = grid.merge(t2, on=["gu", "date", "hour"], how="left")
    # 이용시간(min)은 2025-01~06 결측 -> 사용하지 않고 이동거리(dist)로 대체
    t2 = t2.drop(columns="min")
    t2[["n", "dist"]] = t2[["n", "dist"]].fillna(0)
    t2["dist_per_trip"] = t2["dist"] / t2["n"].where(t2["n"] > 0)     # 1회 평균 이동거리(m)
    t2 = add_calendar(t2)
    t2["band"] = t2["hour"].map(time_band)
    t2.to_csv(os.path.join(out_dir, "T2_gu_date_hour.csv"), index=False, encoding="utf-8-sig")

    # T1: 원자료에 날짜가 빠진 달이 있으므로(2025-02: 2/17~2/28 없음) 합계 대신 일평균(n_per_day)으로 비교
    st = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(os.path.join(part, "ST_*.csv"))))
    st["ym"] = st["ym"].astype(str)

    def make_t1(keys):
        t = t2.groupby(keys, as_index=False).agg(n=("n", "sum"), dist=("dist", "sum"),
                                                 n_days=("date", "nunique"))
        t = t.merge(st, on=["gu", "ym"], how="left")
        t["n_per_day"] = t["n"] / t["n_days"]                         # 일평균 이용건수
        t["dist_per_day"] = t["dist"] / t["n_days"]                   # 일평균 총 이동거리(m)
        t["dist_per_trip"] = t["dist"] / t["n"]                       # 1회 평균 이동거리(m)
        t["n_per_station_day"] = t["n_per_day"] / t["active_station"] # 대여소 1개당 일평균 이용
        return t

    make_t1(["gu", "ym"]).to_csv(os.path.join(out_dir, "T1_gu_month.csv"), index=False, encoding="utf-8-sig")
    t1d = make_t1(["gu", "ym", "daytype"])                            # 주중/주말 분리 버전
    t1d.to_csv(os.path.join(out_dir, "T1_gu_month_daytype.csv"), index=False, encoding="utf-8-sig")
    t1 = t1d

    files = sorted(glob.glob(os.path.join(part, "T3_*.csv")))
    out3 = os.path.join(out_dir, "T3_gu_date_hour_condition.csv.gz")
    for i, f in enumerate(files):
        d = add_calendar(pd.read_csv(f))
        d["band"] = d["hour"].map(time_band)
        d.to_csv(out3, index=False, mode="w" if i == 0 else "a", header=(i == 0), compression="gzip")
    print("완료: T1", t1.shape, "/ T2", t2.shape)


# ---------------------------------------------------------------
# 4. 기상청 ASOS 서울(108) 시간별 자료 정제 + T2에 join
# ---------------------------------------------------------------
def weather(out_dir, *asos_files):
    w = pd.concat(pd.read_csv(f, encoding="utf-8-sig") for f in asos_files)
    w["dt"] = pd.to_datetime(w["TM"].astype(str), format="%Y%m%d%H%M")   # KST, 정시 관측
    w = w.drop_duplicates("dt").sort_values("dt")

    # 결측 코드 처리
    #  RN = -9 : 무강수 -> 0mm  /  WS, WD = -9 : 결측 -> NaN
    #  TA = -9.0 은 앞뒤 시간과 이어지는 실제 영하 기온이므로 그대로 둠
    w.loc[w["RN"] == -9, "RN"] = 0
    w.loc[w["WS"] == -9, "WS"] = float("nan")

    # 관측 자체가 없는 시간(2024-03-11~12, 18시간)은 NaN으로 남김
    full = pd.DataFrame({"dt": pd.date_range(w["dt"].min().normalize(), w["dt"].max().normalize()
                                             + pd.Timedelta(hours=23), freq="h")})
    w = full.merge(w, on="dt", how="left")
    w = w.rename(columns={"TA": "temp", "RN": "rain", "WS": "wind", "HM": "humid"})
    w["rain_yn"] = w["rain"] > 0
    w["date"] = w["dt"].dt.strftime("%Y-%m-%d")
    w["hour"] = w["dt"].dt.hour
    w = w[["date", "hour", "temp", "rain", "rain_yn", "wind", "humid"]]
    w.to_csv(os.path.join(out_dir, "weather_hourly.csv"), index=False, encoding="utf-8-sig")

    # 일 단위 요약 (일평균 기온, 일강수량)
    wd = w.groupby("date", as_index=False).agg(temp_day=("temp", "mean"), temp_max=("temp", "max"),
                                               rain_day=("rain", "sum"))
    wd["rain_day_yn"] = wd["rain_day"] > 0
    wd.to_csv(os.path.join(out_dir, "weather_daily.csv"), index=False, encoding="utf-8-sig")

    t2 = pd.read_csv(os.path.join(out_dir, "T2_gu_date_hour.csv"))
    t2 = t2.merge(w, on=["date", "hour"], how="left").merge(wd, on="date", how="left")
    t2.to_csv(os.path.join(out_dir, "T2_gu_date_hour_weather.csv"), index=False, encoding="utf-8-sig")
    print("weather:", w.shape, "/ T2+weather:", t2.shape, "/ temp NA 행:", t2["temp"].isna().sum())


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "master":  build_master(sys.argv[2], sys.argv[3])
    if step == "month":   process_month(sys.argv[2], sys.argv[3])
    if step == "combine": combine(sys.argv[2])
    if step == "weather": weather(sys.argv[2], *sys.argv[3:])   # weather <출력폴더> <ASOS csv들>

