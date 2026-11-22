# Figures for the 15-minute talk: Korean labels, large type for a 16:9 slide, no in-plot titles
# (each slide carries its own headline, listed in README "발표 그림").
# Elevation on every x axis is the 90 m grid used in the main analysis (data/stations.csv elev_m);
# slope and climb come from the bare-earth DEM (scripts/12_dem_contour.R), which has no buildings in it.
# Station-level shortage is the dry-commute basis (no rain 06-10 h); the monthly backup figure uses all weekdays.
# Run from the project root: Rscript slides/slide_figures.R > slides/slide_figures_log.txt
suppressPackageStartupMessages({
  library(tidyverse)
  library(terra)
  library(vcd)
})
out <- "slides/figures"
dir.create(out, showWarnings = FALSE, recursive = TRUE)
windowsFonts(Noto = windowsFont("Noto Sans KR"))
ink <- "#22262a"; muted <- "#6b7178"; grid_col <- "#e6e8ea"; red <- "#c0392b"; blue <- "#4f7ea8"
band_cols <- c("20m 미만" = "#9fb7c9", "20~40m" = "#4f7ea8", "40m 이상" = "#c0392b")
X_MAX <- 80  # few stations sit above 80 m, so smooth curves stop there

theme_slide <- function() {
  theme_minimal(base_size = 17, base_family = "Noto") +
    theme(text = element_text(colour = ink),
          axis.text = element_text(colour = muted, size = 14),
          axis.title = element_text(size = 15),
          panel.grid.minor = element_blank(),
          panel.grid.major = element_line(colour = grid_col, linewidth = 0.4),
          strip.text = element_text(face = "bold", size = 15, hjust = 0),
          legend.position = "top", legend.justification = "left",
          legend.title = element_text(size = 14), legend.text = element_text(size = 14),
          plot.caption = element_text(colour = muted, size = 11.5, hjust = 0),
          plot.margin = margin(8, 14, 8, 8))
}
save_fig <- function(p, name, w = 10, h = 5.6) {
  ggsave(file.path(out, paste0(name, ".png")), p, width = w, height = h, dpi = 200, bg = "white")
}
pct <- function(x, acc = 0.1) scales::percent(x, accuracy = acc)

# ---- data (same joins and role rules as analysis/eda_analysis.Rmd) ----
rd <- function(f) read_csv(f, col_types = cols(station_no = col_character()),
                           show_col_types = FALSE)
stations <- rd("data/stations.csv") %>%
  filter(use_day > 0) %>%
  select(-am_empty) %>%
  inner_join(rd("data/stations_dry.csv") %>% select(station_no, am_empty = am_empty_dry), by = "station_no") %>%
  inner_join(rd("data/station_terrain_bare.csv") %>% select(station_no, slope_bare = slope_bare_r300), by = "station_no") %>%
  inner_join(rd("data/station_climb_bare.csv") %>% select(station_no, climb_bare = climb_bare_all), by = "station_no") %>%
  left_join(rd("data/station_dong.csv") %>% select(station_no, res_index), by = "station_no") %>%
  left_join(rd("data/stations_wet.csv") %>% select(station_no, am_empty_wet, n_wet), by = "station_no") %>%
  mutate(elev_band = cut(elev_m, c(0, 20, 40, Inf), labels = names(band_cols), right = FALSE),
         gap = as.integer(am_empty >= 0.3))
q20 <- sort(stations$use_day)[floor(nrow(stations) * 0.2) + 1]
q50 <- sort(stations$use_day)[floor(nrow(stations) * 0.5) + 1]
stations <- stations %>%
  mutate(low_near = use_day <= q20 & nearest_station_m <= 300,
         role = case_when(low_near & gap == 1 ~ "supply_gap_suspect", low_near ~ "consolidate", gap == 1 ~ "morning_gap",
                          use_day >= q50 & commute_share >= 0.5 ~ "commute_core", TRUE ~ "other"))
st <- stations %>% filter(!is.na(am_empty))
cat("stations", nrow(stations), "with dry-morning shortage", nrow(st), "\n")
n_above <- sum(st$elev_m > X_MAX)
cap_above <- sprintf("고도 %dm 초과 대여소 %d곳은 수가 적어 그림에서 뺐다.", X_MAX, n_above)

# ---- 01 scale: bikes parked vs riding, weekday hours ----
dh <- read_csv("data/district_hour.csv", show_col_types = FALSE) %>% filter(gu != "(미상)") %>%
  group_by(hour) %>% summarise(parked = sum(parked), riding = sum(riding), .groups = "drop")
peak <- dh %>% slice_max(riding, n = 1)
cat("\n01 peak riding:", peak$riding, "at", peak$hour, "h; parked then", peak$parked,
    "; riding share", round(peak$riding / (peak$riding + peak$parked), 3), "\n")
p01 <- dh %>% pivot_longer(-hour) %>%
  mutate(name = factor(name, levels = c("parked", "riding"), labels = c("대여소에 서 있음", "달리는 중"))) %>%
  ggplot(aes(hour, value, fill = name)) +
  geom_col(width = 0.82) +
  annotate("label", x = peak$hour - 4.5, y = max(dh$parked + dh$riding) + 4200, family = "Noto", size = 5,
           label = sprintf("가장 바쁜 %d시에도\n달리는 자전거는 %s대(%s)", peak$hour,
                           scales::comma(peak$riding), pct(peak$riding / (peak$riding + peak$parked), 1)),
           linewidth = 0, fill = "white", colour = ink, lineheight = 0.95) +
  scale_fill_manual(values = c("대여소에 서 있음" = "#c9ced3", "달리는 중" = red), name = NULL) +
  scale_x_continuous(breaks = seq(0, 23, 3), labels = paste0(seq(0, 23, 3), "시")) +
  scale_y_continuous(labels = scales::comma, expand = expansion(mult = c(0, 0.2))) +
  labs(x = "평일 시간대", y = "자전거 수(대)") + theme_slide() + theme(panel.grid.major.x = element_blank())
save_fig(p01, "01_scale")

# ---- 02 elevation vs morning shortage, LOESS ----
bands <- st %>% group_by(elev_band) %>% summarise(n = n(), v = mean(am_empty), .groups = "drop")
cat("\n02 shortage by band:\n"); print(bands)
band_lab <- bands %>% mutate(x = c(10, 30, 60), label = sprintf("%s\n평균 %s", elev_band, pct(v)))
p02 <- st %>% filter(elev_m <= X_MAX) %>%
  ggplot(aes(elev_m, am_empty)) +
  geom_vline(xintercept = c(20, 40), colour = muted, linetype = "dashed", linewidth = 0.4) +
  geom_point(alpha = 0.22, size = 1, colour = muted) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = red, linewidth = 1.6) +
  geom_label(data = band_lab, aes(x = x, y = 0.86, label = label), family = "Noto", size = 4.8,
             linewidth = 0, fill = "white", colour = ink, lineheight = 0.95) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 0.92)) + coord_cartesian(xlim = c(0, X_MAX)) +
  labs(x = "대여소 고도(m)", y = "출근 시간(7~9시) 품절 비율", caption = cap_above) + theme_slide()
save_fig(p02, "02_elevation_loess")

# ---- 03 map: smoothed shortage surface with district borders ----
fit_map <- loess(am_empty ~ lon * lat, data = st, span = 0.05, degree = 2)
grid <- expand_grid(lon = seq(min(st$lon), max(st$lon), length.out = 170),
                    lat = seq(min(st$lat), max(st$lat), length.out = 135))
km <- function(lat1, lon1, lat2, lon2) {
  6371 * 2 * asin(sqrt(sin((lat2 - lat1) * pi / 360)^2 +
                       cos(lat1 * pi / 180) * cos(lat2 * pi / 180) * sin((lon2 - lon1) * pi / 360)^2))
}
grid$near <- map2_dbl(grid$lat, grid$lon, ~ min(km(.x, .y, st$lat, st$lon)))
grid <- grid %>% filter(near <= 0.8) %>% mutate(fit = pmin(pmax(predict(fit_map, newdata = .), 0), 0.6))
dong <- vect("raw/admdong/HangJeongDong_ver20250701.geojson")
gu_v <- aggregate(dong[dong$sido == "11", ], "sggnm")
grid <- grid[!is.na(extract(gu_v[, "sggnm"], vect(grid, geom = c("lon", "lat"), crs = "EPSG:4326"))$sggnm), ]  # inside Seoul only
gu_line <- as.data.frame(geom(gu_v)) %>% mutate(grp = paste(geom, part, hole))
gu_lab <- as.data.frame(geom(centroids(gu_v, inside = TRUE))) %>%
  mutate(gu = sub("구$", "", gu_v$sggnm[geom]))
p03 <- ggplot() +
  geom_raster(data = grid, aes(lon, lat, fill = fit)) +
  geom_path(data = gu_line, aes(x, y, group = grp), colour = "#7d848b", linewidth = 0.35) +
  geom_text(data = gu_lab, aes(x, y, label = gu), family = "Noto", size = 3.9, colour = "#2f3438") +
  scale_fill_gradientn(colours = c("#f7f4ee", "#f2d2a9", "#e08a5b", "#b8402f", "#5e1a24"),
                       limits = c(0, 0.6), labels = c("0%", "15%", "30%", "45%", "60% 이상"),
                       breaks = c(0, 0.15, 0.3, 0.45, 0.6), name = "출근 시간 품절 비율") +
  coord_quickmap(expand = FALSE) +
  guides(fill = guide_colourbar(title.position = "top")) +
  labs(caption = "대여소 위치에 LOESS 곡면을 맞춘 값. 대여소에서 800m 넘게 떨어진 곳은 비웠다.") +
  theme_slide() + theme(axis.text = element_blank(), axis.title = element_blank(), panel.grid.major = element_blank(),
                        legend.key.width = unit(2.2, "cm"), legend.key.height = unit(0.3, "cm"))
save_fig(p03, "03_map", w = 9, h = 7.6)

# ---- 04 coplot: elevation vs shortage given subway distance ----
q <- quantile(st$subway_m, c(0, .25, .5, .75, 1))
lab4 <- c(sprintf("역까지 %dm 이하", round(q[2])), sprintf("%d~%dm", round(q[2]), round(q[3])),
          sprintf("%d~%dm", round(q[3]), round(q[4])), sprintf("%dm 초과", round(q[4])))
p04 <- st %>% mutate(g = cut(subway_m, q, labels = lab4, include.lowest = TRUE)) %>%
  filter(elev_m <= X_MAX) %>%
  ggplot(aes(elev_m, am_empty)) +
  geom_point(alpha = 0.2, size = 0.8, colour = muted) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = red, linewidth = 1.4) +
  facet_wrap(~ g, nrow = 1) +
  scale_x_continuous(breaks = c(0, 40, 80)) +
  scale_y_continuous(labels = scales::percent) + coord_cartesian(xlim = c(0, X_MAX), ylim = c(0, 0.8)) +
  labs(x = "대여소 고도(m)", y = "출근 시간 품절 비율", caption = cap_above) + theme_slide()
save_fig(p04, "04_coplot_subway", h = 5)

# ---- 05a consolidation candidates by elevation: how many are already running empty ----
cand <- st %>% filter(role %in% c("consolidate", "supply_gap_suspect")) %>%
  group_by(elev_band) %>%
  summarise(n = n(), gap = sum(role == "supply_gap_suspect"), .groups = "drop") %>%
  mutate(share = gap / n)
cat("\n05 consolidation candidates:", sum(cand$n), " of which supply-gap suspects:", sum(cand$gap), "\n"); print(cand)
p05 <- cand %>%
  transmute(elev_band, `아침에 자주 빔(공급 부족 의심)` = gap, `그렇지 않음` = n - gap, n, share) %>%
  pivot_longer(c(`아침에 자주 빔(공급 부족 의심)`, `그렇지 않음`), names_to = "k", values_to = "v") %>%
  mutate(k = factor(k, levels = c("그렇지 않음", "아침에 자주 빔(공급 부족 의심)")),
         elev_band = fct_rev(elev_band)) %>%
  ggplot(aes(v, elev_band, fill = k)) +
  geom_col(width = 0.62) +
  geom_text(data = cand %>% mutate(elev_band = fct_rev(elev_band)), inherit.aes = FALSE,
            aes(x = n + 6, y = elev_band, label = sprintf("%d곳 중 %d곳 (%s)", n, gap, pct(share, 1))),
            hjust = 0, family = "Noto", size = 5.2, colour = ink) +
  scale_fill_manual(values = c("그렇지 않음" = "#c9ced3", "아침에 자주 빔(공급 부족 의심)" = red), name = NULL,
                    breaks = c("아침에 자주 빔(공급 부족 의심)", "그렇지 않음")) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.45))) +
  labs(x = "통합 후보 대여소 수(이용 하위 20%, 300m 안에 다른 대여소)", y = "대여소 고도") +
  theme_slide() + theme(panel.grid.major.y = element_blank())
save_fig(p05, "05a_candidates_by_elevation", h = 4.6)

# ---- 05b mosaic plot of station role by elevation band (class method, backup) ----
roles_kr <- c(commute_core = "출퇴근 핵심", consolidate = "통합 후보", supply_gap_suspect = "공급 부족 의심",
              morning_gap = "아침 품절", other = "기타")
tab <- with(st, table(`역할` = factor(roles_kr[role], levels = roles_kr),
                      `대여소 고도` = factor(elev_band, labels = c("20m 미만", "20~40m", "40m 이상"))))
cat("\n05b role x elevation band:\n"); print(tab); print(chisq.test(tab))
# top labels sit over the first row's tiles, which are narrow for 40 m+, so they are set vertically;
# ragg renders rotated Korean text correctly (the base Windows png device does not)
ragg::agg_png(file.path(out, "05b_mosaic_roles.png"), width = 10, height = 6.4, units = "in", res = 200)
kr <- "Noto Sans KR"
mosaic(tab, shade = TRUE,
       legend = legend_resbased(fontsize = 13, fontfamily = kr, text = "피어슨 잔차", pvalue = FALSE),
       gp_labels = grid::gpar(fontsize = 15, fontfamily = kr),
       gp_varnames = grid::gpar(fontsize = 15, fontface = 2, fontfamily = kr),
       labeling_args = list(rot_labels = c(left = 0, top = 90), just_labels = c(left = "right", top = "left"),
                            varnames = c(FALSE, TRUE), offset_labels = c(left = 0.8, top = 0.3),
                            offset_varnames = c(top = 5.6)),
       margins = c(left = 8.5, top = 8.5))
invisible(dev.off())

# ---- 06 residual dependence: after elevation, slope adds nothing, climb still does ----
fit_elev <- loess(am_empty ~ elev_m, data = st, span = 0.75)
lab6 <- c(slope_bare = "대여소 주변 300m 평균 경사(도)", climb_bare = "도착한 이용이 올라온 높이(m)")
r6 <- st %>% mutate(resid = residuals(fit_elev)) %>%
  select(resid, slope_bare, climb_bare) %>%
  pivot_longer(-resid) %>% filter(!is.na(value)) %>%
  group_by(name) %>% filter(between(value, quantile(value, 0.01), quantile(value, 0.99))) %>% ungroup() %>%
  mutate(name = factor(lab6[name], levels = lab6))
p06 <- ggplot(r6, aes(value, resid)) +
  geom_hline(yintercept = 0, colour = muted, linewidth = 0.5) +
  geom_point(alpha = 0.16, size = 0.8, colour = muted) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = red, linewidth = 1.6) +
  facet_wrap(~ name, scales = "free_x") +
  scale_y_continuous(labels = function(x) paste0(ifelse(x > 0, "+", ""), round(x * 100), "%p")) +
  coord_cartesian(ylim = c(-0.25, 0.25)) +
  labs(x = NULL, y = "고도로 설명하고 남은 품절",
       caption = "고도로 품절을 LOESS 적합한 뒤의 잔차. 경사와 오르막은 건물을 뺀 지표면 기준. 양 끝 1%는 뺐다.") +
  theme_slide() + theme(panel.spacing.x = unit(2.4, "lines"))
save_fig(p06, "06_residual_slope_climb", h = 5.2)

# ---- 07 Tukey mean-difference plot: wet vs dry commute mornings ----
md <- st %>% filter(n_wet >= 30, !is.na(am_empty_wet)) %>%
  mutate(m = (am_empty + am_empty_wet) / 2, d = am_empty_wet - am_empty)
md_band <- md %>% group_by(elev_band) %>%
  summarise(n = n(), dry = mean(am_empty), wet = mean(am_empty_wet), diff = mean(d),
            r = cor(am_empty, am_empty_wet), .groups = "drop")
cat("\n07 wet vs dry (stations with >= 30 wet mornings):\n"); print(md_band)
hi <- md_band %>% filter(elev_band == "40m 이상")
p07 <- ggplot(md, aes(m, d)) +
  geom_hline(yintercept = 0, colour = muted, linewidth = 0.5) +
  geom_point(aes(colour = elev_band), alpha = 0.45, size = 1.2) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = ink, linewidth = 1.4) +
  annotate("label", x = 0.5, y = 0.31, family = "Noto", size = 4.8, hjust = 0, linewidth = 0, fill = "white",
           colour = ink, lineheight = 0.95,
           label = sprintf("40m 이상 대여소\n비 없는 날 %s, 비 온 날 %s\n같은 대여소끼리 상관 %.2f",
                           pct(hi$dry), pct(hi$wet), hi$r)) +
  scale_colour_manual(values = band_cols, name = "대여소 고도") +
  scale_x_continuous(labels = scales::percent) +
  scale_y_continuous(labels = function(x) paste0(ifelse(x > 0, "+", ""), round(x * 100), "%p")) +
  coord_cartesian(ylim = c(-0.4, 0.4)) +
  guides(colour = guide_legend(override.aes = list(alpha = 1, size = 3))) +
  labs(x = "두 날의 평균 품절 비율", y = "비 온 날 - 비 없는 날",
       caption = "출근 시간(6~10시)에 비가 온 평일이 30일 이상인 대여소. 가로 0선에 모일수록 비가 품절을 바꾸지 않는다.") +
  theme_slide()
save_fig(p07, "07_tukey_rain")

# ---- 08 coplot on the residential index ----
r8 <- st %>% filter(!is.na(res_index)) %>%
  mutate(res_group = cut(res_index, quantile(res_index, c(0, 1/3, 2/3, 1)), include.lowest = TRUE,
                         labels = c("업무지구 쪽 동네", "중간", "주거지 쪽 동네")))
cat("\n08 elevation OR per 10 m within residential terciles (90 m elevation, same controls):\n")
for (g in levels(r8$res_group)) {
  f <- glm(gap ~ I(elev_m / 10) + log2(subway_m) + log2(univ_m) + docks, family = binomial, data = filter(r8, res_group == g))
  cat(sprintf("  %s: n %d, OR %.2f (%.2f-%.2f)\n", g, nrow(filter(r8, res_group == g)), exp(coef(f)[2]),
              exp(confint.default(f)[2, 1]), exp(confint.default(f)[2, 2])))
}
p08 <- r8 %>% filter(elev_m <= X_MAX) %>%
  ggplot(aes(elev_m, am_empty)) +
  geom_point(alpha = 0.2, size = 0.8, colour = muted) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = red, linewidth = 1.4) +
  facet_wrap(~ res_group, nrow = 1) +
  scale_x_continuous(breaks = c(0, 40, 80)) +
  scale_y_continuous(labels = scales::percent) + coord_cartesian(xlim = c(0, X_MAX), ylim = c(0, 0.8)) +
  labs(x = "대여소 고도(m)", y = "출근 시간 품절 비율",
       caption = paste0("주거 지수 = 동의 새벽(2~4시) 인구 / 낮(13~15시) 인구(서울 생활인구)의 3분위.\n", cap_above)) +
  theme_slide()
save_fig(p08, "08_coplot_residential", h = 5)

# ---- 09 district level: mean slope vs rentals per station ----
gu_t <- read_csv("data/gu_terrain.csv", show_col_types = FALSE) %>%
  mutate(top3 = gu %in% c("강서구", "송파구", "영등포구"))
p09 <- ggplot(gu_t, aes(slope_bare, rent_per_station)) +
  geom_smooth(method = "loess", span = 0.9, se = FALSE, colour = "#9aa1a8", linewidth = 1.2) +
  geom_point(aes(size = stations, colour = top3), alpha = 0.85) +
  ggrepel::geom_text_repel(aes(label = gu, colour = top3), family = "Noto", size = 4.6, seed = 1,
                           min.segment.length = 0.3, box.padding = 0.6, point.padding = 0.5, show.legend = FALSE) +
  scale_colour_manual(values = c(`TRUE` = red, `FALSE` = blue), guide = "none") +
  scale_size_area(max_size = 9, name = "대여소 수") +
  guides(size = guide_legend(override.aes = list(colour = blue))) +
  scale_y_log10() +
  labs(x = "구 대여소 주변 평균 경사(도, 지표면)", y = "대여소당 평일 대여(건, 로그 축)",
       caption = "빨간색: 이용 상위 3개 구. 구가 25개뿐이고 평평한 구는 대부분 한강변이라 다른 이유가 섞였을 수 있다.") +
  theme_slide()
save_fig(p09, "09_gu_slope", h = 6)

# ---- backups ----
# B1 net change during the day by elevation
pb1 <- stations %>% filter(elev_m <= X_MAX) %>%
  ggplot(aes(elev_m, net_day)) +
  geom_hline(yintercept = 0, colour = muted, linewidth = 0.5) +
  geom_point(alpha = 0.2, size = 0.9, colour = muted) +
  geom_smooth(method = "loess", span = 0.75, se = FALSE, colour = red, linewidth = 1.6) +
  coord_cartesian(xlim = c(0, X_MAX), ylim = c(-25, 25)) +
  labs(x = "대여소 고도(m)", y = "평일 하루 순변화(반납 - 대여, 대)",
       caption = paste("0보다 아래면 하루 동안 자전거가 빠져나가는 대여소.", cap_above)) + theme_slide()
save_fig(pb1, "b1_net_change")

# B2 shortage by elevation band, month by month (all weekdays)
sm <- read_csv("data/station_month.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  inner_join(stations %>% select(station_no, elev_m), by = "station_no") %>% filter(use_day > 0) %>%
  mutate(elev_band = cut(elev_m, c(0, 20, 40, Inf), labels = names(band_cols), right = FALSE))
pb2 <- sm %>% group_by(month, elev_band) %>% summarise(v = mean(am_empty, na.rm = TRUE), .groups = "drop") %>%
  ggplot(aes(month, v, colour = elev_band)) +
  geom_line(linewidth = 1.2) + geom_point(size = 2.6) +
  scale_colour_manual(values = band_cols, name = "대여소 고도") +
  scale_x_continuous(breaks = 1:12, labels = paste0(1:12, "월")) +
  scale_y_continuous(labels = scales::percent, limits = c(0, NA)) +
  labs(x = NULL, y = "출근 시간 품절 비율(평균)", caption = "2025년 전체 평일 기준(비 온 날 포함).") + theme_slide()
save_fig(pb2, "b2_monthly_bands", h = 5)

# B3 predicted probability from the logistic model with the elevation x subway interaction
lr <- st %>% mutate(elev10 = elev_m / 10, l_sub = log2(subway_m), l_uni = log2(univ_m))
fit1 <- glm(gap ~ elev10 + l_sub + l_uni + docks, family = binomial, data = lr)
fit2 <- glm(gap ~ elev10 * l_sub + l_uni + docks, family = binomial, data = lr)
cat("\nB3 elevation OR per 10 m (main effects model):", round(exp(coef(fit1)["elev10"]), 2),
    "(", round(exp(confint.default(fit1)["elev10", ]), 2), ")\n")
nd <- expand_grid(elev10 = seq(0.5, 8, by = 0.1), l_sub = log2(c(200, 800)),
                  l_uni = median(lr$l_uni), docks = median(lr$docks)) %>%
  mutate(p = predict(fit2, newdata = ., type = "response"),
         g = factor(ifelse(l_sub == log2(200), "역까지 200m", "역까지 800m")))
pb3 <- ggplot(nd, aes(elev10 * 10, p, colour = g)) +
  geom_line(linewidth = 1.6) +
  scale_colour_manual(values = c("역까지 200m" = red, "역까지 800m" = blue), name = NULL) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
  labs(x = "대여소 고도(m)", y = "출근 시간 품절이 잦을 확률",
       caption = sprintf("로지스틱 회귀(고도 x 지하철 거리 + 대학 거리 + 거치대 수). 품절이 잦음 = 출근 시간 품절 비율 30%% 이상.")) +
  theme_slide()
save_fig(pb3, "b3_logit_prediction", h = 5)

# B4 binned check of the logistic fit
bin4 <- lr %>% mutate(p = fitted(fit1), bin = ntile(p, 20)) %>%
  group_by(bin) %>% summarise(p = mean(p), observed = mean(gap), n = n(), .groups = "drop")
pb4 <- ggplot(bin4, aes(p, observed)) +
  geom_abline(colour = muted, linewidth = 0.5) +
  geom_point(size = 3.2, colour = blue) +
  scale_x_continuous(labels = scales::percent) + scale_y_continuous(labels = scales::percent) +
  coord_equal(xlim = c(0, 0.8), ylim = c(0, 0.8)) +
  labs(x = "예측 확률(20개 구간 평균)", y = "실제 품절 대여소 비율",
       caption = "대각선에 가까울수록 모형이 잘 맞는다.") + theme_slide()
save_fig(pb4, "b4_logit_calibration", w = 6.4, h = 6.2)

cat("\nfigures written to", out, "\n")
