# Data for the step-by-step slides in the one-file HTML deck (slides/build_deck_html.py):
#   slide 5  (elev)  elevation vs morning shortage, revealed band by band, then the LOESS curve
#   slide 7  (cands) merge candidates as one dot each, then the ones already empty, with a 10/20/30% use cut-off
#   slide 11 (rain)  the same stations on dry and on wet mornings, then the Tukey mean-difference view
# Same stations and rules as slides/slide_figures.R (dry commute mornings, 90 m elevation, 80 m cut for curves,
# LOESS span 0.75, merge candidate = bottom share of use with another station within 300 m, often empty = 30% or more).
# Run from the project root:  Rscript slides/interactive_data.R > slides/interactive_data_log.txt
suppressPackageStartupMessages(library(tidyverse))
X_MAX <- 80
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
gu_en <- c(강남 = "Gangnam", 강동 = "Gangdong", 강북 = "Gangbuk", 강서 = "Gangseo", 관악 = "Gwanak", 광진 = "Gwangjin",
           구로 = "Guro", 금천 = "Geumcheon", 노원 = "Nowon", 도봉 = "Dobong", 동대문 = "Dongdaemun", 동작 = "Dongjak",
           마포 = "Mapo", 서대문 = "Seodaemun", 서초 = "Seocho", 성동 = "Seongdong", 성북 = "Seongbuk", 송파 = "Songpa",
           양천 = "Yangcheon", 영등포 = "Yeongdeungpo", 용산 = "Yongsan", 은평 = "Eunpyeong", 종로 = "Jongno", 중 = "Jung",
           중랑 = "Jungnang")
st <- rd("data/stations.csv") %>%
  filter(use_day > 0) %>%
  select(-am_empty) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty = am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no), by = "station_no") %>%
  left_join(rd("data/stations_wet.csv") %>% select(station_no, am_empty_wet, n_wet), by = "station_no") %>%
  mutate(band = cut(elev_m, c(0, 20, 40, Inf), labels = c("lo", "mid", "hi"), right = FALSE),
         gap = am_empty >= 0.3)
cut_q <- function(p) sort(st$use_day)[floor(nrow(st) * p) + 1]   # same rule as q20 in the analysis
st <- st %>% filter(!is.na(am_empty))
cat("stations", nrow(st), "\n")

# ---- slide 5 ----
pts <- st %>% filter(elev_m <= X_MAX)
fit <- loess(am_empty ~ elev_m, data = pts, span = 0.75)
curve5 <- tibble(x = seq(min(pts$elev_m), max(pts$elev_m), length.out = 120)) %>%
  mutate(y = predict(fit, newdata = data.frame(elev_m = x)))
bands5 <- st %>% group_by(band) %>% summarise(n = n(), v = mean(am_empty), .groups = "drop")
cat("\nslide 5 bands:\n"); print(bands5)
low20 <- st$use_day <= cut_q(0.2) & st$nearest_station_m <= 300
elev <- list(
  points = pts %>% mutate(m = (use_day <= cut_q(0.2) & nearest_station_m <= 300)) %>%
    transmute(n = name, g = unname(gu_en[sub("구$", "", gu)]), e = elev_m, s = round(am_empty, 3), u = use_day, m = as.integer(m)),
  curve = curve5 %>% mutate(across(everything(), ~ round(.x, 4))),
  bands = bands5 %>% transmute(n, v = round(v, 4)),
  n_above = sum(st$elev_m > X_MAX))

# ---- slide 7 ----
cands <- map(c(0.1, 0.2, 0.3), function(p) {
  q <- cut_q(p)
  b <- st %>% filter(use_day <= q, nearest_station_m <= 300) %>%
    group_by(band, .drop = FALSE) %>% summarise(n = n(), gap = sum(gap), .groups = "drop")
  cat(sprintf("\nslide 7 cut-off bottom %d%% (rides a day <= %.1f): %d candidates, %d often empty (%.1f%%)\n",
              round(p * 100), q, sum(b$n), sum(b$gap), 100 * sum(b$gap) / sum(b$n)))
  print(b %>% mutate(share = round(gap / n, 3)))
  list(p = p, q = round(q, 1), n = b$n, gap = b$gap)
})
stopifnot(identical(cands[[2]]$n, c(68L, 167L, 192L)), identical(cands[[2]]$gap, c(6L, 27L, 95L)))

# ---- slide 11 ----
md <- st %>% filter(n_wet >= 30, !is.na(am_empty_wet)) %>%
  mutate(m = (am_empty + am_empty_wet) / 2, d = am_empty_wet - am_empty)
bands11 <- md %>% group_by(band) %>%
  summarise(n = n(), dry = mean(am_empty), wet = mean(am_empty_wet), r = cor(am_empty, am_empty_wet), .groups = "drop")
cat("\nslide 11 (stations with >= 30 wet mornings):\n"); print(bands11)
fit11 <- loess(d ~ m, data = md, span = 0.75)
curve11 <- tibble(x = seq(min(md$m), max(md$m), length.out = 120)) %>% mutate(y = predict(fit11, newdata = data.frame(m = x)))
rain <- list(
  points = md %>% transmute(b = as.integer(band), e = elev_m, dry = round(am_empty, 3), wet = round(am_empty_wet, 3)),
  bands = bands11 %>% transmute(n, dry = round(dry, 4), wet = round(wet, 4), r = round(r, 3)),
  curve = curve11 %>% mutate(across(everything(), ~ round(.x, 4))))

stopifnot(!anyNA(elev$points$g))
jsonlite::write_json(list(elev = elev, cands = cands, rain = rain), "slides/interactive.json",
                     dataframe = "rows", auto_unbox = TRUE, digits = NA)
cat("\nwrote slides/interactive.json:", nrow(elev$points), "elevation points,", nrow(rain$points), "rain points\n")
