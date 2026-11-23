# Slide 10 example. Find real station pairs on the same steep hill: one near the top, one near the foot.
suppressPackageStartupMessages(library(tidyverse))
# Run from the project root: Rscript slides/station_pair.R > slides/station_pair_log.txt
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
s <- rd("data/stations.csv") %>% filter(use_day > 0) %>%
  select(station_no, name, gu, lat, lon, elev_m, use_day, docks) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty_dry, am_snapshots_dry, dry_am_days), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no, elev_bare_m, slope = slope_bare_r300), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no, climb = climb_bare_all), by = "station_no")
cat("stations:", nrow(s), "\n")
q <- quantile(s$slope, c(.5, .75, .9)); print(round(q, 2))
cat("slope range:", range(s$slope), "\n")
steep <- s %>% filter(slope >= q[2], am_snapshots_dry >= 500)
d <- function(a, b, c, e) { r <- 6371000; p <- pi / 180
  2 * r * asin(sqrt(sin((c - a) * p / 2)^2 + cos(a * p) * cos(c * p) * sin((e - b) * p / 2)^2)) }
pairs <- tidyr::crossing(t = steep$station_no, f = steep$station_no) %>% filter(t != f) %>%
  left_join(steep %>% rename_with(~ paste0("t_", .x)), by = c(t = "t_station_no")) %>%
  left_join(steep %>% rename_with(~ paste0("f_", .x)), by = c(f = "f_station_no")) %>%
  mutate(dist = d(t_lat, t_lon, f_lat, f_lon)) %>%
  filter(dist <= 1000, t_elev_m - f_elev_m >= 30, abs(t_slope - f_slope) <= 1.5,
         t_am_empty_dry >= 0.4, f_am_empty_dry <= 0.05) %>%
  arrange(desc(t_am_empty_dry - f_am_empty_dry))
cat("pairs:", nrow(pairs), "\n")
pairs %>% transmute(top = paste(t, t_name, t_gu), foot = paste(f, f_name, f_gu), dist = round(dist),
                    elev = paste(t_elev_m, f_elev_m), slope = paste(round(t_slope, 1), round(f_slope, 1)),
                    empty = paste(round(t_am_empty_dry, 3), round(f_am_empty_dry, 3)),
                    climb = paste(round(t_climb, 1), round(f_climb, 1)), use = paste(t_use_day, f_use_day)) %>%
  head(25) %>% as.data.frame() %>% print(right = FALSE)
