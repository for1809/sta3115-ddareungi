# Terrain variables without buildings: bare-earth elevation and slope from the 1:5000 contours
# (scripts/12_dem_contour.R) and climb from station-pair trip counts (scripts/13_od_pairs.py),
# compared with the Copernicus surface-model versions. Outcome: dry-morning shortage (am_empty_dry >= 0.3).
# Run from the project folder: Rscript analysis/bare_compare.R > analysis/bare_compare_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character(), origin = col_character(), dest = col_character()),
                           show_col_types = FALSE)
st <- rd("data/stations.csv") %>% filter(months_active > 0) %>%
  inner_join(rd("data/station_terrain.csv"), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv"), by = "station_no") %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty_dry, pm_empty_dry, climb_in_m), by = "station_no")

# climb from pair counts, for both elevation sources; round trips (same station) kept or dropped
pairs <- rd("raw/derived/od_pairs_weekday_2025.csv")
cat("pairs", nrow(pairs), " trips", sum(pairs$trips), " round trips share",
    round(sum(pairs$trips[pairs$origin == pairs$dest]) / sum(pairs$trips), 4), "\n")
el <- st %>% select(station_no, elev30_m, elev_bare_m)
pe <- pairs %>% inner_join(el, by = c("origin" = "station_no")) %>% inner_join(el, by = c("dest" = "station_no"), suffix = c("_o", "_d"))
climb <- function(df, col_d, col_o) df %>% group_by(dest) %>%
  summarise(v = sum(trips * (.data[[col_d]] - .data[[col_o]])) / sum(trips), .groups = "drop")
c_bare_all <- climb(pe, "elev_bare_m_d", "elev_bare_m_o") %>% rename(climb_bare_all = v)
c_bare <- climb(filter(pe, origin != dest), "elev_bare_m_d", "elev_bare_m_o") %>% rename(climb_bare = v)
c_cop <- climb(filter(pe, origin != dest), "elev30_m_d", "elev30_m_o") %>% rename(climb_cop_noround = v)
d <- st %>% left_join(c_bare_all, by = c("station_no" = "dest")) %>% left_join(c_bare, by = c("station_no" = "dest")) %>%
  left_join(c_cop, by = c("station_no" = "dest")) %>%
  mutate(gap = as.integer(am_empty_dry >= 0.3), l_sub = log2(subway_m), l_uni = log2(univ_m)) %>%
  filter(!is.na(am_empty_dry), !is.na(elev_bare_m), !is.na(climb_bare), !is.na(climb_in_m))
cat("stations used", nrow(d), "\n")
cat("check: climb from pairs with round trips (Copernicus) vs climb_in_m from 10_aggregate_dry:",
    round(cor(climb(pe, "elev30_m_d", "elev30_m_o")$v[match(d$station_no, climb(pe, "elev30_m_d", "elev30_m_o")$dest)], d$climb_in_m), 4), "\n")

cat("\n== elevation by source ==\n")
print(summary(d %>% select(elev_m, elev30_m, elev_bare_m, slope_r300, slope_bare_r300, climb_in_m, climb_bare)))
cat("\ncorrelations:\n")
vars <- c("elev_m", "elev30_m", "elev_bare_m", "slope_r300", "slope_bare_r300", "climb_in_m", "climb_bare_all", "climb_bare")
print(round(cor(d[vars]), 2))

cat("\n== dry-morning shortage by bare-earth elevation band ==\n")
print(d %>% mutate(band = cut(elev_bare_m, c(-Inf, 20, 40, Inf), right = FALSE)) %>% group_by(band) %>%
        summarise(n = n(), am = round(mean(am_empty_dry), 4), pm = round(mean(pm_empty_dry, na.rm = TRUE), 4)))

cat("\n== one terrain variable at a time (controls: subway, university) ==\n")
base <- "gap ~ l_sub + l_uni"
cat(sprintf("%-26s AIC %.1f\n", "(no terrain)", AIC(glm(as.formula(base), family = binomial, data = d))))
lab <- c(elev_m = "elevation 90 m (Open-Meteo)", elev30_m = "elevation Copernicus 30 m", elev_bare_m = "elevation bare (contours)",
         slope_r300 = "slope r300 Copernicus", slope_bare_r300 = "slope r300 bare",
         climb_in_m = "climb Copernicus (+round)", climb_bare_all = "climb bare (+round)", climb_bare = "climb bare (no round)")
for (v in vars) {
  f <- glm(as.formula(paste(base, "+ scale(", v, ")")), family = binomial, data = d)
  ci <- exp(confint.default(f)[4, ])
  cat(sprintf("%-26s AIC %.1f  OR per 1 SD %.2f (%.2f-%.2f)\n", lab[v], AIC(f), exp(coef(f)[4]), ci[1], ci[2]))
}
for (pair in list(c("elev_bare_m", "slope_bare_r300"), c("elev_bare_m", "climb_bare"), c("elev30_m", "climb_in_m"))) {
  f <- glm(as.formula(paste(base, "+ scale(", pair[1], ") + scale(", pair[2], ")")), family = binomial, data = d)
  cat(sprintf("\n%s + %s: AIC %.1f\n", pair[1], pair[2], AIC(f)))
  print(round(exp(cbind(OR = coef(f), confint.default(f)))[4:5, ], 2))
}
f <- glm(gap ~ I(elev_bare_m / 10) + l_sub + l_uni, family = binomial, data = d)
cat(sprintf("\nbare elevation, OR per 10 m: %.2f (%.2f-%.2f)\n", exp(coef(f)[2]), exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))
write_csv(d %>% select(station_no, climb_bare, climb_bare_all), "data/station_climb_bare.csv")
