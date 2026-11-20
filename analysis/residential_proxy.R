# Is "hills are residential" behind the hill effect? A first check with a residential signal from the trips themselves.
# home_share = share of a station's weekday returns (arrivals) that happen 17-20 h: people ride home in the evening.
# Arrivals are not limited by an empty rack (only by a full one), so the morning shortage does not drive this signal
# the way it would drive departures. Run: Rscript analysis/residential_proxy.R > analysis/residential_proxy_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
h <- rd("data/station_hour.csv") %>% filter(daytype == "weekday") %>% group_by(station_no) %>%
  summarise(arr_eve = sum(arr[hour %in% 17:20], na.rm = TRUE), arr_am = sum(arr[hour %in% 7:9], na.rm = TRUE), arr = sum(arr, na.rm = TRUE),
            dep_am = sum(dep[hour %in% 7:9], na.rm = TRUE), dep = sum(dep, na.rm = TRUE), .groups = "drop") %>%
  mutate(home_share = arr_eve / arr, work_share = arr_am / arr)
d <- rd("data/stations.csv") %>% filter(months_active > 0) %>%
  inner_join(rd("data/station_terrain_bare.csv"), by = "station_no") %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv"), by = "station_no") %>%
  inner_join(h, by = "station_no") %>% filter(arr >= 1) %>%
  mutate(gap = as.integer(am_empty_dry >= 0.3), l_sub = log2(subway_m), l_uni = log2(univ_m))
cat("stations", nrow(d), "\n")
cat("home_share (evening 17-20 h share of returns):\n"); print(summary(d$home_share))
cat("work_share (morning 07-09 h share of returns):\n"); print(summary(d$work_share))
cat("\nspearman: elevation vs home_share", round(cor(d$elev_bare_m, d$home_share, method = "spearman"), 3),
    "; elevation vs work_share", round(cor(d$elev_bare_m, d$work_share, method = "spearman"), 3), "\n")
cat("by bare elevation band:\n")
print(d %>% mutate(band = cut(elev_bare_m, c(-Inf, 20, 40, Inf), right = FALSE)) %>% group_by(band) %>%
        summarise(n = n(), home_share = round(mean(home_share), 3), work_share = round(mean(work_share), 3),
                  am_empty = round(mean(am_empty_dry), 3)))
base <- "gap ~ l_sub + l_uni + docks"
show <- function(rhs) {
  f <- glm(as.formula(paste(base, "+", rhs)), family = binomial, data = d)
  k <- grep("scale", names(coef(f)))
  cat(sprintf("\n%s: AIC %.1f\n", rhs, AIC(f))); print(round(exp(cbind(OR = coef(f), confint.default(f)))[k, , drop = FALSE], 2))
}
show("scale(home_share)")
show("scale(elev_bare_m)")
show("scale(elev_bare_m) + scale(home_share)")
show("scale(elev_bare_m) + scale(home_share) + scale(work_share)")
show("scale(elev_bare_m) + scale(climb_bare_all) + scale(home_share) + scale(work_share)")
cat("\nwithin the most residential third of stations (home_share top tercile):\n")
top <- filter(d, home_share >= quantile(home_share, 2 / 3))
f <- glm(gap ~ I(elev_bare_m / 10) + l_sub + l_uni + docks, family = binomial, data = top)
cat(sprintf("  n %d, elevation OR per 10 m %.2f (%.2f-%.2f)\n", nrow(top), exp(coef(f)[2]),
            exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))
low <- filter(d, home_share <= quantile(home_share, 1 / 3))
f <- glm(gap ~ I(elev_bare_m / 10) + l_sub + l_uni + docks, family = binomial, data = low)
cat(sprintf("  least residential third: n %d, elevation OR per 10 m %.2f (%.2f-%.2f)\n", nrow(low), exp(coef(f)[2]),
            exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))
