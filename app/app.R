# Where Do All the Ddareungi Go? Bikes roll downhill, and nobody rides them back up
# STA3115 Exploratory Data Analysis, Group 1. Shiny app that follows the final talk deck
# (https://for1809.github.io/sta3115-ddareungi-deck/):
#   1 Losing vs running out  2 Elevation  3 Map  4 Subway  5 Model  6 Starting stock  7 Groups  8 Station  About
# Data: app/data/, made by scripts/16_app_data.py from the deck's own tables.
#   Net outflow = rentals minus returns, in bikes (2024-2025 clear weekdays). Never divided by docks.
#   Empty share = share of the 7, 8 and 9 am hourly stock readings with no bike (2025 dry weekdays).
#   Runs out = empty share of at least 20% (the default line; the sliders move it).
library(shiny)
library(bslib)
library(dplyr)
library(readr)
library(ggplot2)
library(leaflet)

# ---- data ----
st <- read_csv("data/stations.csv", col_types = cols(st_id = col_character(), station_no = col_character(),
                                                       group = col_character(), band = col_character()), show_col_types = FALSE)
hr <- read_csv("data/station_hour.csv", col_types = cols(st_id = col_character()), show_col_types = FALSE)
stock <- read_csv("data/stock_hour.csv", show_col_types = FALSE)
curves <- read_csv("data/curves.csv", show_col_types = FALSE)
cuts <- curves %>% filter(curve == "subway_cut") %>% arrange(x) %>% pull(y)
q_lab <- c(paste0("under ", cuts[1], " m"), paste0(cuts[1], "–", cuts[2], " m"), paste0(cuts[2], "–", cuts[3], " m"),
           paste0(cuts[3], " m and over"))
st <- st %>% mutate(ebd = cut(elev, c(-Inf, 20, 40, Inf), labels = c("Below 20 m", "20–40 m", "40 m and above"), right = FALSE),
                    label = paste0(name, " (", gu, ")"))
trip <- st %>% filter(trip == 1)                              # the deck's 2,843 trip-data stations
districts <- sort(unique(st$gu))
station_choices <- with(st %>% filter(trip == 1 | !is.na(empty)) %>% arrange(name),
                        setNames(st_id, paste0(name, ", ", gu, " (", ifelse(is.na(station_no), st_id, station_no), ")")))

# ---- look: the deck's palette ----
ink <- "#191F28"; ink2 <- "#333D4B"; muted <- "#6B7684"; grid_col <- "#E5E8EB"
red <- "#F04452"; blue <- "#3182F6"; grey <- "#B0B8C1"; pink <- "#F7A1A8"; tint <- "#F4F8FF"; navy <- "#1B3A6B"
g_col <- c(G1 = red, G2 = "#FF9F1C", G3 = blue, G4 = "#8B5CF6")
g_lab <- c(G1 = "G1 Stays short", G2 = "G2 Refills by night", G3 = "G3 Collects bikes", G4 = "G4 Office hub")
band_col <- c("Below 20 m" = blue, "20–40 m" = pink, "40 m and above" = red)
theme_app <- function() {
  theme_minimal(base_size = 15) +
    theme(text = element_text(colour = ink), axis.text = element_text(colour = muted), axis.title = element_text(colour = ink2),
          panel.grid.minor = element_blank(), panel.grid.major = element_line(colour = grid_col, linewidth = 0.4),
          legend.position = "top", legend.justification = "left", plot.caption = element_text(colour = muted, hjust = 0))
}
theme_ui <- bs_theme(
  version = 5, bg = "#ffffff", fg = ink, primary = blue, danger = red, secondary = "#f2f4f6",
  base_font = font_collection(font_link("Inter", "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"),
                              font_link("Noto Sans KR", "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap"),
                              "sans-serif"),
  "border-radius" = "16px", "card-border-color" = "#ffffff", "card-cap-bg" = "#ffffff")
pct <- function(x, d = 0) paste0(formatC(100 * x, format = "f", digits = d), "%")
sgn <- function(x, d = 1) sub("^-", "−", sprintf(paste0("%+.", d, "f"), x))
num <- function(x) formatC(x, format = "d", big.mark = ",")
stat_box <- function(title, value, sub = NULL, colour = ink) {
  div(class = "stat-box", div(class = "stat-title", title), div(class = "stat-value", style = paste0("color:", colour), value),
      if (!is.null(sub)) div(class = "stat-sub", sub))
}
css <- "
.stat-box { background:#f4f8ff; border-radius:16px; padding:14px 18px; height:100%; }
.stat-title { color:#6b7684; font-size:.85rem; }
.stat-value { font-size:1.9rem; font-weight:700; letter-spacing:-.5px; line-height:1.2; }
.stat-sub { color:#6b7684; font-size:.8rem; }
.lead-note { color:#4e5968; max-width:64rem; }
.navbar-brand { font-weight:700; }
.station-tip { background:#191f28; color:#fff; border-radius:12px; padding:10px 14px; min-height:3.2rem; }
.station-tip b { font-size:1.05rem; }
.tbl-or td, .tbl-or th { padding:6px 10px; }
"
# hover read-out under a scatter: the nearest station to the mouse
tip <- function(h, d, xv, yv, fmt) {
  p0 <- if (!is.null(h)) nearPoints(d, h, xvar = xv, yvar = yv, maxpoints = 1, threshold = 8) else NULL
  if (is.null(p0) || !nrow(p0)) return(span("Hover over a dot to see the station."))
  HTML(fmt(p0))
}
hover_plot <- function(id, height = 470) plotOutput(id, height = height, hover = hoverOpts(paste0(id, "_hover"), delay = 80, delayType = "debounce"))
district_input <- function(id) selectizeInput(id, "Districts", districts, multiple = TRUE, options = list(placeholder = "All 25 districts"))
by_gu <- function(d, g) if (length(g)) filter(d, gu %in% g) else d

# ---- UI ----
ui <- page_navbar(
  title = "Where Do All the Ddareungi Go?", theme = theme_ui, fillable = FALSE,
  header = tags$head(tags$style(HTML(css))),

  nav_panel("1 Losing vs running out",
    p(class = "lead-note mt-3", "Two measures. Net outflow: rentals minus returns between 7 and 9 am, in bikes; above 0 the station loses bikes.",
      "Empty share: how often the station has no bike at all at 7, 8 or 9 am. Many stations lose bikes in the morning; far fewer run out."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        sliderInput("l_th", "\"Runs out\": empty share of at least (%)", min = 5, max = 50, value = 20, step = 1),
        district_input("l_gu"),
        p(class = "small text-muted", "Deck: empty in at least 1 of 5 morning readings (20%).")),
      layout_columns(col_widths = c(4, 4, 4), uiOutput("l_b1"), uiOutput("l_b2"), uiOutput("l_b3")),
      card(hover_plot("l_plot")),
      div(class = "station-tip", uiOutput("l_tip")),
      p(class = "small text-muted mt-2", "Net outflow: trips on 2024–2025 clear weekdays (378 days). Empty share: hourly stock, 2025 dry weekdays.",
        "Stations beyond ±30 bikes are drawn at the edge."))),

  nav_panel("2 Elevation",
    p(class = "lead-note mt-3", "Each dot is a station: elevation across, daily net outflow in bikes up. Low ground gains bikes, hill-tops lose them:",
      "bikes ride downhill and are not ridden back up."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        district_input("e_gu"),
        checkboxInput("e_loess", "Show the LOESS curve (all stations, span 0.75)", TRUE),
        p(class = "small text-muted", "The curve is the deck's fit to all 2,843 stations; the district filter changes the dots and the numbers.")),
      layout_columns(col_widths = c(4, 4, 4), uiOutput("e_b1"), uiOutput("e_b2"), uiOutput("e_b3")),
      card(hover_plot("e_plot")),
      div(class = "station-tip", uiOutput("e_tip")),
      p(class = "small text-muted mt-2", "Daily net outflow: mean rentals minus returns, 2024–2025 clear weekdays. Stations beyond −20/+30 drawn at the edge."))),

  nav_panel("3 Map",
    p(class = "lead-note mt-3", "Where bikes leave and where stations run out. Hover over a station for its name, click for its numbers."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        radioButtons("m_by", "Colour stations by", c("Daily net outflow (bikes)" = "net", "Empty share, 7–9 am" = "empty",
                                                     "Group (G1–G4)" = "group")),
        district_input("m_gu"),
        uiOutput("m_counts")),
      card(full_screen = TRUE, leafletOutput("m_map", height = 640)))),

  nav_panel("4 Subway",
    p(class = "lead-note mt-3", "Stations far from the subway lose the most bikes in the morning, but their empty share rises much less:",
      "net movement and running out tell different stories."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        checkboxInput("s_split", "Split each quarter by elevation band", FALSE),
        p(class = "small text-muted", "Four equal quarters of distance to the nearest subway station.")),
      layout_columns(col_widths = c(6, 6), uiOutput("s_b1"), uiOutput("s_b2")),
      layout_columns(col_widths = c(6, 6),
        card(card_header("Net outflow, 7–9 am (bikes a morning)"), plotOutput("s_net", height = 380)),
        card(card_header("Empty share, 7–9 am"), plotOutput("s_emp", height = 380))),
      p(class = "small text-muted", textOutput("s_note", inline = TRUE)))),

  nav_panel("5 Model",
    p(class = "lead-note mt-3", "Which station features go with running out? One logistic model with all three features, standardised.",
      "Move the line that defines running out and see whether elevation still comes first."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        sliderInput("g_th", "Runs out: empty share of at least (%)", min = 10, max = 50, value = 20, step = 5),
        p(class = "small text-muted", "Outcome: empty share ≥ the line (2025 dry weekdays). Features: elevation, local relief within 300 m,",
          "log distance to the nearest subway station. Wald 95% intervals.")),
      layout_columns(col_widths = c(3, 3, 3, 3), uiOutput("g_b1"), uiOutput("g_b2"), uiOutput("g_b3"), uiOutput("g_b4")),
      card(card_header("Odds ratio per 1 SD (95% CI), all three features in one model"), plotOutput("g_plot", height = 260)),
      card(card_header("Model table"), tableOutput("g_table"),
           p(class = "small text-muted", "ρ: Spearman correlation with the empty share, one feature at a time (does not depend on the line).")))),

  nav_panel("6 Starting stock",
    p(class = "lead-note mt-3", "Flat stations lose bikes but keep a buffer; hill-top stations start the morning with few bikes, so one or two rentals empty them."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        radioButtons("b_q", "Distance to the subway", setNames(c("3", "0", "1", "2", "all"),
                     c(paste0("Far: ", q_lab[4]), paste0("Near: ", q_lab[1]), q_lab[2], q_lab[3], "All stations"))),
        checkboxInput("b_mid", "Also show 20–40 m", FALSE),
        p(class = "small text-muted", "Flat: below 20 m. Hill: 40 m and above (bare-earth elevation). Mean hourly stock, 2025 dry weekdays.")),
      layout_columns(col_widths = c(6, 6), uiOutput("b_b1"), uiOutput("b_b2")),
      card(card_header("Bikes at the station by hour (mean)"), plotOutput("b_plot", height = 360)),
      card(card_header("Every station: bikes at 8 am against the empty share"), hover_plot("b_scatter", 430),
           div(class = "station-tip", uiOutput("b_scatter_tip"))),
      layout_columns(col_widths = c(6, 6), uiOutput("b_b3"), uiOutput("b_b4")))),

  nav_panel("7 Groups",
    p(class = "lead-note mt-3", "Two questions for every station: does it lose bikes in the morning (7–9 am net outflow > 0),",
      "and is it still short at the end of the day (full-day net outflow > 0)? Only the sign counts, so every station falls in one group."),
    layout_columns(col_widths = c(3, 3, 3, 3), uiOutput("t_b1"), uiOutput("t_b2"), uiOutput("t_b3"), uiOutput("t_b4")),
    layout_columns(col_widths = c(7, 5),
      card(card_header("Net outflow by hour, mean per station (bikes)"),
           checkboxGroupInput("t_show", NULL, setNames(names(g_lab), g_lab), selected = names(g_lab), inline = TRUE),
           plotOutput("t_prof", height = 360)),
      card(card_header("G1 against G2: both lose bikes every morning"), uiOutput("t_g12"))),
    card(card_header("Every station: morning against full-day net outflow"), hover_plot("t_scatter", 430),
         div(class = "station-tip", uiOutput("t_scatter_tip")))),

  nav_panel("8 Station",
    p(class = "lead-note mt-3", "Look up any station: its terrain, how many bikes it loses, how often it is empty, and when bikes leave and arrive."),
    layout_sidebar(
      sidebar = sidebar(width = 330,
        selectizeInput("x_id", "Station", choices = NULL, options = list(placeholder = "Type a name or number")),
        radioButtons("x_show", "Hourly chart", c("Net outflow" = "net", "Rentals and returns" = "both"), inline = TRUE),
        p(class = "small text-muted", "Default: Yeonga Elementary School (Seodaemun), a 54 m hill-top G1 station.")),
      layout_columns(col_widths = c(3, 3, 3, 3), uiOutput("x_b1"), uiOutput("x_b2"), uiOutput("x_b3"), uiOutput("x_b4")),
      layout_columns(col_widths = c(7, 5),
        card(card_header("By hour, 2024–2025 clear weekdays (mean per day)"), plotOutput("x_plot", height = 340)),
        card(card_header("Station facts"), tableOutput("x_facts"))))),

  nav_panel("About",
    div(class = "lead-note mt-3",
      h4("Where Do All the Ddareungi Go? Bikes roll downhill, and nobody rides them back up"),
      p("STA3115 Exploratory Data Analysis, Yonsei University, Fall 2026, Group 1. Final talk, 26 November 2026."),
      p("Slides: ", a("for1809.github.io/sta3115-ddareungi-deck", href = "https://for1809.github.io/sta3115-ddareungi-deck/", target = "_blank"),
        ". Code: ", a("github.com/for1809/sta3115-ddareungi", href = "https://github.com/for1809/sta3115-ddareungi", target = "_blank"), "."),
      h5("Story"),
      p("Many stations lose bikes in the morning, but mainly hill-top stations run out: bikes flow downhill and the hills start the day with few bikes.",
        "Stations that lose bikes in the morning and get none back by night (G1) sit higher than those that refill (G2)."),
      h5("Measures"),
      tags$ul(
        tags$li("Net outflow: rentals minus returns, in bikes, for the whole day and for 7–9 am. Above 0, the station loses bikes."),
        tags$li("Empty share: share of the 7, 8 and 9 am hourly stock readings with no bike at the station."),
        tags$li("Runs out: empty share of at least 20%, that is empty in at least one in five morning readings."),
        tags$li("Groups: G1 loses bikes in the morning and over the full day; G2 loses in the morning but not over the day; G3 loses in neither;",
                "G4 loses over the day but not in the morning. Only the sign of each net outflow counts."),
        tags$li("Elevation: from 1:5,000 contour maps. Local relief: elevation range within 300 m.")),
      h5("Data (all public)"),
      tags$ul(
        tags$li("Seoul Open Data: station-to-station trips, 2024–2025, clear weekdays (378 days, 2,843 stations)."),
        tags$li("Seoul Open Data: bikes available per station by hour, 2025 dry weekdays (empty share and stock)."),
        tags$li("KMA automatic weather stations (rain); Seoul 1:5,000 contours and spot heights; subway stations.")),
      p(class = "small text-muted", "Observational data: the patterns are associations, not causes. Stock is recorded hourly, so short gaps are missed.",
        "Net outflow describes user trips only; trucks and repairs are not in it."))))

# ---- server ----
server <- function(input, output, session) {
  updateSelectizeInput(session, "x_id", choices = station_choices, selected = "ST-224", server = TRUE)

  # 1 Losing vs running out
  l_data <- reactive(by_gu(st %>% filter(!is.na(empty), !is.na(am_net_d)), input$l_gu) %>%
                       mutate(x = pmax(pmin(am_net_d, 30), -30),
                              cls = ifelse(am_net_d <= 0, "gain", ifelse(empty >= input$l_th / 100, "out", "lose"))))
  output$l_b1 <- renderUI({ d <- l_data(); n <- sum(d$am_net_d > 0)
    stat_box("Lose bikes every morning", pct(n / nrow(d)), sprintf("net outflow above 0: %s of %s stations", num(n), num(nrow(d))), blue) })
  output$l_b2 <- renderUI({ d <- l_data(); n <- sum(d$am_net_d > 0); k <- sum(d$cls == "out")
    stat_box("Of those, run out", if (n) pct(k / n) else "none",
             sprintf("empty share ≥ %d%%: %s stations", input$l_th, num(k)), red) })
  output$l_b3 <- renderUI({ d <- l_data(); k <- sum(d$am_net_d <= 0 & d$empty >= input$l_th / 100)
    stat_box("Gain bikes yet run out", num(k), sprintf("of %s stations that gain bikes", num(sum(d$am_net_d <= 0))), muted) })
  output$l_plot <- renderPlot({
    d <- l_data(); th <- input$l_th / 100
    validate(need(nrow(d) >= 5, "Too few stations for this filter."))
    ggplot(d, aes(x, empty)) +
      annotate("rect", xmin = 0, xmax = 30, ymin = th, ymax = 1, fill = "#FFF1F2") +
      geom_point(data = filter(d, cls == "gain"), colour = grey, alpha = 0.4, size = 1.7) +
      geom_point(data = filter(d, cls != "gain"), aes(colour = cls), alpha = 0.6, size = 1.7) +
      geom_vline(xintercept = 0, colour = "#8B95A1", linewidth = 0.8) +
      geom_hline(yintercept = th, colour = ink2, linetype = "dashed", linewidth = 0.8) +
      scale_colour_manual(values = c(lose = blue, out = red), labels = c(lose = "Loses bikes, empty share below the line",
                          out = "Loses bikes and runs out"), name = NULL) +
      annotate("text", x = -29, y = 0.97, label = sprintf("gains bikes: %s", num(sum(d$cls == "gain"))), hjust = 0, colour = muted, fontface = "bold") +
      annotate("text", x = 29, y = 0.97, label = sprintf("loses bikes and runs out: %s", num(sum(d$cls == "out"))), hjust = 1, colour = red, fontface = "bold") +
      scale_x_continuous(breaks = seq(-30, 30, 10), labels = function(v) sub("^-", "−", ifelse(v > 0, paste0("+", v), v))) +
      scale_y_continuous(labels = function(v) pct(v), limits = c(0, 1)) +
      labs(x = "Net outflow, 7–9 am: bikes lost per morning", y = "Empty share, 7–9 am") + theme_app()
  }, res = 96)
  output$l_tip <- renderUI(tip(input$l_plot_hover, l_data(), "x", "empty", function(p0)
    sprintf("<b>%s</b> &nbsp; %s &nbsp;|&nbsp; net outflow 7–9 am %s bikes &nbsp;|&nbsp; empty share %s",
            htmltools::htmlEscape(p0$name), p0$gu, sgn(p0$am_net_d), pct(p0$empty, 1))))

  # 2 Elevation
  e_data <- reactive(by_gu(trip, input$e_gu) %>% mutate(y = pmax(pmin(day_net, 30), -20)))
  band_box <- function(k) renderUI({
    lv <- levels(st$ebd)[k]; d <- e_data() %>% filter(ebd == lv)
    if (!nrow(d)) return(stat_box(lv, "none"))
    stat_box(lv, paste(sgn(mean(d$day_net)), "bikes a day"),
             sprintf("mean net outflow, %s stations; %s end the day short", num(nrow(d)), pct(mean(d$day_net > 0))),
             colour = c(blue, ink, red)[k])
  })
  output$e_b1 <- band_box(1); output$e_b2 <- band_box(2); output$e_b3 <- band_box(3)
  output$e_plot <- renderPlot({
    d <- e_data()
    validate(need(nrow(d) >= 5, "Too few stations for this filter."))
    p <- ggplot(d, aes(elev, y)) +
      geom_hline(yintercept = 0, colour = "#8B95A1") +
      geom_vline(xintercept = c(20, 40), colour = muted, linetype = "dashed", linewidth = 0.4) +
      geom_point(aes(colour = day_net > 0), alpha = 0.45, size = 1.6) +
      scale_colour_manual(values = c(`TRUE` = red, `FALSE` = blue), labels = c(`TRUE` = "Loses bikes", `FALSE` = "Gains bikes"), name = NULL) +
      scale_y_continuous(breaks = seq(-20, 30, 10), labels = function(v) sub("^-", "−", ifelse(v > 0, paste0("+", v), v))) +
      labs(x = "Station elevation (m)", y = "Daily net outflow (bikes a day)",
           caption = paste(num(nrow(d)), "stations. Hover over a dot to name the station.")) + theme_app()
    if (isTRUE(input$e_loess))
      p <- p + geom_line(data = filter(curves, curve == "elev_day_net"), aes(x, y), colour = ink, linewidth = 1.4, inherit.aes = FALSE)
    p
  }, res = 96)
  output$e_tip <- renderUI(tip(input$e_plot_hover, e_data(), "elev", "y", function(p0)
    sprintf("<b>%s</b> &nbsp; %s &nbsp;|&nbsp; elevation %.0f m &nbsp;|&nbsp; daily net outflow %s bikes &nbsp;|&nbsp; group %s",
            htmltools::htmlEscape(p0$name), p0$gu, p0$elev, sgn(p0$day_net), p0$group)))

  # 3 Map
  m_data <- reactive({
    d <- if (input$m_by == "empty") filter(st, !is.na(empty)) else trip
    by_gu(d, input$m_gu)
  })
  output$m_counts <- renderUI({
    d <- m_data()
    txt <- switch(input$m_by,
      net = sprintf("%s lose more than 1 bike a day, %s gain more than 1, %s within ±1.", num(sum(d$day_net > 1)), num(sum(d$day_net < -1)),
                    num(sum(abs(d$day_net) <= 1))),
      empty = sprintf("%s of %s stations run out (empty share ≥ 20%%).", num(sum(d$empty >= 0.2)), num(nrow(d))),
      group = paste(sprintf("%s %s", names(g_lab), num(as.integer(table(factor(d$group, names(g_lab)))))), collapse = ", "))
    p(class = "small", txt)
  })
  # the map is drawn whole on each change (a proxy update is lost while the tab is still hidden)
  output$m_map <- renderLeaflet({
    d <- m_data(); m <- input$m_by
    if (m == "net") {
      d <- d %>% mutate(k = ifelse(day_net > 1, "lose", ifelse(day_net < -1, "gain", "even"))) %>%
        arrange(match(k, c("even", "gain", "lose")))
      fill <- unname(c(lose = red, gain = blue, even = grey)[d$k])
      legend <- list(colors = c(red, blue, grey), labels = c("Loses over 1 bike a day", "Gains over 1 bike a day", "Within ±1"),
                     title = "Daily net outflow")
    } else if (m == "empty") {
      brk <- c(0, 0.05, 0.1, 0.2, 0.4, 1.01)
      cols <- c("#E5E8EB", "#FFD4D8", "#F7A1A8", red, "#A1192A")
      d <- d %>% arrange(empty)
      fill <- cols[findInterval(d$empty, brk, rightmost.closed = TRUE)]
      legend <- list(colors = cols, labels = c("under 5%", "5–10%", "10–20%", "20–40%", "40% and over"), title = "Empty share, 7–9 am")
    } else {
      fill <- unname(g_col[d$group])
      legend <- list(colors = unname(g_col), labels = unname(g_lab), title = "Group")
    }
    lab <- sprintf("<b>%s</b><br>%s", htmltools::htmlEscape(d$name), d$gu)
    pop <- sprintf("<b>%s</b><br>%s, %s m<br>Daily net outflow %s bikes<br>Net outflow 7–9 am %s bikes<br>Empty share %s<br>Group %s",
                   htmltools::htmlEscape(d$name), d$gu, ifelse(is.na(d$elev), round(d$elev_bare), round(d$elev)),
                   ifelse(is.na(d$day_net), "n/a", sgn(d$day_net)), ifelse(is.na(d$am_net), "n/a", sgn(d$am_net)),
                   ifelse(is.na(d$empty), "n/a", pct(d$empty, 1)), ifelse(is.na(d$group), "n/a", d$group))
    leaflet(d, options = leafletOptions(preferCanvas = TRUE)) %>%
      addTiles(options = tileOptions(opacity = 0.55)) %>%   # OpenStreetMap, faded so the stations stand out
      fitBounds(min(st$lon), min(st$lat), max(st$lon), max(st$lat)) %>%
      addCircleMarkers(~lon, ~lat, radius = 4.5, stroke = TRUE, weight = 0.6, color = "#ffffff", fillOpacity = 0.9,
                       fillColor = fill, label = lapply(lab, HTML), popup = pop) %>%
      addLegend("bottomright", colors = legend$colors, labels = legend$labels, title = legend$title, opacity = 0.9)
  })

  # 4 Subway
  s_base <- st %>% filter(!is.na(subway_m), !is.na(elev_bare), !is.na(empty), !is.na(subq)) %>%
    mutate(q = factor(q_lab[as.integer(subq) + 1], q_lab),
           band = factor(c(flat = "Below 20 m", mid = "20–40 m", hill = "40 m and above")[band], levels(st$ebd)))
  s_sum <- reactive({
    g <- if (isTRUE(input$s_split)) c("q", "band") else "q"
    s_base %>% group_by(across(all_of(g))) %>%
      summarise(n = n(), net = mean(am_net_d, na.rm = TRUE), emp = mean(empty), .groups = "drop")
  })
  qs <- s_base %>% group_by(q) %>% summarise(net = mean(am_net_d, na.rm = TRUE), emp = mean(empty))
  output$s_b1 <- renderUI(stat_box("Net outflow, 7–9 am", sprintf("%s → %s bikes", sgn(qs$net[1]), sgn(qs$net[4])),
                                   paste("nearest quarter →", q_lab[4]), ink))
  output$s_b2 <- renderUI(stat_box("Empty share, 7–9 am", sprintf("%s → %s", pct(qs$emp[1], 1), pct(qs$emp[4], 1)),
                                   "nearest → farthest quarter: a much smaller contrast", red))
  s_bars <- function(v, lab_fun, ylab) renderPlot({
    d <- s_sum() %>% mutate(val = .data[[v]])
    p <- if (isTRUE(input$s_split)) {
      ggplot(d, aes(q, val, fill = band)) + geom_col(position = position_dodge(0.8), width = 0.75) +
        geom_text(aes(label = lab_fun(val), vjust = ifelse(val >= 0, -0.4, 1.3)), position = position_dodge(0.8), size = 3.4, colour = ink) +
        scale_fill_manual(values = band_col, name = NULL)
    } else {
      ggplot(d, aes(q, val, fill = if (v == "net") ifelse(val > 0, "lose", "gain") else "lose")) + geom_col(width = 0.62) +
        geom_text(aes(label = lab_fun(val), vjust = ifelse(val >= 0, -0.4, 1.3)), size = 5.5, fontface = "bold",
                  colour = if (v == "net") ifelse(d$val > 0, red, blue) else red) +
        scale_fill_manual(values = c(lose = red, gain = blue), guide = "none")
    }
    p + geom_hline(yintercept = 0, colour = "#8B95A1") +
      scale_y_continuous(labels = lab_fun, expand = expansion(mult = 0.15)) +
      scale_x_discrete(labels = function(v) sub(" m and over", " m\nand over", sub("^under ", "under\n", sub("–", "–\n", v)))) +
      labs(x = "Distance to the nearest subway station", y = ylab) + theme_app() + theme(panel.grid.major.x = element_blank())
  }, res = 96)
  output$s_net <- s_bars("net", function(v) sgn(v), "Bikes a morning")
  output$s_emp <- s_bars("emp", function(v) pct(v, 1), "Empty share")
  output$s_note <- renderText(sprintf("%s stations in four equal quarters of distance. Net outflow: trips, 2024–2025 clear weekdays; empty share: hourly stock, 2025 dry weekdays.",
                                      num(nrow(s_base))))

  # 5 Model
  g_base <- trip %>% filter(!is.na(empty), !is.na(elev), !is.na(relief), !is.na(sub_dist), sub_dist > 0) %>%
    mutate(lsub = log(sub_dist))
  g_rho <- sapply(c("elev", "relief", "lsub"), function(v) cor(g_base[[v]], g_base$empty, method = "spearman"))
  g_fit <- reactive({
    d <- g_base %>% mutate(y = as.integer(empty >= input$g_th / 100))
    validate(need(sum(d$y) >= 10 && sum(1 - d$y) >= 10, "Too few stations on one side of the line."))
    z <- d %>% mutate(across(c(elev, relief, lsub), ~ as.numeric(scale(.x))))
    m <- glm(y ~ elev + relief + lsub, family = binomial, data = z)
    m10 <- glm(y ~ I(elev / 10) + relief + lsub, family = binomial, data = d)
    cf <- summary(m)$coefficients[-1, ]
    r <- rank(fitted(m)); n1 <- sum(d$y); n0 <- nrow(d) - n1
    list(n = nrow(d), n1 = n1, auc = (sum(r[d$y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0),
         or10 = exp(coef(m10)[2]), sd_e = sd(d$elev),
         tab = data.frame(var = c("Elevation (m)", "Local relief within 300 m (m)", "Distance to nearest subway station (log)"),
                          rho = unname(g_rho), or = exp(cf[, 1]), lo = exp(cf[, 1] - 1.96 * cf[, 2]), hi = exp(cf[, 1] + 1.96 * cf[, 2]),
                          p = cf[, 4]))
  })
  output$g_b1 <- renderUI({ f <- g_fit(); stat_box("Elevation, odds ratio per 1 SD", sprintf("%.2f", f$tab$or[1]),
                                                   sprintf("95%% CI %.2f–%.2f; 1 SD = %.0f m", f$tab$lo[1], f$tab$hi[1], f$sd_e), red) })
  output$g_b2 <- renderUI({ f <- g_fit(); stat_box("Per 10 m of elevation", sprintf("×%.2f", f$or10), "odds of running out", red) })
  output$g_b3 <- renderUI({ f <- g_fit(); stat_box("AUC", sprintf("%.2f", f$auc), "how well the model separates the two groups") })
  output$g_b4 <- renderUI({ f <- g_fit(); stat_box("Stations that run out", num(f$n1), sprintf("of %s stations (%s)", num(f$n), pct(f$n1 / f$n))) })
  output$g_plot <- renderPlot({
    lv <- c("Elevation", "Local relief within 300 m", "Subway distance (log)")
    d <- g_fit()$tab %>% mutate(col = c(red, muted, muted), var = factor(lv, rev(lv)))
    ggplot(d, aes(or, var, colour = col)) + geom_vline(xintercept = 1, colour = "#8B95A1") +
      geom_errorbar(aes(xmin = lo, xmax = hi), width = 0.18, linewidth = 1, orientation = "y") +
      geom_point(size = 4) + scale_colour_identity() +
      geom_text(aes(label = sprintf("%.2f", or)), vjust = -1.2, colour = ink, size = 4.6) +
      scale_x_log10(breaks = c(0.5, 0.75, 1, 1.5, 2, 3, 4, 6)) +
      labs(x = "Odds ratio per 1 SD (log scale)", y = NULL) + theme_app()
  }, res = 96)
  output$g_table <- renderTable({
    g_fit()$tab %>% transmute(`Station feature` = var, `ρ` = sprintf("%.2f", rho),
                              `Odds ratio per 1 SD (95% CI)` = sprintf("%.2f (%.2f–%.2f)", or, lo, hi),
                              p = ifelse(p < 0.001, "< 0.001", sprintf("%.2f", p)))
  }, striped = FALSE, width = "100%", align = "lrrr", class = "tbl-or")

  # 6 Starting stock
  b_rows <- reactive({
    qs_ <- if (input$b_q == "all") 0:3 else as.integer(input$b_q)
    bands <- if (isTRUE(input$b_mid)) c("flat", "mid", "hill") else c("flat", "hill")
    stock %>% filter(q %in% qs_, band %in% bands) %>% group_by(band, hour) %>%
      summarise(mean = sum(mean * n) / sum(n), empty = sum(empty * n) / sum(n), .groups = "drop") %>%
      mutate(band = factor(c(flat = "Flat, below 20 m", mid = "20–40 m", hill = "Hill, 40 m and above")[band],
                           c("Flat, below 20 m", "20–40 m", "Hill, 40 m and above")))
  })
  b_box <- function(b, title, colour) renderUI({
    d <- b_rows() %>% filter(band == b)
    stat_box(title, sprintf("%.1f → %.1f bikes", d$mean[d$hour == 7], d$mean[d$hour == 9]),
             sprintf("7 am → 9 am; empty share %s over the 7, 8 and 9 am readings", pct(mean(d$empty[d$hour %in% 7:9]))), colour)
  })
  output$b_b1 <- b_box("Flat, below 20 m", "Flat stations", navy)
  output$b_b2 <- b_box("Hill, 40 m and above", "Hill-top stations", red)
  output$b_plot <- renderPlot({
    d <- b_rows()
    ggplot(d, aes(hour, mean, colour = band)) + annotate("rect", xmin = 7, xmax = 9, ymin = -Inf, ymax = Inf, fill = tint) +
      geom_line(linewidth = 1.3) + geom_point(size = 1.8) +
      geom_text(data = filter(d, hour %in% c(7, 9)), aes(label = sprintf("%.1f", mean)), vjust = -0.9, size = 4, show.legend = FALSE) +
      scale_colour_manual(values = c("Flat, below 20 m" = navy, "20–40 m" = pink, "Hill, 40 m and above" = red), name = NULL) +
      scale_x_continuous(breaks = seq(0, 23, 3), labels = paste0(seq(0, 23, 3), ":00")) +
      scale_y_continuous(limits = c(0, NA), expand = expansion(mult = c(0, 0.12))) +
      labs(x = NULL, y = "Bikes at the station", caption = "Shaded: 7–9 am. Mean hourly stock, 2025 dry weekdays.") + theme_app()
  }, res = 96)
  b_pts <- st %>% filter(!is.na(bikes8), !is.na(empty), !is.na(elev_bare)) %>%
    mutate(x = pmin(bikes8, 40), bd = factor(c(flat = "Below 20 m", mid = "20–40 m", hill = "40 m and above")[band], levels(st$ebd)))
  output$b_scatter <- renderPlot({
    ggplot(b_pts %>% arrange(match(bd, levels(bd))), aes(x, empty)) + geom_point(aes(colour = bd), alpha = 0.45, size = 1.6) +
      geom_line(data = filter(curves, curve == "bikes8_empty"), aes(x, y), colour = ink, linewidth = 1.4, inherit.aes = FALSE) +
      scale_colour_manual(values = band_col, name = NULL) +
      scale_y_continuous(labels = function(v) pct(v), limits = c(0, 1)) +
      labs(x = "Bikes at the station at 8 am, weekday mean (stations beyond 40 drawn at the edge)", y = "Empty share, 7–9 am",
           caption = paste(num(nrow(b_pts)), "stations. Line: LOESS (span 0.3), all stations. Bikes at 8 am: weekday mean, 2025.")) + theme_app()
  }, res = 96)
  output$b_scatter_tip <- renderUI(tip(input$b_scatter_hover, b_pts, "x", "empty", function(p0)
    sprintf("<b>%s</b> &nbsp; %s &nbsp;|&nbsp; %.0f m &nbsp;|&nbsp; %.1f bikes at 8 am &nbsp;|&nbsp; empty share %s",
            htmltools::htmlEscape(p0$name), p0$gu, p0$elev_bare, p0$bikes8, pct(p0$empty, 1))))
  output$b_b3 <- renderUI(stat_box("Empty share: fewer than 5 bikes at 8 am vs 10 or more",
                                   sprintf("%s vs %s", pct(mean(b_pts$empty[b_pts$bikes8 < 5])), pct(mean(b_pts$empty[b_pts$bikes8 >= 10]))),
                                   "few bikes on hand means a station runs out", red))
  output$b_b4 <- renderUI(stat_box("Median bikes at 8 am: hill-top vs flat ground",
                                   sprintf("%.0f vs %.0f", median(b_pts$bikes8[b_pts$band == "hill"]), median(b_pts$bikes8[b_pts$band == "flat"])),
                                   "40 m and above against below 20 m", ink))

  # 7 Groups
  t_n <- table(factor(trip$group, names(g_lab)))
  t_box <- function(g, sub) renderUI(stat_box(g_lab[[g]], num(t_n[[g]]), sprintf("%s of stations: %s", pct(t_n[[g]] / nrow(trip)), sub), g_col[[g]]))
  output$t_b1 <- t_box("G1", "loses bikes in the morning and over the day")
  output$t_b2 <- t_box("G2", "loses in the morning, refills by night")
  output$t_b3 <- t_box("G3", "gains in the morning and over the day")
  output$t_b4 <- t_box("G4", "gains in the morning, loses over the day")
  # mean per station and hour; a station with no trips in an hour counts as 0, as in the deck
  t_prof <- trip %>% select(st_id, group) %>% tidyr_cross(0:23) %>%
    left_join(hr %>% select(st_id, hour, net), by = c("st_id", "hour")) %>%
    group_by(group, hour) %>% summarise(net = mean(coalesce(net, 0)), .groups = "drop")
  output$t_prof <- renderPlot({
    d <- t_prof %>% filter(group %in% input$t_show)
    validate(need(nrow(d) > 0, "Pick at least one group."))
    ggplot(d, aes(hour, net, colour = group)) +
      annotate("rect", xmin = 6.5, xmax = 9.5, ymin = -Inf, ymax = Inf, fill = tint) +          # hours 7, 8, 9
      annotate("rect", xmin = 16.5, xmax = 19.5, ymin = -Inf, ymax = Inf, fill = "#FFF7EC") +   # hours 17, 18, 19
      geom_hline(yintercept = 0, colour = "#8B95A1") + geom_line(linewidth = 1.2) + geom_point(size = 1.5) +
      scale_colour_manual(values = g_col, labels = g_lab, name = NULL) +
      scale_x_continuous(breaks = seq(0, 23, 3), labels = paste0(seq(0, 23, 3), ":00")) +
      labs(x = NULL, y = "Net outflow (bikes; above 0 = loses)", caption = "Shaded: 7–9 am and 5–8 pm. 2024–2025 clear weekdays.") + theme_app()
  }, res = 96)
  output$t_g12 <- renderUI({
    g <- trip %>% filter(group %in% c("G1", "G2")) %>% group_by(group) %>%
      summarise(n = n(), pm = -mean(pm_net), am = mean(am_net), elev = median(elev), sub = median(sub_dist, na.rm = TRUE))
    g1 <- g[g$group == "G1", ]; g2 <- g[g$group == "G2", ]
    tagList(
      layout_columns(col_widths = c(6, 6),
        stat_box("G2: net gain, 5–8 pm", paste(sgn(g2$pm), "bikes"), "mean per station", g_col[["G2"]]),
        stat_box("G1: net gain, 5–8 pm", paste(sgn(g1$pm), "bikes"), "mean per station", g_col[["G1"]])),
      div(class = "mt-3"),
      layout_columns(col_widths = c(6, 6),
        stat_box("Median elevation, G1 vs G2", sprintf("%.0f m vs %.0f m", g1$elev, g2$elev), "G1 sits higher", ink),
        stat_box("Median subway distance", sprintf("%.0f m vs %.0f m", round(g1$sub, -1), round(g2$sub, -1)), "similar", muted)),
      p(class = "small text-muted mt-3", sprintf("Both lose bikes every morning (7–9 am: %s and %s bikes). G2 gets them back in the evening; G1 does not.",
                                                 sgn(g1$am), sgn(g2$am)),
        "Groups describe average user flow, not whether a station is empty or needs a truck."))
  })
  t_pts <- trip %>% mutate(x = pmax(pmin(am_net, 30), -30), y = pmax(pmin(day_net, 30), -30))
  output$t_scatter <- renderPlot({
    ggplot(t_pts, aes(x, y, colour = group)) + geom_hline(yintercept = 0, colour = "#8B95A1") + geom_vline(xintercept = 0, colour = "#8B95A1") +
      geom_point(alpha = 0.5, size = 1.6) +
      scale_colour_manual(values = g_col, labels = g_lab, name = NULL) +
      labs(x = "Net outflow, 7–9 am (bikes)", y = "Net outflow, whole day (bikes)",
           caption = "Stations beyond ±30 bikes drawn at the edge. Hover over a dot to name the station.") + theme_app()
  }, res = 96)
  output$t_scatter_tip <- renderUI(tip(input$t_scatter_hover, t_pts, "x", "y", function(p0)
    sprintf("<b>%s</b> &nbsp; %s &nbsp;|&nbsp; %s &nbsp;|&nbsp; 7–9 am %s, whole day %s bikes &nbsp;|&nbsp; %.0f m",
            htmltools::htmlEscape(p0$name), p0$gu, g_lab[[p0$group]], sgn(p0$am_net), sgn(p0$day_net), p0$elev)))

  # 8 Station
  x_row <- reactive({ req(input$x_id); st %>% filter(st_id == input$x_id) })
  output$x_b1 <- renderUI({ s <- x_row(); e <- coalesce(s$elev, s$elev_bare)
    stat_box("Elevation", if (is.na(e)) "n/a" else sprintf("%.0f m", e),
             if (is.na(s$relief)) "" else sprintf("local relief %.0f m within 300 m", s$relief)) })
  output$x_b2 <- renderUI({ s <- x_row()
    stat_box("Daily net outflow", if (is.na(s$day_net)) "n/a" else paste(sgn(s$day_net), "bikes"),
             if (is.na(s$am_net)) "" else sprintf("7–9 am %s bikes", sgn(s$am_net)),
             if (!is.na(s$day_net) && s$day_net > 0) red else blue) })
  output$x_b3 <- renderUI({ s <- x_row()
    stat_box("Empty share, 7–9 am", if (is.na(s$empty)) "n/a" else pct(s$empty, 1),
             if (is.na(s$empty)) "no 2025 stock readings" else if (s$empty >= 0.2) "runs out (20% or more)" else "below the 20% line",
             if (!is.na(s$empty) && s$empty >= 0.2) red else ink) })
  output$x_b4 <- renderUI({ s <- x_row()
    if (is.na(s$group)) return(stat_box("Group", "n/a", "too few days of trips"))
    stat_box("Group", g_lab[[s$group]], sprintf("rank: loses more bikes a day than %s of stations", pct(mean(trip$day_net < s$day_net))),
             g_col[[s$group]]) })
  output$x_plot <- renderPlot({
    d <- hr %>% filter(st_id == input$x_id)
    validate(need(nrow(d) > 0, "No trip records for this station."))
    d <- tibble(hour = 0:23) %>% left_join(d, by = "hour") %>% mutate(across(c(rent, ret, net), ~ coalesce(.x, 0)))
    base <- ggplot(d, aes(hour)) + annotate("rect", xmin = 6.5, xmax = 9.5, ymin = -Inf, ymax = Inf, fill = tint) +
      scale_x_continuous(breaks = seq(0, 23, 3), labels = paste0(seq(0, 23, 3), ":00")) + theme_app()
    if (input$x_show == "net") {
      base + geom_hline(yintercept = 0, colour = "#8B95A1") + geom_col(aes(y = net, fill = net > 0), width = 0.75) +
        scale_fill_manual(values = c(`TRUE` = red, `FALSE` = blue), labels = c(`TRUE` = "Loses bikes", `FALSE` = "Gains bikes"), name = NULL) +
        labs(x = NULL, y = "Net outflow (bikes)", caption = "Shaded: 7–9 am. Net outflow = rentals minus returns.")
    } else {
      dl <- bind_rows(d %>% transmute(hour, who = "Rentals (bikes leave)", v = rent), d %>% transmute(hour, who = "Returns (bikes arrive)", v = ret))
      base + geom_line(data = dl, aes(y = v, colour = who), linewidth = 1.2) + geom_point(data = dl, aes(y = v, colour = who), size = 1.6) +
        scale_colour_manual(values = c("Rentals (bikes leave)" = red, "Returns (bikes arrive)" = blue), name = NULL) +
        labs(x = NULL, y = "Trips per day", caption = "Shaded: 7–9 am.")
    }
  }, res = 96)
  output$x_facts <- renderTable({
    s <- x_row()
    f <- function(v, fmt) if (is.na(v)) "n/a" else sprintf(fmt, v)
    data.frame(Item = c("Station", "District", "Nearest subway", "Rides a day (rentals + returns)", "Net outflow, 5–8 pm",
                        "Bikes at 8 am (2025 weekday mean)", "Subway-distance quarter"),
               Value = c(paste(s$name, if (!is.na(s$station_no)) s$station_no else s$st_id), s$gu,
                         if (is.na(s$sub_dist) && is.na(s$subway_m)) "n/a" else sprintf("%s, %.0f m", s$subway, coalesce(s$sub_dist, s$subway_m)),
                         f(s$rides, "%.1f"), if (is.na(s$pm_net)) "n/a" else paste(sgn(s$pm_net), "bikes"),
                         f(s$bikes8, "%.1f"), if (is.na(s$subq)) "n/a" else q_lab[as.integer(s$subq) + 1]))
  }, colnames = FALSE, striped = FALSE, width = "100%")
}

# every station paired with every hour (base R, so no extra package)
tidyr_cross <- function(d, hours) {
  out <- d[rep(seq_len(nrow(d)), each = length(hours)), ]
  out$hour <- rep(hours, times = nrow(d))
  out
}

shinyApp(ui, server)
