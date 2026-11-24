# Frozen sources

The analysis is about 2025 and does not call any live API. These snapshots, and every API output in `data/`, are fixed as of
2026-11-24; the fetch scripts refuse to overwrite them unless run with `--refetch`.

| File | What | Taken |
| --- | --- | --- |
| `bikelist_map_20261103.csv` | Station ID (ST-xxx), station number, name, docks, latitude, longitude from the realtime rental API (OA-15493). Links the trip records (ST-xxx) to the stock records (5-digit numbers). | 2026-11-03 |
| `station_info_2606.csv` | Station master file (OA-13252, June 2026 edition, CP949): district, address, install date, dock count. | file of 2026-06, saved 2026-11-03 |

API outputs already saved in `data/` (not fetched again):

| File | Source | Script |
| --- | --- | --- |
| `stations_base.csv`, `subway_stations.csv`, `station_elevation.csv` | the snapshot above, Seoul subway master API, Open-Meteo elevation (Copernicus 90 m) | `scripts/01_fetch_features.py` |
| `universities.csv` | Seoul university list API, geocoded with Nominatim | `scripts/02_universities.py` |
| `dong_living_pop.csv` | Seoul living population API, 10 weekdays in June-July 2026 | `scripts/14_living_population.py` |

Stations are those in the snapshot; a station that closed before 2026-11-03 is missing from it, so its 2025 trips cannot be
linked to the stock records (see the coverage notes in the main README).
