# Checks data/stations_dry.csv (scripts/10_aggregate_dry.py) and compares terrain variables on dry weekdays.
# Run from the project folder: Rscript analysis/dry_compare.R > analysis/dry_compare_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
s <- rd("data/stations.csv") %>% filter(months_active > 0) %>%
  inner_join(rd("data/station_terrain.csv"), by = "station_no") %>%
  inner_join(rd("data/stations_dry.csv"), by = "station_no") %>%
  mutate(l_sub = log2(subway_m), l_uni = log2(univ_m))
cat("stations:", nrow(s), "\n")

cat("\n== 1. checks ==\n")
cat("am_empty_all vs the yearly am_empty in stations.csv: max abs diff",
    round(max(abs(s$am_empty_all - s$am_empty), na.rm = TRUE), 4), "\n")
cat("missing per column:\n"); print(colSums(is.na(s[c("am_empty_dry", "pm_empty_dry", "climb_in_m", "drop_am_out_m", "use_commute_dry")])))
cat("dry-morning snapshots per station:\n"); print(summary(s$am_snapshots_dry))
cat("stations with fewer than 300 dry-morning snapshots:\n")
print(s %>% filter(am_snapshots_dry < 300) %>% select(name, gu, am_snapshots_dry, dry_am_days), n = 30)
cat("distance to the nearest AWS station (m):\n"); print(summary(s$aws_m))
cat("summary of new variables:\n")
print(summary(s %>% select(am_empty_all, am_empty_dry, pm_empty_all, pm_empty_dry, use_commute_dry, climb_in_m, drop_am_out_m)))

cat("\n== 2. does dropping rainy days change the morning shortage? ==\n")
cat("mean am_empty all weekdays", round(mean(s$am_empty_all, na.rm = TRUE), 4),
    " dry mornings", round(mean(s$am_empty_dry, na.rm = TRUE), 4), "\n")
cat("correlation all vs dry:", round(cor(s$am_empty_all, s$am_empty_dry, use = "complete"), 4), "\n")
cat("share with am_empty >= 0.3: all", round(mean(s$am_empty_all >= 0.3, na.rm = TRUE), 4),
    " dry", round(mean(s$am_empty_dry >= 0.3, na.rm = TRUE), 4), "\n")
cat("by elevation band (dry mornings):\n")
print(s %>% mutate(band = cut(elev_m, c(0, 20, 40, Inf), right = FALSE)) %>% group_by(band) %>%
        summarise(n = n(), am_all = mean(am_empty_all, na.rm = TRUE), am_dry = mean(am_empty_dry, na.rm = TRUE),
                  pm_dry = mean(pm_empty_dry, na.rm = TRUE), climb = mean(climb_in_m, na.rm = TRUE)))

cat("\n== 3. which terrain variable explains the dry-morning shortage best? ==\n")
d <- s %>% filter(!is.na(am_empty_dry), !is.na(climb_in_m), !is.na(drop_am_out_m)) %>%
  mutate(gap = as.integer(am_empty_dry >= 0.3))
cat("n =", nrow(d), " gap share", round(mean(d$gap), 4), "\n")
cat("spearman with am_empty_dry:\n")
vars <- c("elev_m", "elev30_m", "slope_r300", "tpi_500", "climb_in_m", "drop_am_out_m")
print(round(sapply(d[vars], function(v) cor(v, d$am_empty_dry, method = "spearman")), 3))
cat("correlation among terrain variables:\n"); print(round(cor(d[vars]), 2))
base <- "gap ~ l_sub + l_uni + docks"
for (v in vars) {
  f <- glm(as.formula(paste(base, "+ scale(", v, ")")), family = binomial, data = d)
  ci <- exp(confint.default(f)[5, ])
  cat(sprintf("%-14s AIC %.1f  OR per 1 SD %.2f (%.2f-%.2f)\n", v, AIC(f), exp(coef(f)[5]), ci[1], ci[2]))
}
f0 <- glm(as.formula(base), family = binomial, data = d); cat(sprintf("%-14s AIC %.1f\n", "(no terrain)", AIC(f0)))
for (pair in list(c("elev30_m", "climb_in_m"), c("elev30_m", "drop_am_out_m"), c("elev30_m", "slope_r300"))) {
  f <- glm(as.formula(paste(base, "+ scale(", pair[1], ") + scale(", pair[2], ")")), family = binomial, data = d)
  o <- exp(cbind(coef(f), confint.default(f)))[5:6, ]
  cat(sprintf("\n%s + %s: AIC %.1f\n", pair[1], pair[2], AIC(f))); print(round(o, 2))
}
cat("\nthreshold check, elev30 OR per 10 m on dry mornings:\n")
for (t in c(0.2, 0.3, 0.4)) {
  f <- glm(I(am_empty_dry >= t) ~ I(elev30_m / 10) + l_sub + l_uni + docks, family = binomial, data = d)
  cat(sprintf("  threshold %.1f: share %.3f  OR %.2f\n", t, mean(d$am_empty_dry >= t), exp(coef(f)[2])))
}
f <- glm(I(am_empty_dryday >= 0.3) ~ I(elev30_m / 10) + l_sub + l_uni + docks, family = binomial, data = d)
cat(sprintf("  dry by whole-day rain < 1 mm instead: OR %.2f\n", exp(coef(f)[2])))
f <- glm(gap ~ I(elev_m / 10) + l_sub + l_uni + docks, family = binomial, data = d)
cat(sprintf("  same model as the report (90 m elevation): OR %.2f (%.2f-%.2f)\n", exp(coef(f)[2]),
            exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))

cat("\n== 4. evening shortage (17-19 h, dry evenings) ==\n")
cat("spearman with pm_empty_dry:\n")
print(round(sapply(d[c(vars, "l_sub", "l_uni", "docks", "commute_share")], function(v) cor(v, d$pm_empty_dry, method = "spearman", use = "complete")), 3))
cat("share with pm_empty_dry >= 0.3:", round(mean(d$pm_empty_dry >= 0.3, na.rm = TRUE), 4), "\n")
cat("top 10 evening-shortage districts (mean pm_empty_dry):\n")
print(d %>% group_by(gu) %>% summarise(pm = mean(pm_empty_dry, na.rm = TRUE), am = mean(am_empty_dry, na.rm = TRUE)) %>% arrange(desc(pm)) %>% head(10))
