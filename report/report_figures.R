# Figures for the PDF report: Korean labels, no in-plot titles (captions live in the HTML), one shared style.
# Run from the report/ folder: Rscript report_figures.R
suppressPackageStartupMessages({
  library(tidyverse)
  library(broom)
})

dir.create("figures", showWarnings = FALSE)
windowsFonts(Noto = windowsFont("Noto Sans KR"))
ink <- "#22262a"; muted <- "#6b7178"; grid_col <- "#e6e8ea"
band_cols <- c("20m 미만" = "#9fb7c9", "20~40m" = "#4f7ea8", "40m 이상" = "#c0392b")

theme_report <- function() {
  theme_minimal(base_size = 10.5, base_family = "Noto") +
    theme(text = element_text(colour = ink),
          axis.text = element_text(colour = muted),
          panel.grid.minor = element_blank(),
          panel.grid.major = element_line(colour = grid_col, linewidth = 0.35),
          strip.text = element_text(face = "bold", hjust = 0),
          legend.position = "top", legend.justification = "left",
          legend.title = element_text(size = 9.5), legend.text = element_text(size = 9.5),
          plot.margin = margin(4, 8, 4, 4))
}
save_fig <- function(p, name, w = 6.6, h = 3.6) {
  ggsave(file.path("figures", paste0(name, ".png")), p, width = w, height = h, dpi = 300, bg = "white")
}

stations <- read_csv("../data/stations.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  filter(use_day > 0) %>%
  mutate(elev_band = cut(elev_m, c(0, 20, 40, Inf), labels = names(band_cols), right = FALSE))
station_month <- read_csv("../data/station_month.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  inner_join(stations %>% select(station_no, elev_m, subway_m, univ_m, docks), by = "station_no") %>%
  filter(use_day > 0)
monthly <- read_csv("../data/monthly_age.csv", show_col_types = FALSE)

# F1. smoothed morning-shortage surface over Seoul
fit_map <- loess(am_empty ~ lon * lat, data = stations, span = 0.05, degree = 2)
grid <- expand_grid(lon = seq(min(stations$lon), max(stations$lon), length.out = 160),
                    lat = seq(min(stations$lat), max(stations$lat), length.out = 125))
km <- function(lat1, lon1, lat2, lon2) {
  6371 * 2 * asin(sqrt(sin((lat2 - lat1) * pi / 360)^2 +
                       cos(lat1 * pi / 180) * cos(lat2 * pi / 180) * sin((lon2 - lon1) * pi / 360)^2))
}
grid$near <- map2_dbl(grid$lat, grid$lon, ~ min(km(.x, .y, stations$lat, stations$lon)))
grid <- grid %>% filter(near <= 0.8) %>% mutate(fit = pmin(pmax(predict(fit_map, newdata = .), 0), 0.6))
gu_lab <- stations %>% group_by(gu) %>% summarise(lon = median(lon), lat = median(lat), .groups = "drop") %>%
  mutate(gu = sub("구$", "", gu))
p1 <- ggplot(grid, aes(lon, lat)) +
  geom_raster(aes(fill = fit)) +
  geom_contour(aes(z = fit), breaks = c(0.15, 0.3), colour = "white", linewidth = 0.25) +
  scale_fill_gradientn(colours = c("#f7f4ee", "#f2d2a9", "#e08a5b", "#b8402f", "#5e1a24"),
                       limits = c(0, 0.6), labels = scales::percent, name = "출근 시간 품절 비율") +
  geom_text(data = gu_lab, aes(label = gu), family = "Noto", size = 2.6, colour = "#3d4247", alpha = 0.85) +
  coord_quickmap() +
  guides(fill = guide_colourbar(title.position = "top")) +
  theme_report() + theme(axis.text = element_blank(), axis.title = element_blank(),
                         panel.grid.major = element_blank(),
                         legend.key.width = unit(1.6, "cm"), legend.key.height = unit(0.22, "cm"))
save_fig(p1, "f1_map", w = 6.2, h = 4.8)

# F2. shortage rate by elevation band, month by month
p2 <- station_month %>%
  mutate(elev_band = cut(elev_m, c(0, 20, 40, Inf), labels = names(band_cols), right = FALSE)) %>%
  group_by(month, elev_band) %>% summarise(v = mean(am_empty, na.rm = TRUE), .groups = "drop") %>%
  ggplot(aes(month, v, colour = elev_band)) +
  geom_line(linewidth = 0.8) + geom_point(size = 1.6) +
  scale_colour_manual(values = band_cols, name = "대여소 고도") +
  scale_x_continuous(breaks = 1:12, labels = paste0(1:12, "월")) +
  scale_y_continuous(labels = scales::percent, limits = c(0, NA)) +
  labs(x = NULL, y = "출근 시간 품절 비율(평균)") + theme_report()
save_fig(p2, "f2_bands")

# F3. coplot: elevation vs shortage within subway-distance quartiles
q <- quantile(stations$subway_m, c(0, .25, .5, .75, 1))
lab <- c(sprintf("역까지 %dm 이하", round(q[2])), sprintf("%d~%dm", round(q[2]), round(q[3])),
         sprintf("%d~%dm", round(q[3]), round(q[4])), sprintf("%dm 초과", round(q[4])))
p3 <- stations %>%
  mutate(g = cut(subway_m, q, labels = lab, include.lowest = TRUE)) %>%
  ggplot(aes(elev_m, am_empty)) +
  geom_point(alpha = 0.18, size = 0.5, colour = muted) +
  geom_smooth(method = "loess", se = FALSE, colour = "#c0392b", linewidth = 0.8) +
  facet_wrap(~ g, nrow = 1) +
  scale_y_continuous(labels = scales::percent) + coord_cartesian(xlim = c(0, 100), ylim = c(0, 0.8)) +
  labs(x = "대여소 고도(m)", y = "출근 시간 품절 비율") + theme_report()
save_fig(p3, "f3_coplot", h = 3.2)

# F4. predicted probability from the logistic model with interaction
lr <- stations %>% filter(!is.na(am_empty)) %>%
  mutate(gap = as.integer(am_empty >= 0.3), elev10 = elev_m / 10, l_sub = log2(subway_m), l_uni = log2(univ_m))
fit2 <- glm(gap ~ elev10 * l_sub + l_uni + docks, family = binomial, data = lr)
nd <- expand_grid(elev10 = seq(0.5, 8, by = 0.1), l_sub = log2(c(200, 800)),
                  l_uni = median(lr$l_uni), docks = median(lr$docks)) %>%
  mutate(p = predict(fit2, newdata = ., type = "response"),
         g = factor(ifelse(l_sub == log2(200), "역까지 200m", "역까지 800m")))
p4 <- ggplot(nd, aes(elev10 * 10, p, colour = g)) +
  geom_line(linewidth = 1) +
  scale_colour_manual(values = c("역까지 200m" = "#c0392b", "역까지 800m" = "#4f7ea8"), name = NULL) +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
  labs(x = "대여소 고도(m)", y = "출근 시간 품절이 잦을 확률") + theme_report()
save_fig(p4, "f4_logit", w = 5.2, h = 3.4)

# F5. elevation odds ratio estimated separately for each month
p5 <- station_month %>% filter(!is.na(am_empty)) %>%
  mutate(gap = as.integer(am_empty >= 0.3), elev10 = elev_m / 10, l_sub = log2(subway_m), l_uni = log2(univ_m)) %>%
  group_by(month) %>%
  group_modify(~ tidy(glm(gap ~ elev10 + l_sub + l_uni + docks, family = binomial, data = .x),
                      exponentiate = TRUE, conf.int = TRUE)) %>%
  filter(term == "elev10") %>%
  ggplot(aes(month, estimate)) +
  geom_hline(yintercept = 1, colour = muted, linewidth = 0.4) +
  geom_pointrange(aes(ymin = conf.low, ymax = conf.high), colour = ink, size = 0.3, linewidth = 0.6) +
  scale_x_continuous(breaks = 1:12, labels = paste0(1:12, "월")) +
  scale_y_continuous(limits = c(0.9, NA)) +
  labs(x = NULL, y = "고도 10m당 오즈비(95% 구간)") + theme_report()
save_fig(p5, "f5_monthly_or", h = 3.0)

# F6. share of trips by age band
age_lab <- c("20대" = "20대", "30대" = "30대", "40대" = "40대", "50대" = "50대", "60대" = "60대", "70대이상" = "70대 이상")
p6 <- monthly %>% filter(age %in% names(age_lab)) %>%
  group_by(month) %>% mutate(share = trips / sum(trips)) %>% ungroup() %>%
  mutate(date = as.Date(paste0(month, "-01")), age = factor(age_lab[age], levels = age_lab)) %>%
  ggplot(aes(date, share, colour = age)) +
  geom_line(linewidth = 0.7) +
  scale_colour_manual(values = c("#c0392b", "#e08a5b", "#4f7ea8", "#2e5c7f", "#8c9aa6", "#c3cbd2"), name = NULL) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = NULL, y = "이용 비중") + theme_report() +
  guides(colour = guide_legend(nrow = 1))
save_fig(p6, "f6_age", w = 6.6, h = 2.5)

cat("figures written\n")
