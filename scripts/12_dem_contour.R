# Step 1h: bare-earth elevation (no buildings) from the Seoul 1:5000 digital map contours and spot heights.
#
# Inputs : raw/contour/contour/N3L_F001.shp (contour lines, HEIGHT), raw/contour/spot/N3P_F002.shp (spot heights,
#          HEIGHT), both Korean 1985 Modified Central Belt (metres); data/station_features.csv
# Output : raw/derived/dem_bare_15m.tif   15 m grid, inverse-distance interpolation of contour vertices
#                                         (one every 15 m along each line) and spot heights within 250 m
#          data/station_terrain_bare.csv  station_no, elev_bare_m, slope_bare_r100, slope_bare_r300 (degrees)
# Copernicus GLO-30 (scripts/07_terrain.R) is a surface model with buildings in it; this one is not.
# Run from the project folder: Rscript scripts/12_dem_contour.R
suppressPackageStartupMessages(library(terra))
t0 <- Sys.time()
con <- vect("raw/contour/contour/N3L_F001.shp")
spt <- vect("raw/contour/spot/N3P_F002.shp")
cat("contours", nrow(con), " spot heights", nrow(spt), "\n")
cat("contour heights:", paste(range(con$HEIGHT), collapse = " to "), " spot heights:", paste(range(spt$HEIGHT), collapse = " to "), "\n")

cp <- as.points(densify(con, 15))
pts <- rbind(data.frame(crds(cp), z = cp$HEIGHT), data.frame(crds(spt), z = spt$HEIGHT))
pts <- pts[is.finite(pts$z) & pts$z > -5, ]
cat("interpolation points:", nrow(pts), "\n")
pv <- vect(pts, geom = c("x", "y"), crs = crs(con))

tmpl <- rast(ext(con), resolution = 15, crs = crs(con))
dem <- interpIDW(tmpl, pv, field = "z", radius = 250, power = 2, maxPoints = 16, minPoints = 2)
dir.create("raw/derived", showWarnings = FALSE)
writeRaster(dem, "raw/derived/dem_bare_15m.tif", overwrite = TRUE)
cat("DEM cells", ncell(dem), " filled", global(!is.na(dem), "sum")[[1]], " time", round(difftime(Sys.time(), t0, units = "mins"), 1), "min\n")

slope <- terrain(dem, v = "slope", unit = "degrees", neighbors = 8)
st <- read.csv("data/station_features.csv", colClasses = c(station_no = "character"), encoding = "UTF-8")
pts_st <- project(vect(st, geom = c("lon", "lat"), crs = "EPSG:4326"), crs(dem))
mean_in <- function(r, dist) extract(r, buffer(pts_st, width = dist), fun = mean, na.rm = TRUE, ID = FALSE)[[1]]
out <- data.frame(station_no = st$station_no,
                  elev_bare_m = round(extract(dem, pts_st, method = "bilinear", ID = FALSE)[[1]], 1),
                  slope_bare_r100 = round(mean_in(slope, 100), 2),
                  slope_bare_r300 = round(mean_in(slope, 300), 2))
write.csv(out, "data/station_terrain_bare.csv", row.names = FALSE, fileEncoding = "UTF-8")

# full check of every station
cat("\nstations", nrow(out), " missing:\n"); print(colSums(is.na(out)))
print(summary(out[, -1]))
old <- read.csv("data/station_terrain.csv", colClasses = c(station_no = "character"))
m <- merge(out, old, by = "station_no")
m$elev90 <- st$elev_m[match(m$station_no, st$station_no)]
cat("\ncorrelation bare vs Copernicus 30 m elevation:", round(cor(m$elev_bare_m, m$elev30_m, use = "complete"), 3),
    "; vs 90 m:", round(cor(m$elev_bare_m, m$elev90, use = "complete"), 3), "\n")
d <- m$elev30_m - m$elev_bare_m
cat("Copernicus 30 m minus bare elevation (m):\n"); print(summary(d))
cat("largest differences:\n")
print(head(m[order(-abs(d)), c("station_no", "elev_bare_m", "elev30_m", "elev90")], 10))
cat("slope r300 bare vs Copernicus: correlation", round(cor(m$slope_bare_r300, m$slope_r300, use = "complete"), 3), "\n")
