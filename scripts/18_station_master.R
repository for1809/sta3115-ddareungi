# One table with everything we know per station (frozen station list, 2,736 rows; 2,713 active in 2025).
# Joins the station-level files in data/ by station_no; nothing is recomputed except the 2x2 group label,
# which follows analysis/two_by_two.R (hourly stock, dry weekdays, stations with >= 30 such days).
# Run: Rscript scripts/18_station_master.R
# Output: data/station_master.csv; column meanings in data/station_master_columns.md
suppressPackageStartupMessages(library(tidyverse))
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character(), adm_cd = col_character(), aws_id = col_character()),
                           show_col_types = FALSE)

m <- rd("data/stations.csv") %>%
  rename(elev90_m = elev_m, am_empty_2025 = am_empty, parked_08_2025 = parked_08, commute_share_2025 = commute_share) %>%
  mutate(active_2025 = months_active > 0) %>%
  left_join(rd("data/station_terrain_bare.csv"), by = "station_no") %>%
  left_join(rd("data/station_terrain.csv"), by = "station_no") %>%
  left_join(rd("data/station_climb_bare.csv"), by = "station_no") %>%
  left_join(rd("data/stations_dry.csv") %>% select(station_no, aws_id, aws_m, am_empty_dry, pm_empty_dry, dry_am_days,
                                                    use_am_dry, use_pm_dry, use_commute_dry, climb_in_m, drop_am_out_m), by = "station_no") %>%
  left_join(rd("data/stations_wet.csv") %>% select(station_no, am_empty_wet, n_wet_days = n_wet), by = "station_no") %>%
  left_join(rd("data/station_2x2.csv") %>% select(station_no, days_dry, am_out_inv_dry, day_out_inv_dry, am_out_trip_dry,
                                                   day_out_trip_dry, other_in_day_dry), by = "station_no") %>%
  mutate(group_2x2 = case_when(is.na(days_dry) | days_dry < 30 | use_day <= 0 | is.na(am_empty_dry) ~ NA_character_,
                               am_out_inv_dry > 0 & day_out_inv_dry > 0 ~ "G1 morning out, day out",
                               am_out_inv_dry > 0 ~ "G2 morning out, day back",
                               day_out_inv_dry > 0 ~ "G3 morning in, day out",
                               TRUE ~ "G4 morning in, day back")) %>%
  left_join(rd("data/station_dong.csv"), by = "station_no")

m <- m %>% relocate(station_no, station_id, name, gu, adm_cd, adm_nm, lat, lon, docks, active_2025, months_active, role,
                    elev_bare_m, elev30_m, elev90_m)
write_csv(m, "data/station_master.csv", na = "")
cat("station_master.csv:", nrow(m), "rows,", ncol(m), "columns; active in 2025:", sum(m$active_2025), "\n")
cat("2x2 groups:\n"); print(count(m, group_2x2))
cat("\nmissing values per column (only columns with any):\n")
na <- colSums(is.na(m)); print(na[na > 0])
