# The team's 2x2 (idea doc, Step 3) rebuilt from data/station_2x2.csv (scripts/15_inventory_2x2.py),
# then compared by elevation, and split into what riders did and what other moves (mostly trucks) did.
# Positive outflow = bikes leave. Run from the project root:
#   Rscript analysis/two_by_two.R > analysis/two_by_two_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
st <- rd("data/stations.csv") %>% filter(use_day > 0) %>% select(station_no, name, gu, elev_m, use_day, docks) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty = am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no), by = "station_no") %>%
  filter(!is.na(am_empty)) %>%
  inner_join(rd("data/station_2x2.csv"), by = "station_no") %>%
  mutate(band = cut(elev_m, c(0, 20, 40, Inf), labels = c("below 20 m", "20-40 m", "40 m+"), right = FALSE))
grp <- function(am, day) case_when(am > 0 & day > 0 ~ "G1 morning out, day out (permanent deficit)",
                                   am > 0 ~ "G2 morning out, day back (self-recovering)",
                                   day > 0 ~ "G3 morning in, day out",
                                   TRUE ~ "G4 morning in, day back")
summ <- function(d, g) d %>% group_by({{ g }}) %>%
  summarise(stations = n(), median_elev = median(elev_m), share_40m = round(mean(elev_m >= 40), 3),
            mean_shortage = round(mean(am_empty), 3), mean_rides = round(mean(use_day), 1),
            riders_day_out = round(mean(day_trip), 2), other_in_day = round(mean(other), 2), .groups = "drop")

for (k in c("dry", "all")) {
  d <- st %>% filter(.data[[paste0("days_", k)]] >= 30) %>%
    transmute(station_no, name, gu, elev_m, band, am_empty, use_day,
              am_inv = .data[[paste0("am_out_inv_", k)]], day_inv = .data[[paste0("day_out_inv_", k)]],
              am_trip = .data[[paste0("am_out_trip_", k)]], day_trip = .data[[paste0("day_out_trip_", k)]],
              other = .data[[paste0("other_in_day_", k)]]) %>%
    mutate(g = grp(am_inv, day_inv))
  cat(sprintf("\n==== inventory 2x2, %s weekdays (stations with >= 30 such days: %d) ====\n",
              ifelse(k == "dry", "dry (< 1 mm all day)", "all"), nrow(d)))
  cat("morning-outflow stations (G1 + G2):", sum(d$am_inv > 0), "\n")
  print(summ(d, g), width = 200)
  if (k == "dry") dry <- d
}

d <- dry
cat("\n==== G1 vs G2 by elevation band (dry) ====\n")
print(d %>% filter(am_inv > 0) %>% count(band, g) %>% group_by(band) %>% mutate(share = round(n / sum(n), 3)) %>% ungroup(), width = 200)
m <- glm(I(g == "G1 morning out, day out (permanent deficit)") ~ I(elev_m / 10), family = binomial, data = d %>% filter(am_inv > 0))
cat("\nlogit P(G1 | morning outflow) on elevation per 10 m: OR",
    round(exp(coef(m)[2]), 2), "95% CI", round(exp(confint.default(m)[2, ]), 2),
    "p", signif(summary(m)$coefficients[2, 4], 2), "\n")

cat("\n==== who refills G2 (dry): riders or other moves ====\n")
g2 <- d %>% filter(g == "G2 morning out, day back (self-recovering)") %>%
  mutate(refill = if_else(day_trip <= 0, "riders bring back at least as many as they take", "riders take more; other moves refill"))
print(g2 %>% group_by(refill) %>% summarise(stations = n(), median_elev = median(elev_m), share_40m = round(mean(elev_m >= 40), 3),
                                            riders_day_out = round(mean(day_trip), 2), other_in_day = round(mean(other), 2), .groups = "drop"), width = 200)

cat("\n==== riders only: trip-based 2x2 (dry), trucks taken out ====\n")
d2 <- d %>% mutate(g = grp(am_trip, day_trip))
print(summ(d2, g), width = 200)
cat("\nby band, share of stations riders drain over the day (trip daily outflow > 0):\n")
print(d %>% group_by(band) %>% summarise(stations = n(), share_riders_drain = round(mean(day_trip > 0), 3),
                                          mean_riders_day_out = round(mean(day_trip), 2), mean_other_in = round(mean(other), 2),
                                          .groups = "drop"))
cat("\ncorrelation of elevation with riders' daily outflow:", round(cor(d$elev_m, d$day_trip), 3),
    "; with other moves (in):", round(cor(d$elev_m, d$other), 3), "\n")
cat("\nexample stations (slide 10):\n")
print(d %>% filter(station_no %in% c("04363", "00533")) %>% select(station_no, name, elev_m, am_inv, day_inv, am_trip, day_trip, other, g), width = 200)

cat("\n==== sanity: inventory vs trips (dry) ====\n")
cat("cor of morning outflow, inventory vs trips:", round(cor(d$am_inv, d$am_trip), 3), "\n")
cat("cor of daily outflow, inventory vs trips:", round(cor(d$day_inv, d$day_trip), 3), "\n")
cat("sum over stations of |other moves| per dry day:", round(sum(abs(d$other))), "bikes\n")
