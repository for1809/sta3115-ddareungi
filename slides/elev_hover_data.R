# Data for the hover version of slide 5 (elevation vs morning shortage) in the one-file HTML deck.
# Same stations, shortage (dry commute mornings), 80 m cut and LOESS (span 0.75) as 02_elevation_loess.png
# in slides/slide_figures.R; the LOESS is fitted here and sent as a curve so the browser only draws it.
# Run from the project root:  Rscript slides/elev_hover_data.R > slides/elev_hover_data_log.txt
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
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no), by = "station_no")
q20 <- sort(st$use_day)[floor(nrow(st) * 0.2) + 1]
st <- st %>% filter(!is.na(am_empty)) %>%
  mutate(low_near = use_day <= q20 & nearest_station_m <= 300,
         band = cut(elev_m, c(0, 20, 40, Inf), right = FALSE))
cat("stations", nrow(st), "; above", X_MAX, "m:", sum(st$elev_m > X_MAX), "; merge candidates", sum(st$low_near), "\n")
print(st %>% group_by(band) %>% summarise(n = n(), mean_shortage = round(mean(am_empty), 4)))

pts <- st %>% filter(elev_m <= X_MAX)
fit <- loess(am_empty ~ elev_m, data = pts, span = 0.75)   # what geom_smooth(method = "loess", span = 0.75) fits
grid <- tibble(x = seq(min(pts$elev_m), max(pts$elev_m), length.out = 120))
grid$y <- predict(fit, newdata = data.frame(elev_m = grid$x))
cat("LOESS at 10, 30, 60 m:", round(predict(fit, data.frame(elev_m = c(10, 30, 60))), 3), "\n")

out <- list(
  points = pts %>% transmute(n = name, g = unname(gu_en[sub("구$", "", gu)]), e = elev_m,
                             s = round(am_empty, 3), u = use_day, m = as.integer(low_near)),
  curve = grid %>% mutate(across(everything(), ~ round(.x, 4))),
  bands = st %>% group_by(band) %>% summarise(v = round(mean(am_empty), 4), .groups = "drop") %>% pull(v),
  n_above = sum(st$elev_m > X_MAX))
stopifnot(!anyNA(out$points$g))
jsonlite::write_json(out, "slides/elev_hover.json", dataframe = "rows", auto_unbox = TRUE, digits = NA)
cat("wrote slides/elev_hover.json:", nrow(out$points), "points\n")
