"""Net outflow in bikes, no docks: chart data and wording for the final deck (read by slides/build_final_deck.py, step 9b).

Decision 2026-11-25: dock counts are not station capacity (bikes are parked next to the docks; at 93% of stations the
95th-percentile hourly stock exceeds the dock count), so the deck drops "% of docks" everywhere:
  station net outflow      bikes a day (cw_net) and bikes per morning, 7-9 am (cw_am_net)
  2x2 groups               sign only, the team's original rule: G1 am > 0 and day > 0, G2 am > 0 and day <= 0,
                           G3 am <= 0 and day <= 0, G4 am <= 0 and day > 0; no "balanced" band
  district values          mean bikes per station in the district
Inputs   the deck's own chart data (ixdata in the built deck), data/od_2024_2025/od/s0_station_summary.csv,
         data/od_2024_2025/od/s0_station_hour_profile.csv.gz (2024-2025 clear weekdays)
"""
import csv, gzip, math, re, json
from collections import defaultdict
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[1]
OD = R / "data/od_2024_2025/od"


def sign_type(am, day):
    if am > 0:
        return "G1" if day > 0 else "G2"
    return "G4" if day > 0 else "G3"


def q(v, p):
    return float(np.quantile(np.asarray(v, float), p))


def lowess(xs, ys, grid, span=0.75):
    """Local quadratic fit with tricube weights, like R's loess() defaults (span 0.75, degree 2)."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    k = int(math.floor(span * len(xs))); out = []
    for g in grid:
        d = np.abs(xs - g); h = np.sort(d)[k - 1]
        w = np.sqrt(np.clip(1 - (d / h) ** 3, 0, None) ** 3)
        A = np.vander(xs - g, 3, increasing=True)
        b, *_ = np.linalg.lstsq(A * w[:, None], ys * w, rcond=None); out.append(b[0])
    return out


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def ols_std(X, y):
    """Standardised OLS: coefficients, two-sided p (normal approximation, n in the thousands), R^2."""
    X = (X - X.mean(0)) / X.std(0); y = (y - y.mean()) / y.std()
    A = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ beta; n, k = A.shape
    s2 = res @ res / (n - k); se = np.sqrt(np.diag(s2 * np.linalg.inv(A.T @ A)))
    p = [math.erfc(abs(b / s) / math.sqrt(2)) for b, s in zip(beta, se)]
    return beta[1:], p[1:], 1 - (res @ res) / (y @ y)


def build(D, old_types=False):
    """Return (new chart data, numbers). old_types=True rebuilds the deck's own values (check against the deck)."""
    rows = [r for r in csv.DictReader(open(OD / "s0_station_summary.csv", encoding="utf-8-sig")) if r["enough_days"] == "True"]
    P = D["stations"]
    assert len(rows) == len(P)
    for r, p in zip(rows, P):
        assert abs(float(r["cw_net_rate"]) - p["d"]) < 0.051, (r["st_id"], p)
    hp = defaultdict(dict)
    with gzip.open(OD / "s0_station_hour_profile.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["daytype"] == "clear_weekday":
                hp[r["st_id"]][int(r["hour"])] = float(r["net"])
    N = json.loads(json.dumps(D))
    S = N["stations"]
    for r, p in zip(rows, S):
        net, am = float(r["cw_net"]), float(r["cw_am_net"])
        if old_types:
            p["t"] = p["t"]
        else:
            p["d"], p["a"], p["t"] = round(net, 1), round(am, 1), sign_type(am, net)
        p["_id"], p["_am"], p["_pm"], p["_net"] = r["st_id"], am, float(r["cw_pm_net"]), net
        p["_relief"] = float(r["relief_300m"]) if r["relief_300m"] else None
        p["_sub"] = float(r["subway_dist_m"]) if r["subway_dist_m"] else None
    val = (lambda p: p["d"])
    # elevation bands and bins
    span = [(0, 20), (20, 40), (40, 1e9)]
    N["bands"] = []
    for lo, hi in span:
        v = [val(p) for p in S if lo <= p["e"] < hi]
        N["bands"].append({"n": len(v), "mean": round(float(np.mean(v)), 1), "med": round(float(np.median(v)), 1), "out": round(sum(x > 0 for x in v) / len(v), 3)})
    for b in N["bins"]:
        lo, hi = [float(x) for x in b["b"].strip("[)").split(",")]
        v = [val(p) for p in S if lo <= p["e"] < hi]
        b["n"], b["out"] = len(v), round(sum(x > 0 for x in v) / len(v), 3)
    # LOESS of net outflow on elevation, on the deck's grid; NA below the lowest station, as in the deck
    xs = [p["e"] for p in S]; ys = [val(p) for p in S]
    grid = N["elev_curve"]["x"]
    fit = lowess(xs, ys, grid)
    N["elev_curve"]["y"] = [("NA" if g < min(xs) + 4 else round(f, 2)) for g, f in zip(grid, fit)]
    # districts: mean bikes per station
    by = defaultdict(list)
    for p in S:
        by[p["g"]].append(p)
    for g in N["guday"]:
        x = by[g["g"]]
        g["r"] = round(float(np.mean([p["_net"] for p in x])), 2)
        g["am"] = round(float(np.mean([p["_am"] for p in x])), 2)
        g["abs"] = round(float(np.mean([abs(p["_net"]) for p in x])), 2)
        g["n"] = len(x)
    for g in N["guhour"]:
        x = by[g["g"]]
        g["r"] = round(sum(hp[p["_id"]].get(g["h"], 0.0) for p in x) / len(x), 3)
    # groups
    ty = defaultdict(list)
    for p in S:
        ty[p["t"]].append(p)
    order = [t["ty"] for t in N["tcount"]]
    N["tcount"] = [{"ty": t, "N": len(ty[t])} for t in order if ty[t]] if not old_types else N["tcount"]
    N["prof"] = [{"ty": t, "h": h, "net": round(float(np.mean([hp[p["_id"]].get(h, 0.0) for p in ty[t]])), 3)}
                 for t in ("G1", "G2", "G3", "G4") for h in range(24)]
    def box(t, k):
        v = [p[k] for p in ty[t] if p[k] is not None]
        return {"ty": t, "n": len(ty[t]), "p10": round(q(v, .1), 1), "q1": round(q(v, .25), 1), "med": round(q(v, .5), 1), "q3": round(q(v, .75), 1), "p90": round(q(v, .9), 1)}
    N["box_e"] = [box(t, "e") for t in ("G1", "G2", "G3", "G4")]
    N["box_s"] = [box(t, "_sub") for t in ("G1", "G2", "G3", "G4")]
    N["g12"] = [{"ty": t, "n": len(ty[t]), "elev": round(q([p["e"] for p in ty[t]], .5), 1),
                 "relief": round(q([p["_relief"] for p in ty[t] if p["_relief"] is not None], .5), 1),
                 "sub": round(q([p["_sub"] for p in ty[t] if p["_sub"] is not None], .5)),
                 "am": round(float(np.mean([p["_am"] for p in ty[t]])), 2), "pm": round(float(np.mean([p["_pm"] for p in ty[t]])), 2),
                 "day": round(float(np.mean([p["_net"] for p in ty[t]])), 2)} for t in ("G1", "G2")]
    # feature table: the features we can rebuild here (the land-use zone is not in this repository)
    ok = [p for p in S if p["_relief"] is not None and p["_sub"] is not None and p["_sub"] > 0]
    feats = [("Elevation (m)", [p["e"] for p in ok]), ("Local relief within 300 m (m)", [p["_relief"] for p in ok]),
             ("Distance to nearest subway station (log)", [math.log(p["_sub"]) for p in ok])]
    y = np.array([val(p) for p in ok])
    beta, pv, r2 = ols_std(np.column_stack([f for _, f in feats]), y)
    N["factors"] = [{"var": n, "rho": round(spearman(f, y), 2), "beta": round(float(b), 2), "p": pv_}
                    for (n, f), b, pv_ in zip(feats, beta, pv)]
    N["r2"] = round(float(r2), 3); N["_n_factor"] = len(ok)
    for p in S:
        for k in [k for k in p if k.startswith("_")]:
            del p[k]
    return N


# ---------------------------------------------------------------- the deck itself: data, charts, words
def f1(v):
    return f"{v:+.1f}".replace("-", "−")


def apply(html):
    """Swap the deck's chart data for the bike-based one and rewrite every dock wording. Every old string must be found."""
    m = re.search(r'(<script[^>]*id="ixdata"[^>]*>)(.*?)(</script>)', html, re.S)
    D = json.loads(m.group(2))
    N = build(D)
    S = N["stations"]
    cnt = {t["ty"]: t["N"] for t in N["tcount"]}
    tot = len(S)
    pc = lambda t: round(100 * cnt[t] / tot)
    B = N["bands"]; bins = {b["b"]: b for b in N["bins"]}
    n50 = sum(p["e"] >= 50 for p in S); l50 = sum(p["e"] >= 50 and p["d"] > 0 for p in S)
    gd = {g["g"]: g for g in N["guday"]}
    g1, g2 = N["g12"]
    gu_g1 = {}
    for p in S:
        gu_g1.setdefault(p["g"], []).append(p["t"] == "G1")
    assert max(gu_g1, key=lambda k: sum(gu_g1[k]) / len(gu_g1[k])) == "Seodaemun"
    sh_sdm = round(100 * sum(gu_g1["Seodaemun"]) / len(gu_g1["Seodaemun"]))
    emptied = cnt["G1"] + cnt["G2"]
    fac, r2 = N.pop("factors"), N.pop("r2"); N.pop("_n_factor")
    N["factors"], N["r2"] = D["factors"], D["r2"]          # the table is static HTML; the data block keeps its old copy
    pfmt = lambda p: "&lt; 0.001" if p < 0.001 else f"{p:.2f}"
    rows = "".join(('<tr class="hl">' if j == 0 else "<tr>") + f'<td>{r["var"]}</td><td style="text-align:right">{r["rho"]:.2f}</td>'
                   f'<td style="text-align:right">{r["beta"]:.2f}</td><td style="text-align:right">{pfmt(r["p"])}</td></tr>\n' for j, r in enumerate(fac))
    html = html[:m.start(2)] + json.dumps(N, ensure_ascii=False, separators=(",", ":")) + html[m.end(2):]
    am = lambda g: f1(gd[g]["am"])
    sub1, sub2 = round(g1["sub"], -1), round(g2["sub"], -1)
    R_ = [
        # scope
        ("Computed for the whole day and for the 7–9 am commute, and divided by the number of docks so that large and small stations can be compared.",
         "Counted in bikes, for the whole day and for the 7–9 am commute."),
        ("station elevation from 1:5,000 contour maps, subway stations and land-use zones.", "station elevation from 1:5,000 contour maps and subway stations."),
        ("We compute it for the whole day and for the morning commute, and divide it by the number of docks so that large and small stations can be compared. "
         "A daily net outflow of plus 40% means a station loses bikes equal to 40% of its docks every day, and a truck has to bring them back.",
         "We count it in bikes, for the whole day and for the morning commute. A daily net outflow of plus 4 means the station ends every day "
         "four bikes short, and a truck has to bring them back."),
        # district map
        ("Gwangjin +27%, Seodaemun +23%, Dongdaemun +18% of docks",
         f"Gwangjin {am('Gwangjin')}, Seodaemun {am('Seodaemun')}, Dongdaemun {am('Dongdaemun')} bikes per station"),
        ("Seongdong −39%, Jung −15%, Yeongdeungpo −13%:", f"Seongdong {am('Seongdong')}, Jung {am('Jung')}, Yeongdeungpo {am('Yeongdeungpo')} bikes:"),
        ("'Net flow, 7–9 am (% of docks)'", "'Net flow, 7–9 am (bikes per station)'"),
        ("'Net flow, whole day (% of docks)'", "'Net flow, whole day (bikes per station)'"),
        ("div(GD[g][key], k === 1 ? 30 : 15)", "div(GD[g][key], k === 1 ? 4 : 2)"),
        # elevation scatter
        ('<p class="stat-num blue">−15%</p><p class="stat-lab">below 20 m: these stations gain bikes on average; 38% end the day short</p>',
         f'<p class="stat-num blue">{f1(B[0]["mean"])}</p><p class="stat-lab">bikes a day below 20 m: these stations gain bikes on average; {B[0]["out"]:.0%} end the day short</p>'),
        ('<p class="stat-num ink">+4%</p><p class="stat-lab">20–40 m: roughly balanced; 56% end the day short</p>',
         f'<p class="stat-num ink">{f1(B[1]["mean"])}</p><p class="stat-lab">bikes a day at 20–40 m: roughly balanced; {B[1]["out"]:.0%} end the day short</p>'),
        ('<p class="stat-num">+42%</p><p class="stat-lab">40 m and above: 91% end the day short</p>',
         f'<p class="stat-num">{f1(B[2]["mean"])}</p><p class="stat-lab">bikes a day at 40 m and above: {B[2]["out"]:.0%} end the day short</p>'),
        ("Every one of the 143 stations at 50 m or higher loses bikes.",
         f"{l50} of the {n50} stations at 50 m or higher lose bikes."),
        ("Each dot is a station, with elevation across and daily net outflow up, as a share of its docks. Below 20 metres, stations gain bikes on average, "
         "15% of their docks a day. Between 20 and 40 metres they are roughly balanced. At 40 metres and above, they lose 42% of their docks every day, "
         "and 91% of them end the day short. Every one of the 143 stations above 50 metres loses bikes. The red LOESS curve sits just below zero on low "
         "ground, crosses zero at about 25 metres and reaches around plus 50% by 60 metres.",
         f"Each dot is a station, with elevation across and daily net outflow up, in bikes. Below 20 metres, stations gain bikes on average, "
         f"{-B[0]['mean']:.1f} a day. Between 20 and 40 metres they are roughly balanced. At 40 metres and above, they lose {B[2]['mean']:.1f} bikes "
         f"every day, and {B[2]['out']:.0%} of them end the day short. {l50} of the {n50} stations above 50 metres lose bikes. The red LOESS curve "
         "sits below zero on low ground, crosses zero at about 25 metres and reaches about plus 5 bikes a day by 60 metres."),
        ("Y0 = -100, Y1 = 150", "Y0 = -20, Y1 = 30"),
        ("[-100, -50, 0, 50, 100, 150]", "[-20, -10, 0, 10, 20, 30]"),
        ("+ Math.abs(v) + '%');", "+ Math.abs(v));"),
        ("'Daily net outflow (% of docks)'", "'Daily net outflow (bikes a day)'"),
        ("y: y(140)", "y: y(28)"), ("y: y(-90)", "y: y(-18)"),
        ("100%/+150% and above 100 m sit at the edge", "20/+30 and above 100 m sit at the edge"),
        ("y: y0 + 54, 'text-anchor': 'end', 'font-size': 46", "y: y0 + 50, 'text-anchor': 'end', 'font-size': 40"),
        ("${cnt.G2} recover by night, ${cnt.G1} do not", "${cnt.G2.toLocaleString('en')} recover by night, ${cnt.G1.toLocaleString('en')} do not"),
        ("sgn(b.mean, 0) + '%'", "sgn(b.mean, 1)"),
        ("sgn(best.d, 0) + '% of docks'", "sgn(best.d, 1) + ' bikes a day'"),
        ("'Below 20 m: on average these stations gain bikes, 15% of their docks a day.'",
         f"'Below 20 m: on average these stations gain {-B[0]['mean']:.1f} bikes a day.'"),
        ("'40 m and above: they lose 42% of their docks every day. 91% of them end the day short.'",
         f"'40 m and above: they lose {B[2]['mean']:.1f} bikes a day, and {B[2]['out']:.0%} of them end the day short.'"),
        ("about +50% by 60 m", "about +5 bikes a day by 60 m"),
        # station map
        ("p => Math.abs(p.d) <= 10", "p => Math.abs(p.d) <= 1"),
        ("p => p.d > 10", "p => p.d > 1"), ("p => p.d < -10", "p => p.d < -1"),
        ("loses over 10% of docks a day (", "loses over 1 bike a day ("), ("gains over 10% (", "gains over 1 ("),
        ("'Now the stations that lose more than 10% of their docks a day, in red.", "'Now the stations that lose more than one bike a day, in red."),
        ("Now we add the stations that lose more than 10% of their docks every day, in red.", "Now we add the stations that lose more than one bike a day, in red."),
        ("below 15 metres, 39% of stations end the day short; at 50 metres and above, every one of them does.",
         f"below 15 metres, {bins['[0,15)']['out']:.0%} of stations end the day short; at 50 metres and above, {l50} of {n50} do."),
        # feature table
        ("Outcome: daily net outflow (% of docks), 2,843 stations. ρ: Spearman correlation, one feature at a time. β: all five features in one linear "
         "model on standardised variables (R² = 0.15).",
         f"Outcome: daily net outflow (bikes), {tot:,} stations. ρ: Spearman correlation, one feature at a time. β: all three features in one linear "
         f"model on standardised variables (R² = {r2:.2f})."),
        ("we compared five candidates.", "we compared three candidates."),
        ("The second is the coefficient when all five enter one linear model on a standardised scale.",
         "The second is the coefficient when all three enter one linear model on a standardised scale."),
        ("Elevation comes first on both: a correlation of 0.40 and a coefficient of 0.33, three times larger than any other. Distance to the subway and "
         "land-use zone hardly matter. The model explains only 15% of the variation,",
         f"Elevation comes first on both: a correlation of {fac[0]['rho']:.2f} and a coefficient of {fac[0]['beta']:.2f}, several times larger than any "
         f"other. Distance to the subway hardly matters. The model explains only {round(100 * r2)}% of the variation,"),
        # 2x2
        ("(net outflow beyond ±10% of docks)", "(net outflow above zero or not, in bikes)"),
        ('<p class="stat-num">893 vs 703</p>', f'<p class="stat-num">{cnt["G1"]:,} vs {cnt["G2"]:,}</p>'),
        ('<p class="stat-num ink">1,596</p>', f'<p class="stat-num ink">{emptied:,}</p>'),
        ("Why does only half of them recover?", "Why do fewer than half of them recover?"),
        ("Stations within 10% of their docks on both counts are balanced. ", ""),
        ("which stays short: 893 stations, 31%.", f"which stays short: {cnt['G1']:,} stations, {pc('G1')}%."),
        ("which refills by night: 703.", f"which refills by night: {cnt['G2']:,}."),
        ("1,596 stations lose bikes every morning. About half of them get their bikes back by night, and the other half never do.",
         f"{emptied:,} stations lose bikes every morning. {cnt['G2']:,} of them get their bikes back by night; {cnt['G1']:,} never do."),
        ("'The right column is the 1,596 stations emptied every morning. 703 recover by night; 893 never do. Why?'",
         f"'The right column is the {emptied:,} stations emptied every morning. {cnt['G2']:,} recover by night; {cnt['G1']:,} never do. Why?'"),
        # group map
        ("893 stations, 31%:", f"{cnt['G1']:,} stations, {pc('G1')}%:"), ("703, 25%:", f"{cnt['G2']:,}, {pc('G2')}%:"),
        ("533, 19%:", f"{cnt['G3']:,}, {pc('G3')}%:"), ("424, 15%:", f"{cnt['G4']:,}, {pc('G4')}%:"),
        ("In Seodaemun, 60% of the stations that are not balanced are G1,", f"In Seodaemun, {sh_sdm}% of the stations are G1,"),
        # G1 against G2
        (">−5.7 bikes<", f">{f1(g2['pm'])} bikes<"), (">−1.3 bikes<", f">{f1(g1['pm'])} bikes<"),
        ("28 m vs 19 m", f"{g1['elev']:.0f} m vs {g2['elev']:.0f} m"),
        ("(500 m vs 470 m)", f"({sub1:.0f} m vs {sub2:.0f} m)"),
        ("about 1.3 bikes per station against 5.7 for G2", f"about {-g1['pm']:.1f} bikes per station against {-g2['pm']:.1f} for G2"),
        ("G1 stations sit at a median of 28 metres, G2 stations at 19.", f"G1 stations sit at a median of {g1['elev']:.0f} metres, G2 stations at {g2['elev']:.0f}."),
        ("500 against 470 metres", f"{sub1:.0f} against {sub2:.0f} metres"),
        ("G1 stations sit a median 28 m up, G2 at 19 m", f"G1 stations sit a median {g1['elev']:.0f} m up, G2 at {g2['elev']:.0f} m"),
        # conclusion
        ("703 stations (G2)", f"{cnt['G2']:,} stations (G2)"), ("893 hill-top G1", f"{cnt['G1']:,} hill-top G1"),
        ("533 low-lying G3", f"{cnt['G3']:,} low-lying G3"), ("703 stations get their bikes back", f"{cnt['G2']:,} stations get their bikes back"),
        ("the 893 G1 stations", f"the {cnt['G1']:,} G1 stations"), ("the 533 G3 stations", f"the {cnt['G3']:,} G3 stations"),
    ]
    for old, new in R_:
        assert old in html, old[:90]
        html = html.replace(old, new)
    html, k = re.subn(r"`Balanced, within[^`]*`", "`Only the sign counts: every station falls in one of the four groups`", html)
    assert k == 1
    t0 = html.index('<tr class="hl"><td>Elevation (m)</td>'); t1 = html.index("</table>", t0)
    html = html[:t0] + rows + html[t1:]
    return html, N
