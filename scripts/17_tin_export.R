# Step 1i (part 1): points for a TIN (triangulated) bare-earth surface, which replaces the IDW of scripts/12_dem_contour.R.
# IDW of contour vertices puts a station that sits near one contour at exactly that contour's height (29% of stations
# landed on a multiple of 5 m). Linear interpolation on triangles between the contour vertices does not.
# Inputs : raw/contour/contour/N3L_F001.shp (contours), raw/contour/spot/N3P_F002.shp (spot heights), data/stations_base.csv,
#          raw/derived/dem_bare_15m.tif (only for its 15 m grid)
# Output : raw/derived/tin_points.csv   x, y, z: contour vertices every 10 m and spot heights within 600 m of a station
#          raw/derived/tin_stations.csv station_no, x, y (same projected CRS)
#          raw/derived/tin_grid.txt     ncol nrow xmin ymin cell of the 15 m grid
# Run: Rscript scripts/17_tin_export.R; python scripts/17_tin_elevation.py; Rscript scripts/17_tin_terrain.R
suppressPackageStartupMessages(library(terra))
con <- vect("raw/contour/contour/N3L_F001.shp")
spt <- vect("raw/contour/spot/N3P_F002.shp")
st <- read.csv("data/stations_base.csv", colClasses = c(station_no = "character"))
pst <- project(vect(st, geom = c("lon", "lat"), crs = "EPSG:4326"), crs(con))
g <- rast("raw/derived/dem_bare_15m.tif")
cat(ncol(g), nrow(g), xmin(g), ymin(g), res(g)[1], "\n", file = "raw/derived/tin_grid.txt")
if (!file.exists("raw/derived/tin_points.csv")) {
  area <- aggregate(buffer(pst, 600))
  cp <- as.points(densify(con, 10))
  pts <- rbind(data.frame(crds(cp), z = cp$HEIGHT), data.frame(crds(spt), z = spt$HEIGHT))
  pts <- pts[is.finite(pts$z) & pts$z > -5, ]
  pv <- vect(pts, geom = c("x", "y"), crs = crs(con))
  keep <- is.related(pv, area, "intersects")
  cat("points:", nrow(pts), " within 600 m of a station:", sum(keep), "\n")
  write.csv(pts[keep, ], "raw/derived/tin_points.csv", row.names = FALSE)
}
write.csv(data.frame(station_no = st$station_no, crds(pst)), "raw/derived/tin_stations.csv", row.names = FALSE)
cat("grid:", readLines("raw/derived/tin_grid.txt"), "\n")
