# Main report numbers recomputed on dry mornings (am_empty_dry from scripts/10_aggregate_dry.py).
# Same definitions as the report: shortage station = am_empty >= 0.3; roles use the yearly use_day thresholds
# (low use = bottom 20%, another station within 300 m), only the shortage part switches to dry mornings.
# Run from the project folder: Rscript analysis/dry_main_numbers.R > analysis/dry_main_numbers_log.txt
suppressPackageStartupMessages({ library(tidyverse); library(broom) })
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
s <- rd("data/stations.csv") %>% filter(months_active > 0) %>%
  inner_join(rd("data/stations_dry.csv"), by = "station_no") %>%
  mutate(gap = as.integer(am_empty_dry >= 0.3), elev10 = elev_m / 10, l_sub = log2(subway_m), l_uni = log2(univ_m),
         band = cut(elev_m, c(0, 20, 40, Inf), labels = c("<20", "20-40", ">=40"), right = FALSE))
cat("stations", nrow(s), "; shortage share (dry mornings)", round(mean(s$gap), 4), "\n\n")
cat("mean dry-morning shortage by band:\n"); print(s %>% group_by(band) %>% summarise(n = n(), am_dry = round(mean(am_empty_dry), 4)))

f1 <- glm(gap ~ elev10 + l_sub + l_uni + docks, family = binomial, data = s)
cat("\nlogistic, no interaction (OR, 95% CI, p):\n")
print(tidy(f1, exponentiate = TRUE, conf.int = TRUE, conf.method = "Wald") %>% mutate(across(where(is.numeric), ~ round(.x, 3))))
ci <- exp(confint.default(f1)); cat("Wald CI:\n"); print(round(ci, 2))
f2 <- glm(gap ~ elev10 * l_sub + l_uni + docks, family = binomial, data = s)
cat("\ninteraction elev10:l_sub p =", signif(summary(f2)$coefficients["elev10:l_sub", 4], 3),
    " coef =", round(coef(f2)["elev10:l_sub"], 3), "\n")

q20 <- sort(s$use_day)[floor(nrow(s) * 0.2) + 1]
q50 <- sort(s$use_day)[floor(nrow(s) * 0.5) + 1]
s <- s %>% mutate(low_near = use_day <= q20 & nearest_station_m <= 300,
                  role = case_when(low_near & gap == 1 ~ "supply_gap_suspect", low_near ~ "consolidate",
                                   gap == 1 ~ "morning_gap",
                                   use_day >= q50 & commute_share >= 0.5 ~ "commute_core", TRUE ~ "other"))
cat("\nthresholds: low use", q20, " median", q50, "\n")
cat("roles (dry mornings):\n"); print(table(s$role))
cand <- filter(s, low_near)
cat("consolidation candidates", nrow(cand), "; supply-gap suspects", sum(cand$gap),
    sprintf("(%.1f%%)", 100 * mean(cand$gap)), "; of which elevation >= 40 m", sum(cand$gap & cand$elev_m >= 40), "\n")
cat("commute core", sum(s$role == "commute_core"), "; of which elevation < 20 m", sum(s$role == "commute_core" & s$elev_m < 20), "\n")
tab <- table(s$role, s$band)
cat("chi-square role x band:\n"); print(chisq.test(tab))

cat("\nthreshold and rain-definition checks, OR per 10 m (90 m elevation):\n")
for (t in c(0.2, 0.3, 0.4)) {
  f <- glm(I(am_empty_dry >= t) ~ elev10 + l_sub + l_uni + docks, family = binomial, data = s)
  cat(sprintf("  dry mornings, threshold %.1f: OR %.2f\n", t, exp(coef(f)[2])))
}
f <- glm(I(am_empty_dryday >= 0.3) ~ elev10 + l_sub + l_uni + docks, family = binomial, data = s)
cat(sprintf("  dry = whole-day rain < 1 mm, threshold 0.3: OR %.2f\n", exp(coef(f)[2])))
