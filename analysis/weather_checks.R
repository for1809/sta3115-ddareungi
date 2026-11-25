# Two weather checks (inputs from scripts/11_weather_checks.py and scripts/09_weather_daily.py).
#  A. Do hill stations still run empty on wet mornings, when fewer people ride? (structural vs demand-driven shortage)
#  B. How much do rain, temperature and wind change weekday rentals?
# Run from the project folder: Rscript analysis/weather_checks.R > analysis/weather_checks_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f, ...) read_csv(f, show_col_types = FALSE, ...)
st <- rd("data/stations.csv", col_types = cols(station_no = col_character())) %>% filter(months_active > 0)
wet <- rd("data/stations_wet.csv", col_types = cols(station_no = col_character()))
s <- st %>% select(station_no, name, gu, elev_m, subway_m, univ_m) %>% inner_join(wet, by = "station_no") %>%
  mutate(band = cut(elev_m, c(0, 20, 40, Inf), labels = c("20m 미만", "20~40m", "40m 이상"), right = FALSE),
         l_sub = log2(subway_m), l_uni = log2(univ_m))

cat("== A. wet vs dry mornings (07-09 h snapshots) ==\n")
cat("stations:", nrow(s), "; wet-morning snapshots per station:\n"); print(summary(s$n_wet))
cat("\nmean shortage by elevation band:\n")
print(s %>% group_by(band) %>% summarise(n = n(), dry = mean(am_empty_dry, na.rm = TRUE), wet = mean(am_empty_wet, na.rm = TRUE),
                                        ratio_wet_dry = wet / dry,
                                        after_wet = mean(am_empty_dry_after_wet, na.rm = TRUE),
                                        after_dry = mean(am_empty_dry_after_dry, na.rm = TRUE)))
cat("\npaired difference wet - dry per station (mean, 95% CI) by band:\n")
for (b in levels(s$band)) {
  x <- with(filter(s, band == b, n_wet >= 30), am_empty_wet - am_empty_dry)
  t <- t.test(x)
  cat(sprintf("  %-8s n=%4d  mean %+.4f  (%+.4f to %+.4f)\n", b, length(x), mean(x), t$conf.int[1], t$conf.int[2]))
}
cat("\nelevation odds ratio per 10 m (shortage >= 30%), wet vs dry mornings, stations with >= 30 wet snapshots:\n")
d <- filter(s, n_wet >= 30)
for (g in c("dry", "wet", "dry_after_wet", "dry_after_dry")) {
  y <- d[[paste0("am_empty_", g)]] >= 0.3
  f <- glm(y ~ I(elev_m / 10) + l_sub + l_uni, family = binomial, data = d)
  ci <- exp(confint.default(f)[2, ])
  cat(sprintf("  %-14s share %.3f  OR %.2f (%.2f-%.2f)\n", g, mean(y, na.rm = TRUE), exp(coef(f)[2]), ci[1], ci[2]))
}
cat("correlation of station shortage, wet vs dry mornings:", round(cor(d$am_empty_wet, d$am_empty_dry, use = "complete"), 3), "\n")

cat("\n== B. weather and weekday rentals (zone = bike stations sharing the nearest AWS station) ==\n")
w <- rd("data/weather_daily.csv", col_types = cols(aws_id = col_character(), date = col_date()))
r <- rd("data/daily_aws_rentals.csv", col_types = cols(aws_id = col_character(), date = col_date())) %>%
  inner_join(w, by = c("aws_id", "date")) %>%
  mutate(month = factor(lubridate::month(date)), wday = factor(lubridate::wday(date)),
         rain_am_c = cut(rain_am, c(-Inf, 0, 1, 5, Inf), labels = c("없음", "1mm 이하", "1~5mm", "5mm 초과")),
         rain_day_c = cut(rain_day, c(-Inf, 0, 1, 5, 20, Inf), labels = c("없음", "1mm 미만", "1~5mm", "5~20mm", "20mm 초과")),
         temp_c = cut(temp_am, c(-Inf, 0, 10, 20, 25, 30, Inf), labels = c("0도 미만", "0~10도", "10~20도", "20~25도", "25~30도", "30도 이상")),
         wind_c = cut(wind_am, c(-Inf, 2, 4, Inf), labels = c("2m/s 미만", "2~4m/s", "4m/s 이상")))
cat("zone-days:", nrow(r), " weekdays:", n_distinct(r$date), " zones:", n_distinct(r$aws_id), "\n")
r <- r %>% mutate(temp_c = relevel(temp_c, "20~25도"))
pct <- function(f, pat) {
  co <- summary(f)$coefficients; k <- grep(pat, rownames(co))
  tibble(term = rownames(co)[k], change_pct = round((exp(co[k, 1]) - 1) * 100, 1),
         lo = round((exp(co[k, 1] - 1.96 * co[k, 2]) - 1) * 100, 1), hi = round((exp(co[k, 1] + 1.96 * co[k, 2]) - 1) * 100, 1))
}
f_am <- lm(log(rentals_am + 1) ~ rain_am_c + temp_c + wind_c + aws_id + month + wday, data = r)
cat("\nmorning (07-09 h) rentals, % change vs no rain / 20-25 C / calm, with zone, month and weekday fixed effects:\n")
print(bind_rows(pct(f_am, "^rain_am_c"), pct(f_am, "^temp_c"), pct(f_am, "^wind_c")), n = 30)
f_day <- lm(log(rentals + 1) ~ rain_day_c + temp_c + wind_c + aws_id + month + wday, data = r)
cat("\nwhole-day rentals, % change by daily rain (same controls):\n")
print(pct(f_day, "^rain_day_c"))
cat("\nshare of zone-days by morning rain:\n"); print(round(prop.table(table(r$rain_am_c)), 3))
