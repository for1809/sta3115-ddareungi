# Step 1e: terrain variables for every bike station from the Copernicus DEM GLO-30 (30 m).
#
# Inputs : data/station_features.csv (station_no, lat, lon, elev_m from the 90 m DEM)
#          raw/dem/cop30_N37_00_E126_00.tif, raw/dem/cop30_N37_00_E127_00.tif
#          (https://copernicus-dem-30m.s3.amazonaws.com, tiles Copernicus_DSM_COG_10_<tile>_DEM.tif)
# Output : data/station_terrain.csv
#   elev30_m      elevation at the station (bilinear, 30 m DEM)
#   slope_pt      slope at the station in degrees (bilinear on the slope grid)
#   slope_r100    mean slope within 100 m of the station (degrees)
#   slope_r300    mean slope within 300 m of the station (degrees)
#   tpi_500       station elevation minus mean elevation within 500 m (m): > 0 means above its surroundings
# The GLO-30 is a surface model, so buildings leak into it in dense areas. The buffer means (r100, r300)
# smooth that out; slope_pt is kept for comparison.
# Run from the project folder: Rscript scripts/07_terrain.R
suppressPackageStartupMessages(library(terra))

st <- read.csv("data/station_features.csv", colClasses = c(station_no = "character"), encoding = "UTF-8")
tiles <- list.files("raw/dem", pattern = "^cop30_.*\\.tif$", full.names = TRUE)
stopifnot(length(tiles) == 2)

dem <- merge(sprc(lapply(tiles, rast)))
dem <- crop(dem, ext(min(st$lon) - 0.02, max(st$lon) + 0.02, min(st$lat) - 0.02, max(st$lat) + 0.02))
slope <- terrain(dem, v = "slope", unit = "degrees", neighbors = 8)

pts <- vect(st, geom = c("lon", "lat"), crs = "EPSG:4326")
mean_in <- function(r, dist) {
  b <- buffer(pts, width = dist)
  extract(r, b, fun = mean, na.rm = TRUE, ID = FALSE)[[1]]
}

out <- data.frame(
  station_no = st$station_no,
  elev30_m   = round(extract(dem, pts, method = "bilinear", ID = FALSE)[[1]], 1),
  slope_pt   = round(extract(slope, pts, method = "bilinear", ID = FALSE)[[1]], 2),
  slope_r100 = round(mean_in(slope, 100), 2),
  slope_r300 = round(mean_in(slope, 300), 2)
)
out$tpi_500 <- round(out$elev30_m - mean_in(dem, 500), 1)
write.csv(out, "data/station_terrain.csv", row.names = FALSE, fileEncoding = "UTF-8")

# full check of every station, not a sample
cat("stations:", nrow(out), " missing per column:\n"); print(colSums(is.na(out)))
cat("\nsummary:\n"); print(summary(out[, -1]))
cat("\ncorrelation with the 90 m elevation (elev_m):\n")
print(round(cor(cbind(elev_m = st$elev_m, out[, -1]), use = "pairwise.complete.obs"), 2))
