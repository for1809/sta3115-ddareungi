# Slide "STEP 7. WHEN" in the final deck uses the teammate deck's elevation (Seoul 1:5,000 contours, bare earth),
# so the riders vs other moves split and the morning shortage are recomputed here by bare-earth elevation band.
# Run from the project root:  Rscript analysis/rebalance_bare.R > analysis/rebalance_bare_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
st <- rd("data/stations.csv") %>% filter(use_day > 0) %>% select(station_no, elev_m) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty = am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no, elev_bare_m), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no), by = "station_no") %>%
  filter(!is.na(am_empty)) %>%
  left_join(rd("data/station_2x2.csv") %>% filter(days_dry >= 30) %>%
              transmute(station_no, riders = -day_out_trip_dry, other = other_in_day_dry,
                        am_inv = am_out_inv_dry, am_trip = am_out_trip_dry), by = "station_no")
cat("stations", nrow(st), "; cor(90 m grid, bare-earth elevation) =", round(cor(st$elev_m, st$elev_bare_m), 3), "\n")
for (v in c("elev_m", "elev_bare_m")) {
  cat("\n==== bands by", v, "====\n")
  print(st %>% mutate(band = cut(.data[[v]], c(-Inf, 20, 40, Inf), right = FALSE,
                                 labels = c("Below 20 m", "20-40 m", "40 m and above"))) %>%
          group_by(band) %>%
          summarise(stations = n(), shortage = round(mean(am_empty), 4), with_split = sum(!is.na(riders)),
                    drained = round(mean(riders < 0, na.rm = TRUE), 3),   # before riders is overwritten by its mean
                    riders = round(mean(riders, na.rm = TRUE), 2), other = round(mean(other, na.rm = TRUE), 2),
                    .groups = "drop"), width = 200)
}
d <- st %>% filter(!is.na(am_inv))
cat("\ncorrelation of 07-09 h stock change with rides:", round(cor(d$am_inv, d$am_trip), 3), "\n")

# merge candidates (bottom 20% of use, another station within 300 m) by bare-earth band, for the conclusion
mc <- rd("data/stations.csv") %>% filter(use_day > 0) %>% select(station_no, use_day, nearest_station_m) %>%
  inner_join(st %>% select(station_no, am_empty, elev_bare_m), by = "station_no")
q20 <- sort(mc$use_day)[floor(nrow(mc) * 0.2) + 1]
cat("\nmerge candidates by bare-earth band (q20 =", q20, "rides a day):\n")
print(mc %>% filter(use_day <= q20, nearest_station_m <= 300) %>%
        mutate(band = cut(elev_bare_m, c(-Inf, 20, 40, Inf), right = FALSE, labels = c("Below 20 m", "20-40 m", "40 m and above"))) %>%
        group_by(band) %>% summarise(candidates = n(), often_empty = sum(am_empty >= 0.3), share = round(often_empty / candidates, 3)))
