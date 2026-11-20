# District (gu) level: does flat terrain go with heavy use? 25 districts, descriptive only.
# Terrain = mean over the district's bike stations (bare-earth DEM from the 1:5000 contours, scripts/12_dem_contour.R).
# Use = 2025 weekday rentals per day (departures), total and per station (data/station_hour.csv).
# Run from the project folder: Rscript analysis/gu_terrain.R > analysis/gu_terrain_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
st <- rd("data/stations.csv") %>% filter(months_active > 0) %>%
  inner_join(rd("data/station_terrain_bare.csv"), by = "station_no") %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty_dry), by = "station_no")
dep <- rd("data/station_hour.csv") %>% filter(daytype == "weekday") %>% group_by(station_no) %>%
  summarise(rent_day = sum(dep), rent_am = sum(dep[hour %in% 7:9]), .groups = "drop")
g <- st %>% inner_join(dep, by = "station_no") %>% group_by(gu) %>%
  summarise(stations = n(), rent_day = sum(rent_day), rent_am = sum(rent_am),
            rent_per_station = rent_day / stations,
            elev_bare = mean(elev_bare_m), slope_bare = mean(slope_bare_r300),
            share_flat = mean(slope_bare_r300 < 2), share_high = mean(elev_bare_m >= 40),
            am_empty = mean(am_empty_dry), .groups = "drop") %>%
  arrange(desc(rent_day))
cat("districts:", nrow(g), "\n\n")
print(g %>% mutate(across(where(is.double), ~ round(.x, 2))), n = 25, width = 200)
cat("\nspearman correlations across 25 districts:\n")
vars <- c("elev_bare", "slope_bare", "share_flat", "share_high")
for (y in c("rent_day", "rent_per_station", "am_empty")) {
  cat(sprintf("%-17s", y), paste(sprintf("%s %+.2f (p %.3f)", vars, sapply(vars, function(v) cor(g[[v]], g[[y]], method = "spearman")),
                                          sapply(vars, function(v) suppressWarnings(cor.test(g[[v]], g[[y]], method = "spearman"))$p.value)), collapse = "  "), "\n")
}
cat("\nstation count vs total rentals (spearman):", round(cor(g$stations, g$rent_day, method = "spearman"), 2), "\n")
cat("top 3 by total rentals:", paste(head(g$gu, 3), collapse = ", "), "\n")
cat("their mean slope:", round(mean(head(g$slope_bare, 3)), 2), " others:", round(mean(g$slope_bare[-(1:3)]), 2), "\n")
f <- lm(log(rent_per_station) ~ slope_bare, data = g)
cat(sprintf("log(rentals per station) ~ slope: %+.1f%% per 1 degree (p %.3f, R2 %.2f)\n",
            (exp(coef(f)[2]) - 1) * 100, summary(f)$coefficients[2, 4], summary(f)$r.squared))
write_csv(g, "data/gu_terrain.csv")
