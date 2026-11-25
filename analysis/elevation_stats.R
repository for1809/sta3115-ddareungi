# Station elevation statistics, all 2,736 stations in the frozen station list (data/stations.csv).
# Three elevation sources: bare earth from the Seoul 1:5,000 contours (elev_bare_m, used in the final deck's terrain slides),
# Copernicus DEM 30 m (elev30_m) and Open-Meteo / Copernicus 90 m (elev_m). Stations active in 2025: months_active > 0.
# Run: Rscript analysis/elevation_stats.R > analysis/elevation_stats_log.txt
# Output: the log only; per-station values are in data/station_master.csv
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)

st <- rd("data/stations.csv") %>% select(station_no, name, gu, lat, lon, months_active, elev_m) %>%
  left_join(rd("data/station_terrain.csv") %>% select(station_no, elev30_m), by = "station_no") %>%
  left_join(rd("data/station_terrain_bare.csv") %>% select(station_no, elev_bare_m, slope_bare_r300), by = "station_no") %>%
  mutate(active_2025 = months_active > 0)
cat("stations:", nrow(st), " active in 2025:", sum(st$active_2025), "\n")
cat("missing elevation: bare", sum(is.na(st$elev_bare_m)), " 30 m", sum(is.na(st$elev30_m)), " 90 m", sum(is.na(st$elev_m)), "\n\n")

summ <- function(d, v) d %>% summarise(n = sum(!is.na(.data[[v]])), mean = mean(.data[[v]], na.rm = TRUE), sd = sd(.data[[v]], na.rm = TRUE),
  min = min(.data[[v]], na.rm = TRUE), p10 = quantile(.data[[v]], .1, na.rm = TRUE), q1 = quantile(.data[[v]], .25, na.rm = TRUE),
  median = median(.data[[v]], na.rm = TRUE), q3 = quantile(.data[[v]], .75, na.rm = TRUE), p90 = quantile(.data[[v]], .9, na.rm = TRUE),
  max = max(.data[[v]], na.rm = TRUE)) %>% mutate(across(where(is.double), ~ round(.x, 1)))
act <- filter(st, active_2025)
cat("== summary, stations active in 2025 (m) ==\n")
print(bind_rows(bare_earth = summ(act, "elev_bare_m"), cop30 = summ(act, "elev30_m"), cop90 = summ(act, "elev_m"), .id = "source"), width = 200)
cat("\ncorrelation between sources: bare vs 30 m", round(cor(act$elev_bare_m, act$elev30_m), 3),
    "; bare vs 90 m", round(cor(act$elev_bare_m, act$elev_m), 3), "; 30 m vs 90 m", round(cor(act$elev30_m, act$elev_m), 3), "\n")

cat("\n== stations by bare-earth elevation band (active in 2025) ==\n")
print(act %>% mutate(band = cut(elev_bare_m, c(-Inf, 15, 25, 35, 50, 100, Inf), right = FALSE,
                                labels = c("below 15 m", "15-25 m", "25-35 m", "35-50 m", "50-100 m", "100 m and above"))) %>%
        count(band) %>% mutate(share = round(100 * n / sum(n), 1), cum = cumsum(share)))
cat("\n== bands used in the analysis (bare earth) ==\n")
print(act %>% mutate(band = cut(elev_bare_m, c(-Inf, 20, 40, Inf), right = FALSE, labels = c("below 20 m", "20-40 m", "40 m and above"))) %>%
        count(band) %>% mutate(share = round(100 * n / sum(n), 1)))

cat("\n== highest 10 stations (bare earth) ==\n")
print(act %>% arrange(desc(elev_bare_m)) %>% slice(1:10) %>% select(station_no, name, gu, elev_bare_m, elev30_m, elev_m))
cat("\n== lowest 5 ==\n")
print(act %>% arrange(elev_bare_m) %>% slice(1:5) %>% select(station_no, name, gu, elev_bare_m, elev30_m, elev_m))

gu <- act %>% group_by(gu) %>% summarise(stations = n(), mean_m = round(mean(elev_bare_m), 1), median_m = round(median(elev_bare_m), 1),
  max_m = round(max(elev_bare_m), 1), share_40m_plus = round(100 * mean(elev_bare_m >= 40), 1), .groups = "drop") %>% arrange(desc(median_m))
cat("\n== by district (bare earth, active in 2025), highest median first ==\n")
print(gu, n = Inf)
