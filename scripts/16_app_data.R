# Step 16: small data files for the Shiny app (app/), cut from the analysis tables.
# Same 2,713 stations and the same shortage measure as the talk (dry commute mornings, 07/08/09 h snapshots).
# Run from the project root:  Rscript scripts/16_app_data.R > data/16_app_data_log.txt
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()), show_col_types = FALSE)
gu_en <- c(강남 = "Gangnam", 강동 = "Gangdong", 강북 = "Gangbuk", 강서 = "Gangseo", 관악 = "Gwanak", 광진 = "Gwangjin",
           구로 = "Guro", 금천 = "Geumcheon", 노원 = "Nowon", 도봉 = "Dobong", 동대문 = "Dongdaemun", 동작 = "Dongjak",
           마포 = "Mapo", 서대문 = "Seodaemun", 서초 = "Seocho", 성동 = "Seongdong", 성북 = "Seongbuk", 송파 = "Songpa",
           양천 = "Yangcheon", 영등포 = "Yeongdeungpo", 용산 = "Yongsan", 은평 = "Eunpyeong", 종로 = "Jongno", 중 = "Jung",
           중랑 = "Jungnang")

st <- rd("data/stations.csv") %>%
  filter(use_day > 0) %>%
  select(station_no, name, gu, lat, lon, elev_m, subway_m, subway_name, univ_m, nearest_station_m, use_day, net_day) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty = am_empty_dry, am_empty_all), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no, slope = slope_bare_r300), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no, climb = climb_bare_all), by = "station_no") %>%
  filter(!is.na(am_empty)) %>%
  left_join(rd("data/stations_wet.csv") %>% filter(n_wet >= 30) %>% select(station_no, am_empty_wet, n_wet), by = "station_no") %>%
  left_join(rd("data/station_2x2.csv") %>% filter(days_dry >= 30) %>%
              transmute(station_no, riders_in = -day_out_trip_dry, other_in = other_in_day_dry), by = "station_no") %>%
  mutate(gu_en = unname(gu_en[sub("구$", "", gu)]),
         name = sub("^\\d+\\.\\s*", "", name),
         across(c(am_empty, am_empty_all, am_empty_wet), ~ round(.x, 3)),
         across(c(slope, climb, riders_in, other_in, net_day), ~ round(.x, 2)),
         lat = round(lat, 6), lon = round(lon, 6))
stopifnot(nrow(st) == 2713, !anyNA(st$gu_en))
cat("stations", nrow(st), "; with wet mornings >= 30:", sum(!is.na(st$am_empty_wet)),
    "; with rider/other split:", sum(!is.na(st$riders_in)), "\n")
cat("band means (dry):\n")
print(st %>% mutate(band = cut(elev_m, c(0, 20, 40, Inf), right = FALSE)) %>% group_by(band) %>%
        summarise(n = n(), shortage = round(mean(am_empty), 4)))
q20 <- sort(st$use_day)[floor(nrow(st) * 0.2) + 1]
cat("merge candidates (bottom 20%, within 300 m):", sum(st$use_day <= q20 & st$nearest_station_m <= 300),
    "; often empty among them:", sum(st$use_day <= q20 & st$nearest_station_m <= 300 & st$am_empty >= 0.3), "\n")

dir.create("app/data", showWarnings = FALSE, recursive = TRUE)
write_csv(st, "app/data/stations.csv")
hr <- rd("data/station_hour.csv") %>% semi_join(st, by = "station_no") %>% select(station_no, daytype, hour, dep, arr)
write_csv(hr, "app/data/station_hour.csv")
cat("wrote app/data/stations.csv (", nrow(st), "rows ) and app/data/station_hour.csv (", nrow(hr), "rows )\n")
