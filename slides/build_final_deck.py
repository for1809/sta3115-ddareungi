"""Final talk deck: the teammate's deck (slides/team/deck_ddareungi_teammate.html, kept untouched) plus our analysis.

Changes, all made here so the original stays as received:
  1. a new slide "STEP 7. WHEN" after slide 16 (g12): hourly stock matched with trip records shows the hills are
     refilled every day by moves other than rides (mostly rebalancing), but not during the 7-9 am peak
     (figure slides/figures_en/10b_rebalance_bare.png; numbers from analysis/rebalance_bare_log.txt, by bare-earth
     elevation like the teammate deck; 2025 weekdays with under 1 mm of rain)
  2. the conclusion: refill the hills before the morning, and a warning about merging low-use stations
     (bottom 20% of use with another station within 300 m: 89 of the 164 at 40 m and above already empty)
  3. limits, item 1: trucks are now seen, but only as the part of stock change rides do not explain
  4. page numbers: each slide's counter is reset to its new place
Run from the project root:  python slides/build_final_deck.py
Output: slides/deck_final.html
"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "team" / "deck_ddareungi_teammate.html"
OUT = ROOT / "deck_final.html"
FIG = ROOT / "figures_en" / "10b_rebalance_bare.png"   # bare-earth elevation bands, as in the teammate deck

t = SRC.read_text(encoding="utf-8")
img = "data:image/png;base64," + base64.b64encode(FIG.read_bytes()).decode("ascii")

WHEN = f"""<section id="when" data-transition="fade">
<p class="eyebrow">STEP 7. WHEN</p>
<h2>Trucks already refill the hills every day, but not before 8 am</h2>
<div class="body">
<div class="figcard"><img src="{img}" alt="Bikes added to a station per weekday by riders and by other moves, by bare-earth elevation band. Below 20 m riders add 1.0 and other moves take 1.5; at 40 m and above riders take 4.4 and other moves add 4.4." style="width:1071px;height:557px;object-fit:contain"></div>
<div class="side" style="gap:18px">
<div class="stat"><p class="stat-num">−4.4</p><p class="stat-lab">bikes a day riders take from stations at 40 m and above</p></div>
<div class="stat"><p class="stat-num blue">+4.4</p><p class="stat-lab">bikes a day put back there by other moves, mostly rebalancing</p></div>
<div class="stat"><p class="stat-num ink">0.99</p><p class="stat-lab">correlation of stock change and rides at 7 to 9 am: almost no refilling in the peak</p></div>
<div class="stat"><p class="stat-num">28%</p><p class="stat-lab">of commute hours those stations still have zero bikes</p></div>
<p class="note muted" style="font-size:20px">2025 dry weekdays; hourly stock matched with trips.</p>
</div>
</div>
<div class="foot"><p class="foot-l">STA3115 Exploratory Data Analysis, Group 1</p><p class="foot-r"></p></div>
<aside>Trip records do not show the trucks. So we also took the hourly stock at every station and matched it with the trips: whatever the rides do not explain is other moves, mostly the trucks. Below 20 metres, riders bring in about one bike a day and other moves take about one away. At 40 metres and above, riders take away about four bikes a day, and other moves bring almost exactly four back. So the trucks already go up the hills every day. But between 7 and 9 a.m. the stock moves almost exactly with the rides, a correlation of 0.99: almost nothing is refilled during the peak, and those hill-top stations still have no bikes in 28% of the commute hours. The question is not only where the trucks go, but when.</aside>
</section>
"""

CONCLUSION = """<section id="conclusion" class="accent" data-transition="fade">
<p class="eyebrow">CONCLUSION</p>
<h2>Send the trucks up the hills before the morning, and skip the stations that refill themselves</h2>
<div class="take">
<p class="take-line soft">Bikes roll downhill in the morning and are not ridden back up: net flow runs downhill 69% of the time where the ground slopes.</p>
<p class="take-line soft">An empty station at 9 am is not always a problem. 703 stations (G2) refill themselves by night.</p>
<p class="take-line soft">The hills already get bikes back every day, yet stay empty in 28% of commute hours: the refill does not arrive before the peak.</p>
<p class="take-line"><b>Refill the 893 hill-top G1 stations before 7 am, with bikes from the 533 low-lying G3 stations. And do not merge low-use stations on ride counts alone: half the hill-top merge candidates already run empty.</b></p>
</div>
<aside>To sum up. Bikes roll downhill in the morning and are not ridden back up. Because of that, an empty station at 9 am is not always a problem: 703 stations get their bikes back by night without any help. The stations that really need a truck are the 893 G1 stations on the hills, and they are already refilled every day, just not before the morning peak. So the plan is about timing: bring bikes from the 533 G3 stations on low ground that pile up all day, and have them on the hills before 7 a.m. One more point for the debate about cutting the system: if you merge the least-used stations by ride counts alone, half of the hill-top candidates are stations that are already empty in the morning. Their low use may mean no bikes, not no demand.</aside>
</section>
"""

secs = list(re.finditer(r"<section\b.*?</section>\s*", t, re.S))
ids = [re.search(r'id="([^"]+)"', m.group(0)).group(1) for m in secs]
assert "when" not in ids and {"g12", "conclusion", "limits"} <= set(ids), ids

parts, k_prev = [], 0
for m, sid in zip(secs, ids):
    parts.append(t[k_prev:m.start()])
    s = m.group(0)
    if sid == "conclusion":
        s = CONCLUSION + "\n"
    if sid == "limits":
        old = "Trip records hide trucks: we see where bikes go, not where trucks already move them."
        assert s.count(old) == 1, "limits item 1 changed"
        s = s.replace(old, "Trucks appear only as the stock change that rides do not explain: we do not see when each truck comes.")
        s = s.replace("First, trip records do not show the trucks, so we see where riders move bikes, not where trucks already move them back.",
                      "First, we see the trucks only indirectly, as the change in stock that rides do not explain, so we do not know when each truck arrives.")
    parts.append(s)
    if sid == "g12":
        parts.append(WHEN + "\n")
    k_prev = m.end()
parts.append(t[k_prev:])
out = "".join(parts)

# page numbers: section n resets the counter to n - 1 (hidden slides do not count)
n = 0


def renumber(m):
    global n
    n += 1
    tag = re.sub(r'\sstyle="counter-reset: page \d+"', "", m.group(0))
    return tag.replace("<section ", f'<section style="counter-reset: page {n - 1}" ', 1)


out = re.sub(r"<section\b[^>]*>", renumber, out)
OUT.write_text(out, encoding="utf-8")
print(n, "slides ->", OUT, round(OUT.stat().st_size / 1e6, 2), "MB")
