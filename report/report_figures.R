# Figures for the PDF report: Korean labels, no in-plot titles (captions live in the HTML), one shared style.
# Run from the report/ folder: Rscript report_figures.R
suppressPackageStartupMessages({
  library(tidyverse)
  library(broom)
  library(patchwork)
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

# station-level figures use the morning shortage on days without rain 06-10 h (scripts/10_aggregate_dry.py);
# the monthly figures (F2, F5) stay on all weekdays
dry <- read_csv("../data/stations_dry.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE)
stations <- read_csv("../data/stations.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  filter(use_day > 0) %>%
  select(-am_empty) %>%
  inner_join(dry %>% select(station_no, am_empty = am_empty_dry, climb_in_m), by = "station_no") %>%
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

# F7. terrain variables compared: AIC of a logistic model with one terrain variable (dry mornings)
terr <- read_csv("../data/station_terrain.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE)
d7 <- stations %>% inner_join(terr %>% select(station_no, elev30_m, slope_r300), by = "station_no") %>%
  filter(!is.na(am_empty), !is.na(climb_in_m)) %>%
  mutate(gap = as.integer(am_empty >= 0.3), l_sub = log2(subway_m), l_uni = log2(univ_m))
terms7 <- c("지형 변수 없음" = "1", "경사(주변 300m)" = "slope_r300", "고도(90m 격자)" = "elev_m",
            "고도(30m 격자)" = "elev30_m", "오르막" = "climb_in_m", "고도 + 오르막" = "elev30_m + climb_in_m")
aic7 <- tibble(model = names(terms7), aic = map_dbl(terms7, function(v)
  AIC(glm(as.formula(paste("gap ~ l_sub + l_uni + docks +", v)), family = binomial, data = d7)))) %>%
  mutate(model = fct_reorder(model, -aic), best = aic == min(aic))
p7 <- ggplot(aic7, aes(aic, model)) +
  geom_segment(aes(x = min(aic) - 40, xend = aic, yend = model), colour = grid_col, linewidth = 2.2) +
  geom_point(aes(colour = best), size = 3) +
  geom_text(aes(label = round(aic)), nudge_x = 18, hjust = 0, family = "Noto", size = 3.2, colour = ink) +
  scale_colour_manual(values = c(`TRUE` = "#c0392b", `FALSE` = "#4f7ea8"), guide = "none") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(x = "AIC (낮을수록 품절을 잘 설명)", y = NULL) + theme_report() + theme(panel.grid.major.y = element_blank())
save_fig(p7, "f7_terrain", w = 5.6, h = 2.8)
cat("F7 AIC:\n"); print(aic7)

# F8. morning rain: rentals fall a lot (left), hill-station shortage barely moves (right)
w8 <- read_csv("../data/weather_daily.csv", col_types = cols(aws_id = col_character(), date = col_date()), show_col_types = FALSE)
r8 <- read_csv("../data/daily_aws_rentals.csv", col_types = cols(aws_id = col_character(), date = col_date()), show_col_types = FALSE) %>%
  inner_join(w8, by = c("aws_id", "date")) %>%
  mutate(month = factor(lubridate::month(date)), wday = factor(lubridate::wday(date)),
         rain = cut(rain_am, c(-Inf, 0, 1, 5, Inf), labels = c("없음", "1mm 이하", "1~5mm", "5mm 초과")),
         temp = relevel(cut(temp_am, c(-Inf, 0, 10, 20, 25, 30, Inf)), "(20,25]"),
         wind = cut(wind_am, c(-Inf, 2, 4, Inf)))
f8 <- lm(log(rentals_am + 1) ~ rain + temp + wind + aws_id + month + wday, data = r8)
co <- summary(f8)$coefficients[grep("^rain", rownames(summary(f8)$coefficients)), ]
left <- tibble(rain = factor(sub("^rain", "", rownames(co)), levels = c("1mm 이하", "1~5mm", "5mm 초과")),
               pct = (exp(co[, 1]) - 1), lo = exp(co[, 1] - 1.96 * co[, 2]) - 1, hi = exp(co[, 1] + 1.96 * co[, 2]) - 1)
pa <- ggplot(left, aes(rain, pct)) +
  geom_col(fill = "#4f7ea8", width = 0.6) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.15, colour = ink) +
  geom_text(aes(y = pct / 2, label = scales::percent(pct, accuracy = 1)), colour = "white", family = "Noto", size = 3.6, fontface = "bold") +
  scale_y_continuous(labels = scales::percent, limits = c(-1, 0)) +
  labs(x = "출근 시간(6~10시) 강수량", y = "아침(7~9시) 대여 변화") + theme_report()
wet8 <- read_csv("../data/stations_wet.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  inner_join(stations %>% select(station_no, elev_band), by = "station_no") %>%
  group_by(elev_band) %>%
  summarise(`비 없음` = mean(am_empty_dry, na.rm = TRUE), `비 옴` = mean(am_empty_wet, na.rm = TRUE)) %>%
  pivot_longer(-elev_band, names_to = "cond", values_to = "v") %>%
  mutate(cond = factor(cond, levels = c("비 없음", "비 옴")))
pb <- ggplot(wet8, aes(elev_band, v, fill = cond)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.62) +
  geom_text(aes(label = scales::percent(v, accuracy = 0.1)), position = position_dodge(width = 0.7),
            vjust = -0.5, family = "Noto", size = 3, colour = ink) +
  scale_fill_manual(values = c("비 없음" = "#c0392b", "비 옴" = "#9fb7c9"), name = "출근 시간") +
  scale_y_continuous(labels = scales::percent, limits = c(0, 0.3)) +
  labs(x = "대여소 고도", y = "출근 시간 품절 비율") + theme_report()
save_fig(pa + pb + patchwork::plot_layout(widths = c(1, 1.15)), "f8_rain", w = 6.8, h = 3.2)
print(left); print(wet8)
