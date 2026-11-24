# Step 1i (part 3): bare-earth station terrain from the TIN surface (scripts/17_tin_elevation.py), replacing the IDW one.
# Inputs : raw/derived/dem_tin_15m.asc, data/station_elevation_tin.csv, data/stations_base.csv, data/station_terrain_bare.csv (IDW)
# Output : data/station_terrain_bare.csv      station_no, elev_bare_m, slope_bare_r100, slope_bare_r300 (now from the TIN)
#          data/station_terrain_bare_idw.csv  the earlier IDW values, kept for comparison
# elev_bare_m is the station's TIN value (exact, from the triangulation); the 2 stations outside the triangulation keep
# their IDW value. Slopes are the mean slope (degrees) within 100 m and 300 m on the 15 m TIN grid.
# Run: Rscript scripts/17_tin_terrain.R
suppressPackageStartupMessages(library(terra))
rd <- function(f) read.csv(f, colClasses = c(station_no = "character"))
if (!file.exists("data/station_terrain_bare_idw.csv")) file.copy("data/station_terrain_bare.csv", "data/station_terrain_bare_idw.csv")
idw <- rd("data/station_terrain_bare_idw.csv")
tin <- rd("data/station_elevation_tin.csv")
con_crs <- crs(vect("raw/contour/contour/N3L_F001.shp"))
dem <- rast("raw/derived/dem_tin_15m.asc"); crs(dem) <- con_crs
slope <- terrain(dem, "slope", unit = "degrees")
st <- rd("data/stations_base.csv")
pst <- project(vect(st, geom = c("lon", "lat"), crs = "EPSG:4326"), con_crs)
mean_in <- function(r, dist) extract(r, buffer(pst, width = dist), fun = mean, na.rm = TRUE, ID = FALSE)[[1]]
out <- data.frame(station_no = st$station_no, slope_bare_r100 = round(mean_in(slope, 100), 2), slope_bare_r300 = round(mean_in(slope, 300), 2))
out$elev_bare_m <- tin$elev_tin_m[match(out$station_no, tin$station_no)]
miss <- is.na(out$elev_bare_m)
out$elev_bare_m[miss] <- idw$elev_bare_m[match(out$station_no[miss], idw$station_no)]
for (v in c("slope_bare_r100", "slope_bare_r300")) {          # a station with no TIN cell in its buffer keeps the IDW slope
  na <- is.na(out[[v]]); out[[v]][na] <- idw[[v]][match(out$station_no[na], idw$station_no)]
  if (any(na)) cat(v, "from IDW for", sum(na), "station(s):", out$station_no[na], "\n")
}
out <- out[, c("station_no", "elev_bare_m", "slope_bare_r100", "slope_bare_r300")]
write.csv(out, "data/station_terrain_bare.csv", row.names = FALSE, fileEncoding = "UTF-8")
cat("stations", nrow(out), " outside the TIN (IDW kept):", sum(miss), " missing:", colSums(is.na(out))[-1], "\n")
m <- merge(out, idw, by = "station_no", suffixes = c("_tin", "_idw"))
cat("elevation TIN - IDW: mean", round(mean(m$elev_bare_m_tin - m$elev_bare_m_idw), 2), " sd", round(sd(m$elev_bare_m_tin - m$elev_bare_m_idw), 2), "\n")
cat("slope r300 TIN vs IDW: correlation", round(cor(m$slope_bare_r300_tin, m$slope_bare_r300_idw), 3),
    " mean", round(mean(m$slope_bare_r300_tin), 2), "vs", round(mean(m$slope_bare_r300_idw), 2), "\n")
cat("exact multiples of 5 m: TIN", sum(abs(out$elev_bare_m / 5 - round(out$elev_bare_m / 5)) < 1e-9),
    " IDW", sum(abs(idw$elev_bare_m / 5 - round(idw$elev_bare_m / 5)) < 1e-9), "\n")
