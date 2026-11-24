"""Wording of the final deck (slides/deck_final.html): same content, numbers and order, plainer English.

Read by slides/build_final_deck.py. For each slide id: the eyebrow, the title, the speaker notes, and
(old, new) pairs for the text in the body. JS gives (old, new) pairs for the chart script: step cues and the
group names drawn inside the charts. Every old string must be found, so a change in the source deck is caught.
"""

NL = chr(10)   # a line break, for pairs that remove a whole line of the slide

GROUPS = [("G1 Never refilled", "G1 Stays short"), ("G2 Refills itself", "G2 Refills by night"),
          ("G3 Piles up", "G3 Collects bikes"), ("G4 Daytime hub", "G4 Office hub")]

SLIDES = {
    "cover": dict(
        pairs=[('<p class="kicker">Where are all the Ddareungi at?</p>', '<p class="kicker">Where do all the Ddareungi go?</p>'),
               ("<h1>Bikes roll down the hills<br>and do not come back up</h1>", "<h1>Bikes roll downhill,<br>and nobody rides them back up</h1>")],
        aside="Hello, we are Group 1. Our topic is Ddareungi, Seoul’s public bike system. We asked a simple question: "
              "where do all the bikes go? The short answer is in the title. In the morning, bikes roll downhill, and nobody rides them back up."),

    "intro": dict(
        title="Seoul’s public bike: rent at one station, return at any other",
        pairs=[("5.06 million members, 250 million rides in ten years", "5.06 million members and 250 million rides in ten years"),
               ("Scan the QR code on the bike with the app. The lock opens by Bluetooth. Age 13 and over, 24 hours a day.",
                "Scan the QR code on the bike in the app and the lock opens. Open to anyone 13 or older, around the clock."),
               ("Lock the rear wheel at any station and the return is automatic. Locked anywhere else, it still counts as rented.",
                "Lock the back wheel at any station and the return is logged. Outside a station, the rental keeps running."),
               ("1,000 won for an hour on a day pass. Season passes run 7 to 365 days; return and rent again when time is up.",
                "A day pass costs 1,000 won per hour. Season passes cover 7 to 365 days; when time runs out, return and rent again."),
               ("7–9 am and 5–7 pm carry 44% of weekday rides. The city already sends 33 staff to 330 crowded or empty stations.",
                "The commute hours, 7–9 am and 5–7 pm, carry 44% of weekday rides. The city already sends 33 staff to 330 stations that run too full or too empty.")],
        aside="First, a quick introduction for anyone who has not used Ddareungi. It started in October 2015, and today about 45,000 bikes "
              "are spread over some 2,800 stations. You rent a bike with an app: scan the QR code and the lock opens. You can return it at any "
              "station by locking the back wheel. A day pass costs 1,000 won an hour, and season passes are also available. The key point for us: "
              "on weekdays, the morning and evening commute hours account for 44% of all rides. Because people pick up a bike at one station and "
              "leave it at another, some stations run empty while others overflow. The city knows this already. At commute times it sends 33 staff "
              "to 330 stations that are too full or too empty. That imbalance is what we studied."),

    "why": dict(
        eyebrow="WHY THIS MATTERS",
        title="Rides are falling while the deficit grows",
        pairs=[("rides a year, 2023 → 2025; 2025 alone is −14.8%", "rides a year from 2023 to 2025, with −14.8% in 2025 alone"),
               ("operating deficit in 2025, almost double the ₩9.4 bn of 2022", "operating deficit in 2025, nearly twice the ₩9.4 bn of 2022")],
        aside="Ddareungi grew quickly, from 32 million rides in 2021 to almost 45 million in 2023. Since then it has fallen two years in a row, "
              "to 37.4 million in 2025, a drop of 14.8% in one year. Over the same period the operating deficit grew, from 9.4 billion won in 2022 "
              "to 17.6 billion won in 2025, nearly twice as much."),

    "cost": dict(
        # only the question, centred; the 53% and the trucks are in the speaker notes
        pairs=[('<p class="eyebrow">WHERE THE MONEY GOES</p>' + NL, ""),
               ('<h2>More than half the running cost is moving bikes around</h2>', '<h2 style="padding-top:47px">Our Question</h2>'),
               ('<div class="cols">\n<div class="col">\n<div class="stat"><p class="big">53%</p><p class="big-lab">of operating cost is labour for redistributing bikes</p></div>\n<p class="text">Those are the trucks we all see on the street, loading bikes at one station and dropping them at another.</p>\n</div>\n<div class="col">\n<p class="text">A truck is needed because some stations run out of bikes while others fill up.</p>\n<p class="lead"><b>Our question:</b> where do bikes pile up, where do they run out, and why?</p>\n<p class="text muted">If we know that, the trucks can go to the right place at the right time.</p>\n</div>\n</div>\n',
                '<div style="flex:1;display:flex;align-items:center;justify-content:center;padding-bottom:80px"><p style="margin:0;font-size:76px;line-height:1.25;font-weight:700;letter-spacing:-1.5px;text-align:center;color:var(--ink)">Where do bikes pile up,<br>where do they run out,<br>and <span style="color:var(--blue)">why</span>?</p></div>\n')],
        aside="Where does the money go? According to Bike Magazine, 53% of the operating cost is staff time spent redistributing bikes. "
              "That is the work of the trucks you see on the street, picking up bikes at one station and dropping them off at another. "
              "They are needed because some stations run dry while others overflow. So our question is: where do bikes pile up, where do they "
              "run out, and why? If the data can answer that, trucks can be sent to the right place at the right time."),

    "factors": dict(
        eyebrow="WHAT MIGHT MATTER",
        title="Possible Factors",
        # 1 and 2 keep only the factor; 3 and 4 keep only what is measured
        pairs=[('class="q-text">Time of day: commuting or leisure?', 'class="q-text">Time of day'),
               ('class="q-text">Weather: rain and temperature', 'class="q-text">Weather'),
               ('class="q-text">Terrain: elevation and slope', 'class="q-text">Elevation and slope'),
               ("Nearby transit: distance to a subway station", "Distance to the nearest subway station")],
        aside="Before looking at the data, we listed what might decide where a bike ends up. Time of day, because commuting and leisure trips "
              "look different. Weather: rain and temperature. Terrain, because pedalling uphill is hard. And transit, since many people ride to "
              "and from the subway. The first two tell us which days to study; the last two are possible explanations."),

    "hours": dict(
        eyebrow="STEP 1. CHOOSING THE DAYS",
        title="Weekdays follow a clear commute pattern; weekends do not",
        pairs=[("two sharp weekday peaks: 11,300 and 13,200 rides in the hour", "two sharp weekday peaks, with 11,300 and 13,200 rides in the hour"),
               ('<p class="stat-num">One hill</p><p class="stat-lab">on weekends and holidays, peaking at 5 pm with 6,900</p>',
                '<p class="stat-num">One broad peak</p><p class="stat-lab">on weekends and holidays, highest at 5 pm with 6,900 rides</p>'),
               ('<p class="stat-num ink">Weekdays</p><p class="stat-lab">are what we study from here, with the 7–9 am commute as the key window</p>',
                '<p class="stat-num ink">Weekdays only</p><p class="stat-lab">from here on, with the 7–9 am commute as the key window</p>')],
        aside="First, time of day. This chart shows the average number of rides started in each hour. On weekdays there are two sharp peaks, "
              "at 8 in the morning and 6 in the evening: that is commuting. On weekends and holidays there is a single broad peak in the "
              "afternoon. Because the weekday pattern repeats day after day, we focus on weekdays, and especially on the morning commute, "
              "from 7 to 9 am."),

    "weather": dict(
        eyebrow="STEP 1. CHOOSING THE DAYS",
        title="Rainy days are too irregular to model, so we set them aside",
        pairs=[('<p class="stat-num blue">Smooth</p><p class="stat-lab">on dry weekdays: rides rise with temperature and dip in the hottest weeks (LOESS, span 0.75)</p>',
                '<p class="stat-num blue">Dry days</p><p class="stat-lab">follow a smooth curve: rides rise with temperature and dip in the hottest weeks (LOESS, span 0.75)</p>'),
               ("Each dot is one of 480 weekdays: every Monday to Friday of 2024 and 2025 except public holidays (490), minus 10 days whose rentals and returns did not match.",
                "Each dot is one weekday: 480 in all, every Monday to Friday in 2024 and 2025 except public holidays (490), minus 10 days with mismatched records."),
               ('<p class="stat-num">Scattered</p><p class="stat-lab">on rainy weekdays (1 mm or more)</p>',
                '<p class="stat-num">Rainy days</p><p class="stat-lab">(1 mm or more) scatter far from any curve</p>'),
               ("the residual spread: SD 37k rides on rainy days vs 13k on dry days, and it grows with temperature",
                "larger residual spread on rainy days (SD 37k vs 13k rides), and it grows with temperature")],
        aside="Next, weather. Each dot is one weekday, with temperature across and total rides up. On dry days the points follow a smooth "
              "LOESS curve: rides rise with temperature and dip a little in the hottest weeks. On days with 1 millimetre of rain or more, rides "
              "fall and the points scatter. The residuals make this clear: on dry days they are small and even, with a standard deviation of "
              "about 13,000 rides. On rainy days the spread is three times larger and grows with temperature. So the effect of rain depends on "
              "things our data does not capture, such as when and how hard it rains. That is why we set rainy days aside and keep dry weekdays."),

    "scope": dict(
        pairs=[("Rentals minus returns at a station. Positive: the station loses bikes. Negative: it gains them.",
                "Rentals minus returns at a station. Positive means the station loses bikes; negative means it gains them."),
               ("Measured for the whole day and for the 7–9 am commute, and divided by the number of docks so big and small stations compare.",
                "Computed for the whole day and for the 7–9 am commute, and divided by the number of docks so that large and small stations can be compared."),
               ("Every station-to-station trip in 2024–2025 (Seoul Open Data, 5-minute records), hourly weather from KMA, station elevation from 1:5,000 contours, subway stations and land-use zones.",
                "Every station-to-station trip in 2024–2025 (Seoul Open Data, 5-minute records), hourly KMA weather, station elevation from 1:5,000 contour maps, subway stations and land-use zones."),
               ("Dry weekday = not a weekend or holiday, and less than 1 mm of rain. Ten days whose rentals and returns did not match were dropped.",
                "A dry weekday is a weekday that is not a public holiday and has under 1 mm of rain. We dropped ten days on which rentals and returns did not match.")],
        aside="That leaves 378 dry weekdays in 2024 and 2025, and 2,843 stations. Our measure is net outflow: rentals minus returns. When it is "
              "positive, the station loses bikes; when it is negative, it gains them. We compute it for the whole day and for the morning "
              "commute, and divide it by the number of docks so that large and small stations can be compared. A daily net outflow of plus 40% "
              "means a station loses bikes equal to 40% of its docks every day, and a truck has to bring them back."),

    "gumap": dict(
        title="Each morning, some districts empty out while others fill up",
        pairs=[("every district lights up at the two commute peaks", "every district is busiest at the two commute peaks"),
               ('<p class="stat-num">Lose, 7–9 am</p>', '<p class="stat-num">Losing, 7–9 am</p>'),
               ('<p class="stat-num blue">Gain, 7–9 am</p>', '<p class="stat-num blue">Gaining, 7–9 am</p>'),
               ("Seongdong −39%, Jung −15%, Yeongdeungpo −13%: offices in Seongsu, the city centre and Yeouido",
                "Seongdong −39%, Jung −15%, Yeongdeungpo −13%: the office areas of Seongsu, the city centre and Yeouido"),
               ("By night the colours do not cancel out. The leftover is what trucks move.",
                "Over the whole day the colours do not cancel out. What is left over is what the trucks have to move.")],
        aside="Now, where. First, plain use: rentals per station in each hour. Drag the slider and you can see every district peak at 8 am "
              "and 6 pm. Next, net flow during the morning commute. Red districts lose bikes and blue districts gain them. Gwangjin, Seodaemun "
              "and Dongdaemun lose bikes, while the office areas of Seongdong, the city centre and Yeouido gain them. Over the whole day the "
              "colours do not cancel out, and what is left over is exactly what the trucks have to move. But a district is a large unit. "
              "What is it about a station that makes it lose bikes?"),

    "traits": dict(
        title="Of the station features we tested, elevation matters most",
        pairs=[('<th style="width:40%">Station trait</th>', '<th style="width:40%">Station feature</th>'),
               ("<td>Relief within 300 m (m)</td>", "<td>Local relief within 300 m (m)</td>"),
               ("<td>Docks at the station</td>", "<td>Number of docks</td>"),
               ("<td>Distance to the nearest subway station (log)</td>", "<td>Distance to nearest subway station (log)</td>"),
               ("Outcome: daily net outflow (% of docks), 2,843 stations. ρ: Spearman, one trait at a time. β: all five traits together in a linear model on standardised variables (R² = 0.15). We use it to rank traits, not to predict.",
                "Outcome: daily net outflow (% of docks), 2,843 stations. ρ: Spearman correlation, one feature at a time. β: all five features in one linear model on standardised variables (R² = 0.15). The model ranks the features; it is not meant to predict.")],
        aside="To see which station features go with losing bikes, we compared five candidates. The first column is the rank correlation "
              "with daily net outflow, one feature at a time. The second is the coefficient when all five enter one linear model on a "
              "standardised scale. Elevation comes first on both: a correlation of 0.40 and a coefficient of 0.33, three times larger than any "
              "other. Distance to the subway and land-use zone hardly matter. The model explains only 15% of the variation, so we use it to rank "
              "the features, not to predict. Let us look at elevation directly."),

    "elev": dict(
        pairs=[("below 20 m: these stations gain bikes; 38% of them end the day short", "below 20 m: these stations gain bikes on average; 38% end the day short"),
               ("20–40 m: about even; 56% end short", "20–40 m: roughly balanced; 56% end the day short"),
               ("All 143 stations at 50 m or higher lose bikes.", "Every one of the 143 stations at 50 m or higher loses bikes.")],
        aside="This is our core figure. Each dot is a station, with elevation across and daily net outflow up, as a share of its docks. "
              "Below 20 metres, stations gain bikes on average, 15% of their docks a day. Between 20 and 40 metres they are roughly balanced. "
              "At 40 metres and above, they lose 42% of their docks every day, and 91% of them end the day short. Every one of the 143 stations "
              "above 50 metres loses bikes. The red LOESS curve sits just below zero on low ground, crosses zero at about 25 metres and reaches "
              "around plus 50% by 60 metres. We stop the curve at 80 metres, where there are too few stations."),

    "stmap": dict(
        title="On the map, the stations that lose bikes sit on the hills",
        aside="Here is the same pattern on the map. First, the terrain: the shaded areas are ground 50 metres or higher. Now we add the "
              "stations that lose more than 10% of their docks every day, in red. They sit on the shaded hills: the northern foothills, "
              "Gwanak, and the hills of Seodaemun, Seongbuk and Jongno. The bars on the right say the same with numbers: below 15 metres, "
              "39% of stations end the day short; at 50 metres and above, every one of them does. Finally, the stations that gain bikes, in "
              "blue, line the Han River, its streams and the flat business areas. So elevation matters. The next question is how. Where do "
              "the bikes go?"),

    "vec": dict(
        title="Bikes flow downhill: people ride down but rarely ride back up",
        pairs=[("of flow where the ground slopes; 7% uphill (morning: 59% vs 12%)", "of net flow on sloping ground, against 7% uphill (morning: 59% vs 12%)"),
               ("among the 120 biggest flows in the hills of Seodaemun, Jongno and Seongbuk", "of the 120 largest flows in the hills of Seodaemun, Jongno and Seongbuk")],
        aside="To see how, we turned every trip into a flow map. For each pair of places we take the trips from A to B minus the trips from B "
              "to A, and sum them into one arrow per square kilometre, drawn over the terrain. Darker ground is higher. Then we colour each "
              "arrow by whether it points downhill or uphill. On sloping ground, 69% of the net flow runs downhill and only 7% uphill. Zoom in "
              "on Seodaemun, Jongno and Seongbuk, which combine hills and many commuters: of the 120 largest net flows between neighbourhoods, "
              "58% run downhill and just 1% uphill. People ride down and make the trip back some other way, so the bikes stay at the bottom."),

    "hypo": dict(
        eyebrow="WHAT THIS MEANS FOR THE TRUCKS",
        title="Does every hill-top station need a truck every morning?",
        pairs=[("Many stations are emptied by the 7–9 am commute.", "Many stations are emptied during the 7–9 am commute."),
               ("But if residents ride back in the evening, the station refills itself by night, and no truck is needed.",
                "But if residents ride back in the evening, the station refills by night and needs no truck."),
               ("Split stations on two questions: emptied in the morning? Still short at night?",
                "So we ask two questions of every station: is it emptied in the morning, and is it still short at night?")],
        aside="What does this mean for the trucks? Should a truck rush to every station that is emptied in the morning? Not necessarily. "
              "If residents ride back home in the evening, the station refills by night and needs no truck. We call this the self-balancing "
              "hypothesis. To test it, we ask two questions of every station: is it emptied in the morning, and is it still short at the end "
              "of the day?"),

    "quad": dict(
        title="Two questions sort the stations into four groups",
        pairs=[('<p class="stat-num">893 | 703</p><p class="stat-lab">G1 never refilled | G2 refills itself, the trucks’ real target vs a false alarm</p>',
                '<p class="stat-num">893 vs 703</p><p class="stat-lab">G1 stays short and needs a truck; G2 refills by night and does not</p>'),
               ("stations are emptied in the morning. Why does only half refill?", "stations are emptied in the morning. Why does only half of them recover?"),
               ("stations, each placed by its two answers", "stations, each sorted by its two answers")],
        aside="Here are the two questions as a grid. The columns ask whether a station is emptied during the morning commute; the rows ask "
              "whether it is still short at the end of the day. Stations within 10% of their docks on both counts are balanced. Top right is G1, "
              "which stays short: 893 stations, 31%. Bottom right is G2, which refills by night: 703. Bottom left is G3, which collects bikes "
              "all day, and top left is G4, an office hub that fills in the morning and empties during the day. Each tile also shows a typical "
              "day for its group: up means bikes leave, down means bikes arrive. Now look at the right column: 1,596 stations lose bikes every "
              "morning. About half of them get their bikes back by night, and the other half never do. Why?"),

    "tmap": dict(
        title="Each group occupies its own part of the city",
        pairs=[('<p class="stat-num">G1 Never refilled</p><p class="stat-lab">893 stations, 31%: all over, densest on hillsides</p>',
                '<p class="stat-num">G1 Stays short</p><p class="stat-lab">893 stations, 31%: across the city, densest on hillsides</p>'),
               ('>G2 Refills itself</p><p class="stat-lab">703, 25%: flat residential areas</p>', '>G2 Refills by night</p><p class="stat-lab">703, 25%: flat residential areas</p>'),
               ('>G3 Piles up</p><p class="stat-lab">533, 19%: streams and low ground</p>', '>G3 Collects bikes</p><p class="stat-lab">533, 19%: along streams and on low ground</p>'),
               ('>G4 Daytime hub</p><p class="stat-lab">424, 15%: business districts</p>', '>G4 Office hub</p><p class="stat-lab">424, 15%: business districts</p>')],
        aside="On the map, each group occupies its own part of the city. G1, which stays short, sits on the hills: the northern foothills, "
              "Gwanak, Seodaemun and Eunpyeong. In Seodaemun, 60% of the stations that are not balanced are G1, the highest share of any "
              "district. G2, which refills by night, is found in flat residential areas such as Nowon, Gangdong and Songpa. G3, which collects "
              "bikes, lines the streams: Jungnangcheon, Anyangcheon and Tancheon. G4 sits in the business districts: Yeouido, Gwanghwamun and "
              "the Guro Digital Complex."),

    "g12": dict(
        title="Same morning, different evening: the difference is the hill",
        pairs=[("net return to a G1 station: the ride back up does not happen", "net return to a G1 station: few people ride back up"),
               ("median elevation, G1 vs G2. Subway distance: 500 m vs 470 m", "median elevation of G1 and G2; distance to the subway is similar (500 m vs 470 m)")],
        aside="To see why, we compare the two groups hour by hour. G2, in orange: bikes leave in the morning and the evening commute brings "
              "them back, so by night the station is full again. G1, in red: the same morning drain, but only a trickle comes back in the "
              "evening, about 1.3 bikes per station against 5.7 for G2. What separates them? Elevation. G1 stations sit at a median of 28 "
              "metres, G2 stations at 19. Distance to the subway is almost the same, 500 against 470 metres. People ride down to the station "
              "in the morning, and in the evening few of them ride back up the hill."),

    "when": dict(
        title="The hills are refilled every day, but not before the morning rush",
        pairs=[("bikes a day riders take from stations at 40 m and above", "bikes a day that riders take from stations at 40 m and above"),
               ("bikes a day put back there by other moves, mostly rebalancing", "bikes a day returned there by other moves, mostly trucks"),
               ("correlation of stock change and rides at 7 to 9 am: almost no refilling in the peak",
                "correlation of stock change with rides at 7–9 am: almost no refilling in the peak"),
               ("of commute hours those stations still have zero bikes", "of commute hours in which those stations have no bikes")],
        aside="Trip records do not show the trucks. So we also took the hourly stock at every station and matched it with the trips: "
              "whatever the rides do not explain is other moves, mostly trucks. Below 20 metres, riders bring in about one bike a day and "
              "other moves take about one away. At 40 metres and above, riders take away about four bikes a day and other moves bring almost "
              "exactly four back. So trucks already go up the hills every day. But between 7 and 9 am, stock moves almost exactly with the "
              "rides, a correlation of 0.99. Almost nothing is refilled during the peak, and those hill-top stations still have no bikes in "
              "28% of commute hours. The question is not only where the trucks go, but when."),

    "conclusion": dict(
        title="Get bikes up the hills before the morning rush, and leave alone the stations that refill themselves",
        pairs=[("Bikes roll downhill in the morning and are not ridden back up: net flow runs downhill 69% of the time where the ground slopes.",
                "Bikes roll downhill in the morning and are not ridden back up: 69% of net flow on sloping ground runs downhill."),
               ("An empty station at 9 am is not always a problem. 703 stations (G2) refill themselves by night.",
                "An empty station at 9 am is not always a problem: 703 stations (G2) refill on their own by night."),
               ("The hills already get bikes back every day, yet stay empty in 28% of commute hours: the refill does not arrive before the peak.",
                "The hills are refilled every day, yet stay empty in 28% of commute hours, because the refill does not come before the rush."),
               ("Refill the 893 hill-top G1 stations before 7 am, with bikes from the 533 low-lying G3 stations. And do not merge low-use stations on ride counts alone: half the hill-top merge candidates already run empty.",
                "Refill the 893 hill-top G1 stations before 7 am, using bikes from the 533 low-lying G3 stations. And do not merge stations on ride counts alone: half of the hill-top merge candidates are already empty in the morning.")],
        aside="To sum up. Bikes roll downhill in the morning and are not ridden back up. Because of that, an empty station at 9 am is not "
              "always a problem: 703 stations get their bikes back by night without any help. The stations that really need a truck are the "
              "893 G1 stations on the hills, and they are already refilled every day, just not before the morning rush. So the plan is about "
              "timing: take bikes from the 533 G3 stations on low ground, which collect bikes all day, and have them on the hills before 7 am. "
              "One more point for the debate about cutting the system: if you merge the least-used stations on ride counts alone, half of the "
              "hill-top candidates are stations that are already empty in the morning. Their low use may mean no bikes, not no demand."),

    "limits": dict(
        pairs=[("Trucks appear only as the stock change that rides do not explain: we do not see when each truck comes.",
                "Trucks are visible only as stock changes that rides do not explain, so we cannot tell when each truck arrives."),
               ("A station that runs empty records no rentals, so demand on the hills is likely higher than we see.",
                "An empty station records no rentals, so demand on the hills is probably higher than we see."),
               ("Weekdays without rain only: weekends and rainy days need their own study.",
                "We looked only at dry weekdays; weekends and rainy days need their own analysis."),
               ("We describe patterns; we do not estimate the cost a new truck plan would save.",
                "We describe patterns; we do not estimate how much a new truck schedule would save.")],
        aside="Some limits. First, we see the trucks only indirectly, as the change in stock that rides do not explain, so we cannot tell "
              "when each truck arrives. Second, an empty station records no rentals, so demand on the hills is probably higher than our "
              "numbers show. Third, we looked only at dry weekdays. And fourth, this is an exploratory study: we describe the pattern, but we "
              "do not estimate how much a new truck schedule would save."),

    "thanks": dict(
        pairs=[('<p class="byline">Group 1 · STA3115 Exploratory Data Analysis · Data: Seoul Open Data, KMA, Seoul digital topographic map</p>',
                '<p class="byline">Group 1, STA3115 Exploratory Data Analysis. Data: Seoul Open Data, KMA, Seoul digital topographic map</p>')],
        aside="Thank you for listening. We are happy to take questions."),

    "appendix": dict(
        title="Backup slides for questions",
        pairs=[("Season pass vs day pass, weekdays vs weekends", "Season passes vs day passes, weekdays vs weekends")],
        aside="Backup slides for questions."),

    "a_pass": dict(
        title="Season-pass holders on weekdays make the commute peaks",
        aside="If asked who makes the commute peaks: season-pass holders on weekdays, with peaks at 8 am and 6 pm. Day-pass riders on "
              "weekends show a single afternoon peak. Season passes account for about 83% of all rides."),

    "a_inc": dict(
        title="District income does not explain how much stations are used",
        pairs=[("Only 25 districts, and a district-level correlation says nothing about individual riders.",
                "With only 25 districts, a district-level correlation says nothing about individual riders.")],
        aside="If asked about income: across the 25 districts, average income and rentals per station are unrelated, with a Spearman "
              "correlation of 0.05 and a permutation p-value of 0.81. Gangnam and Seocho are the richest districts but sit in the middle "
              "for use per station."),
}

# step cues (speaker notes overlay) and labels inside the charts
JS = GROUPS + [
    ("'Rides grew to 44.9 million in 2023, then fell two years in a row: 37.4 million in 2025, 14.8% fewer than 2024.'",
     "'Rides grew to 44.9 million in 2023, then fell two years in a row, to 37.4 million in 2025: 14.8% fewer than in 2024.'"),
    ("'Meanwhile the operating deficit grew, from 9.4 billion won in 2022 to 17.6 billion won in 2025.'",
     "'Over the same years the operating deficit grew, from 9.4 billion won in 2022 to 17.6 billion won in 2025.'"),
    ("'Weekdays: two sharp peaks, 8 am and 6 pm. That is commuting.'", "'Weekdays: two sharp peaks at 8 am and 6 pm. That is commuting.'"),
    ("'Weekends and holidays: one soft hill in the afternoon. No commute pattern.'", "'Weekends and holidays: one broad afternoon peak, with no commute pattern.'"),
    ("'So from here on: weekdays, and the two commute windows.'", "'From here on we study weekdays and the two commute windows.'"),
    ("'Dry weekdays: rides rise with temperature and dip in the hottest weeks. The points hug the LOESS curve.'",
     "'Dry weekdays: rides rise with temperature and dip in the hottest weeks. The points stay close to the LOESS curve.'"),
    ("'Rainy weekdays: far fewer rides, and the points scatter widely.'", "'Rainy weekdays: far fewer rides, and the points scatter widely.'"),
    ("'Residuals: rainy days are three times as noisy, and the noise grows with temperature. Temperature alone cannot explain them.'",
     "'Residuals: rainy days vary three times as much, and more so when it is warm. Temperature alone cannot explain them.'"),
    ("'Rentals per station at each hour. Drag the slider: the whole city lights up at 8 am and 6 pm.'",
     "'Rentals per station in each hour. Drag the slider: every district peaks at 8 am and 6 pm.'"),
    ("'Over the whole day the colours do not cancel out. That leftover is what the trucks have to move.'",
     "'Over the whole day the colours do not cancel out. What is left over is what the trucks have to move.'"),
    ("'G1, never refilled: all over the city, but densest on the hillsides.'", "'G1, stays short: across the city, but densest on the hillsides.'"),
    ("'G2, refills itself: flat residential areas.'", "'G2, refills by night: flat residential areas.'"),
    ("'G3, piles up: along the streams and the low ground.'", "'G3, collects bikes: along the streams and on low ground.'"),
    ("'G4, daytime hub: the business districts.'", "'G4, office hub: the business districts.'"),
    ("'G2, refills itself: bikes leave in the morning, and the evening commute brings them back.'",
     "'G2, refills by night: bikes leave in the morning, and the evening commute brings them back.'"),
    ("'G1, never refilled: the same morning drain, but in the evening only a trickle comes back.'",
     "'G1, stays short: the same morning drain, but only a trickle comes back in the evening.'"),
]
