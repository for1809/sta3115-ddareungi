# Compare terrain variables as predictors of the morning shortage (Y3 >= 0.3).
# Run from the project folder: Rscript analysis/terrain_compare.R > analysis/terrain_compare_log.txt
# Preliminary: Y3 here still uses all 2025 weekdays (rainy days not yet excluded).
suppressPackageStartupMessages(library(tidyverse))
s <- read_csv("data/stations.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  filter(months_active > 0) %>%
  inner_join(read_csv("data/station_terrain.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE), by = "station_no") %>%
  mutate(gap = as.integer(am_empty >= 0.3), l_sub = log2(subway_m), l_uni = log2(univ_m))
cat("n =", nrow(s), "\n\nsteepest at the station point (check for building artifacts):\n")
print(s %>% arrange(desc(slope_pt)) %>% select(name, gu, elev_m, elev30_m, slope_pt, slope_r100, slope_r300, am_empty) %>% head(12), width = 200)
cat("\nlargest |elev30 - elev90| (DEM disagreement):\n")
print(s %>% mutate(d = elev30_m - elev_m) %>% arrange(desc(abs(d))) %>% select(name, gu, elev_m, elev30_m, d) %>% head(8), width = 200)
cat("\nspearman with am_empty:\n")
print(round(sapply(s[c("elev_m","elev30_m","slope_pt","slope_r100","slope_r300","tpi_500")], function(v) cor(v, s$am_empty, method = "spearman")), 3))
cat("\nlogistic, one terrain variable + l_sub + l_uni (lower AIC = better):\n")
base <- "gap ~ l_sub + l_uni"
for (v in c("elev_m","elev30_m","slope_pt","slope_r100","slope_r300","tpi_500")) {
  f <- glm(as.formula(paste(base, "+ scale(", v, ")")), family = binomial, data = s)
  cat(sprintf("%-11s AIC %.1f  OR per 1 SD %.2f\n", v, AIC(f), exp(coef(f)[4])))
}
f <- glm(gap ~ scale(elev_m) + scale(slope_r300) + l_sub + l_uni, family = binomial, data = s)
cat("\nelev_m and slope_r300 together (OR per 1 SD):\n"); print(round(exp(cbind(OR = coef(f), confint.default(f)))[2:3, ], 2))
cat("AIC", round(AIC(f), 1), "\n")
