# data/station_master.csv: one row per station

Built by `scripts/18_station_master.R` from the station files in `data/` (joined by `station_no`, nothing recomputed
except `group_2x2`). 2,736 rows: the frozen station list (`data/source/`); 2,713 were active in 2025. Unless a column says
otherwise, "weekday" means a 2025 Monday to Friday that is not a public holiday, and "dry" means the station's nearest
KMA AWS recorded no rain in the window (see `scripts/10_aggregate_dry.py`). Empty cell = not available (for example
a station with no stock records).

| Column | Meaning | Source |
| --- | --- | --- |
| station_no | 5-digit station number (used by the stock records) | snapshot |
| station_id | ST-xxx id (used by the trip records) | snapshot |
| name, gu | station name and district | snapshot, station info |
| adm_cd, adm_nm | administrative dong (2025-07 boundaries) | analysis/residential_check.R |
| lat, lon | WGS84 coordinates | snapshot |
| docks | number of docks | snapshot |
| active_2025, months_active | active in 2025; months of 2025 with trips | 06_aggregate_year.py |
| role | low use / commute core / other, citywide thresholds (see 05_aggregate.py) | 06_aggregate_year.py |
| elev_bare_m | ground elevation (m) from the Seoul 1:5,000 contours and spot heights, IDW on a 15 m grid; snaps to multiples of 5 m near contours | 12_dem_contour.R |
| elev_tin_m, tin_flat | ground elevation (m) by linear interpolation on a triangulation of the same contours and spot heights; tin_flat = 1 where the triangle's three corners share one height | 17_tin_elevation.py |
| elev30_m | Copernicus DEM 30 m (surface model, buildings included) | 07_terrain.R |
| elev90_m | Open-Meteo elevation (Copernicus 90 m, whole metres) | 01_fetch_features.py |
| subway_m, subway_name | distance (m) to the nearest subway station and its name | 04_station_features.py |
| univ_m, univ_name | distance (m) to the nearest university and its name | 04_station_features.py |
| nearest_station_m | distance (m) to the nearest other bike station | 04_station_features.py |
| gu_filled | 1 if the district was missing and taken from the nearest station | 04_station_features.py |
| use_day | rentals + returns per weekday | 06_aggregate_year.py |
| dep_day, arr_day, net_day | rentals, returns, rentals minus returns per weekday (net > 0: bikes leave) | 06_aggregate_year.py |
| commute_share_2025 | share of weekday rentals in 07-09 h and 17-19 h | 06_aggregate_year.py |
| am_empty_2025 | share of weekday 07, 08, 09 h stock snapshots with 0 bikes (all weather) | 06_aggregate_year.py |
| parked_08_2025 | mean bikes parked at 08 h on weekdays | 06_aggregate_year.py |
| slope_bare_r100, slope_bare_r300 | mean ground slope (degrees) within 100 m and 300 m, from the contour surface | 12_dem_contour.R |
| slope_pt, slope_r100, slope_r300, tpi_500 | slope at the station and within 100 m / 300 m (degrees), and elevation minus mean elevation within 500 m (m), Copernicus 30 m | 07_terrain.R |
| climb_bare, climb_bare_all | mean climb (m) of trips ending here: elevation here minus at the origin, bare elevation; without / with round trips | analysis/bare_compare.R |
| aws_id, aws_m | nearest KMA AWS station and its distance (m) | 10_aggregate_dry.py |
| am_empty_dry, pm_empty_dry | share of 07-09 h / 17-19 h stock snapshots with 0 bikes on dry mornings / evenings | 10_aggregate_dry.py |
| dry_am_days | number of dry weekday mornings | 10_aggregate_dry.py |
| use_am_dry, use_pm_dry, use_commute_dry | rentals + returns in 07-09 h, 17-19 h, and both, per dry weekday | 10_aggregate_dry.py |
| climb_in_m, drop_am_out_m | mean climb of trips ending here; mean drop of 07-09 h trips leaving here (Copernicus 30 m) | 10_aggregate_dry.py |
| am_empty_wet, n_wet_days | morning empty share on wet weekday mornings, and how many | stations_wet.csv |
| days_dry | dry weekdays with stock at 06, 07, 09 and 23 h | 15_inventory_2x2.py |
| am_out_inv_dry, day_out_inv_dry | bikes at 07 h minus 09 h, and at 06 h minus 23 h (> 0: bikes leave), dry weekdays | 15_inventory_2x2.py |
| am_out_trip_dry, day_out_trip_dry | the same from trips only (rentals minus returns) | 15_inventory_2x2.py |
| other_in_day_dry | daily bikes added by moves other than rides (trip outflow minus stock outflow; mostly trucks) | 15_inventory_2x2.py |
| group_2x2 | G1 to G4 from am_out_inv_dry and day_out_inv_dry (as analysis/two_by_two.R; empty if fewer than 30 dry days) | 18_station_master.R |
| res_index | night / day living population of the station's dong (> 1: residential) | 14_living_population.py |
