# data/od_2024_2025: trip-based data for 2024–2025 (Jiho)

Trip-based data behind the net-flow analysis, 2024-01 to 2025-12. It sits next to the existing `data/` files and changes
none of them. Plots are not included. The stock-based "morning empty" measures of the existing data are not used here.

## What is here

| Path | What | Built by |
| --- | --- | --- |
| `source/station_info/` | station files (OA-13252), 2023-12, 2024-06, 2024-12, 2025-06, 2025-12 | download |
| `source/seoul_gu.json` | district boundaries (southkorea/seoul-maps 2013) | GitHub |
| `master/station_master_final.csv` | one row per station (2,904): ids, name, district, coordinates, docks, install date, elevation, relief, nearest subway | `build_final_master.py`, then `subway_from_repo_api.py` |
| `master/station_master.csv`, `station_table.csv` | station list before the GIS joins | `build_station_table.py` |
| `master/station_elevation.csv` | elevation from the 1:5,000 contours (TIN), relief within 300 m | `station_elevation_from_contour.py` |
| `master/mapping/` | ST-xxx ↔ station number per period, with the hourly-rental correlation (`map_r`) | `station_id_mapping.py` |
| `tables/T1_gu_month*.csv`, `T4_month_pass.csv`, `QA_monthly.csv` | district × month rentals; monthly rentals by pass type; row checks | `preprocess_ddareungi.py` |
| `tables/T3_gu_date_hour_condition.csv.gz` | district × date × hour × sex × age group × pass type rentals | `preprocess_ddareungi.py` |
| `tables/age_station_hour.csv.gz` | station × age group × weekday/offday × hour rentals (sum 80,387,987) | `age_station_hour.py` |
| `od/s0_station_summary.csv` | one row per station: clear-weekday rentals, returns, net outflow (day, 07–09 h, 17–19 h), per dock, 2×2 type; `enough_days` = at least 50 clear weekdays | `step0_build_tables.py` |
| `od/s0_station_daily.csv.gz`, `s0_station_hour_profile.csv.gz`, `s0_daily_seoul.csv`, `s0_qa.txt` | station × date; station × hour by day type; citywide daily; dropped days | `step0_build_tables.py` |
| `od/od_pairs_all_clearweekday.csv.gz` | station-to-station trips summed over the clear weekdays: whole day, 07–09 h, 17–19 h | `step4_od_pairs.py` |
| `od/s4_vector_1km.csv` | 1 km net-flow vectors, whole day and 07–09 h, with downhill / uphill / across class | `step4_flow_prep.py` |

Scripts are in `scripts/od_2024_2025/`.

## Stations

`master/station_master_final.csv` has 2,904 stations from the five station files. 2,878 of them could be linked to the
trip records (ST id). `od/s0_station_summary.csv` keeps those 2,878; the analysis uses the 2,843 with `enough_days`
(at least 50 of the clear weekdays with records). The 35 left out are mostly stations installed in 2025 or closed early
in the period (median 34 clear weekdays). Against the snapshot in `data/source/`, 2,713 ST ids are in both.

## Subway

The subway columns (`subway_nearest`, `subway_dist_m`, `subway_lines`, `subway_n_500m`) are computed from the repo's
API list, `data/subway_stations.csv` (784 station-line rows), by `subway_from_repo_api.py`. They replace the values from
a subway shapefile used earlier (distance correlation 0.994; the same nearest station for 97.8% of stations).

## Not settled yet

- Weather: "clear weekday" (no weekend or holiday, daily rain < 1 mm; 378 days) was set with KMA ASOS 108. The repo's
  AWS data (`data/weather_daily.csv`) covers 2025 only, so 2024 cannot be switched yet.
- Elevation: `elevation_m` comes from the same contours as the repo's `elev_tin_m` and `elev_bare_m` (Pearson 0.994 and
  0.996), but snaps more stations to multiples of 5 m (48% vs 14%).

## Not included

- Raw trip files (5-minute OD, about 2.7 GB) and hourly usage files (OA-15245, about 7.6 GB): too large for GitHub.
  Download from Seoul Open Data and run `step0_od_aggregate.py` and `preprocess_ddareungi.py`.
