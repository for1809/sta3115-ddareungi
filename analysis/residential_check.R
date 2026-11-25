# Does "hills are residential" explain the hill effect? Residential index from Seoul living population.
# Stations are placed in administrative dongs (raw/admdong, vuski/admdongkor ver20250701) and get their dong's
# res_index = night (02-04 h) / day (13-15 h) living population (scripts/14_living_population.py).
# Outcome: dry-morning shortage >= 30%. Run: Rscript analysis/residential_check.R > analysis/residential_check_log.txt
suppressPackageStartupMessages({ library(tidyverse); library(terra) })
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character(), adm_cd = col_character()), show_col_types = FALSE)

dong <- vect("raw/admdong/HangJeongDong_ver20250701.geojson")
dong <- dong[dong$sido == "11", ]
cat("Seoul dongs in boundary file:", nrow(dong), "\n")
st <- rd("data/stations.csv") %>% filter(months_active > 0)
pts <- vect(st, geom = c("lon", "lat"), crs = "EPSG:4326")
hit <- extract(dong[, c("adm_cd2", "adm_nm")], pts)
st$adm_cd <- substr(hit$adm_cd2, 1, 8)
st$adm_nm <- hit$adm_nm
cat("stations placed in a dong:", sum(!is.na(st$adm_cd)), "of", nrow(st), "\n")

lp <- rd("data/dong_living_pop.csv")
cat("dong codes matched to living population:", sum(unique(st$adm_cd) %in% lp$adm_cd), "of", n_distinct(st$adm_cd), "\n")
d <- st %>% left_join(lp, by = "adm_cd") %>%
  inner_join(rd("data/station_terrain_bare.csv"), by = "station_no") %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv"), by = "station_no") %>%
  filter(!is.na(res_index), !is.na(am_empty_dry)) %>%
  mutate(gap = as.integer(am_empty_dry >= 0.3), l_sub = log2(subway_m), l_uni = log2(univ_m), l_res = log(res_index))
cat("stations analysed:", nrow(d), "\n\nres_index of stations' dongs:\n"); print(summary(d$res_index))
cat("most and least residential dongs with stations:\n")
print(d %>% distinct(adm_nm, res_index) %>% arrange(res_index) %>% slice(c(1:3, (n() - 2):n())))

cat("\n== are hills more residential? ==\n")
cat("spearman elevation vs res_index:", round(cor(d$elev_bare_m, d$res_index, method = "spearman"), 3), "\n")
print(d %>% mutate(band = cut(elev_bare_m, c(-Inf, 20, 40, Inf), right = FALSE)) %>% group_by(band) %>%
        summarise(n = n(), res_index = round(median(res_index), 3), am_empty = round(mean(am_empty_dry), 3)))
cat("spearman res_index vs dry-morning shortage:", round(cor(d$res_index, d$am_empty_dry, method = "spearman"), 3), "\n")

cat("\n== logistic models (controls: subway, university) ==\n")
base <- "gap ~ l_sub + l_uni"
show <- function(rhs) {
  f <- glm(as.formula(paste(base, "+", rhs)), family = binomial, data = d)
  k <- grep("scale", names(coef(f)))
  cat(sprintf("\n%s: AIC %.1f\n", rhs, AIC(f))); print(round(exp(cbind(OR = coef(f), confint.default(f)))[k, , drop = FALSE], 2))
}
show("scale(l_res)")
show("scale(elev_bare_m)")
show("scale(elev_bare_m) + scale(l_res)")
show("scale(elev_bare_m) * scale(l_res)")
show("scale(elev_bare_m) + scale(climb_bare_all) + scale(l_res)")

cat("\n== elevation effect within residential and non-residential dongs ==\n")
d <- d %>% mutate(res_group = cut(res_index, quantile(res_index, c(0, 1/3, 2/3, 1)), include.lowest = TRUE,
                                  labels = c("least residential", "middle", "most residential")))
for (g in levels(d$res_group)) {
  x <- filter(d, res_group == g)
  f <- glm(gap ~ I(elev_bare_m / 10) + l_sub + l_uni, family = binomial, data = x)
  cat(sprintf("  %-17s n %4d  res_index %.2f-%.2f  shortage share %.3f  elevation OR per 10 m %.2f (%.2f-%.2f)\n",
              g, nrow(x), min(x$res_index), max(x$res_index), mean(x$gap), exp(coef(f)[2]),
              exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))
}
write_csv(d %>% select(station_no, adm_cd, adm_nm, res_index), "data/station_dong.csv")
