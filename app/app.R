# Look Before You Cut: Seoul's public bikes run out on the hills
# STA3115 Exploratory Data Analysis, Group 1. Shiny app that follows the talk:
#   1 Elevation  2 Map  3 Merge candidates  4 Who refills the hills  5 Station  6 About
# Data: app/data/ (scripts/16_app_data.R). Shortage = share of 07/08/09 h snapshots with zero bikes on
# 2025 weekday mornings with no rain 06-10 h at the nearest KMA station.
library(shiny)
library(bslib)
library(dplyr)
library(readr)
library(ggplot2)
library(leaflet)
library(DT)
library(forcats)

# ---- data ----
st <- read_csv("data/stations.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE) %>%
  mutate(band = cut(elev_m, c(-Inf, 20, 40, Inf), labels = c("Below 20 m", "20-40 m", "40 m and above"), right = FALSE),
         label = paste0(name, " (", gu_en, ")"))
hr <- read_csv("data/station_hour.csv", col_types = cols(station_no = col_character()), show_col_types = FALSE)
districts <- sort(unique(st$gu_en))
station_choices <- setNames(st$station_no, paste0(st$name, ", ", st$gu_en, "-gu (", st$station_no, ")"))

# ---- look: same palette and fonts as the slides ----
ink <- "#191f28"; muted <- "#6b7684"; grid_col <- "#e5e8eb"; red <- "#f04452"; blue <- "#3182f6"; light <- "#90c2ff"
band_cols <- c("Below 20 m" = light, "20-40 m" = blue, "40 m and above" = red)
theme_app <- function() {
  theme_minimal(base_size = 15) +
    theme(text = element_text(colour = ink), axis.text = element_text(colour = muted),
          panel.grid.minor = element_blank(), panel.grid.major = element_line(colour = grid_col, linewidth = 0.4),
          legend.position = "top", legend.justification = "left", plot.caption = element_text(colour = muted, hjust = 0))
}
theme_ui <- bs_theme(
  version = 5, bg = "#ffffff", fg = ink, primary = blue, danger = red, secondary = "#f2f4f6",
  base_font = font_collection(font_link("Inter", "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"),
                              font_link("Noto Sans KR", "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap"),
                              "sans-serif"),
  "border-radius" = "16px", "card-border-color" = "#ffffff", "card-cap-bg" = "#ffffff")
pct <- function(x, d = 1) paste0(formatC(100 * x, format = "f", digits = d), "%")
stat_box <- function(title, value, sub = NULL, colour = ink) {
  div(class = "stat-box", div(class = "stat-title", title), div(class = "stat-value", style = paste0("color:", colour), value),
      if (!is.null(sub)) div(class = "stat-sub", sub))
}
css <- "
.stat-box { background:#f4f8ff; border-radius:16px; padding:14px 18px; height:100%; }
.stat-title { color:#6b7684; font-size:.85rem; }
.stat-value { font-size:1.9rem; font-weight:700; letter-spacing:-.5px; line-height:1.2; }
.stat-sub { color:#6b7684; font-size:.8rem; }
.lead-note { color:#4e5968; max-width:62rem; }
.navbar-brand { font-weight:700; }
.station-tip { background:#191f28; color:#fff; border-radius:12px; padding:10px 14px; min-height:3.2rem; }
.station-tip b { font-size:1.05rem; }
"

# ---- UI ----
ui <- page_navbar(
  title = "Look Before You Cut", theme = theme_ui, fillable = FALSE,
  header = tags$head(tags$style(HTML(css))),

  nav_panel("1 Elevation",
    p(class = "lead-note mt-3", "Each dot is a station. The higher the station, the more often it has no bikes at commute time.",
      "Switch to wet mornings: demand falls by half or more, yet hill-tops stay empty."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        radioButtons("e_basis", "Mornings", c("Dry weekdays" = "dry", "Wet weekdays" = "wet", "All weekdays" = "all")),
        selectizeInput("e_gu", "Districts", districts, multiple = TRUE, options = list(placeholder = "All 25 districts")),
        sliderInput("e_elev", "Elevation (m)", min = 0, max = ceiling(max(st$elev_m)), value = c(0, ceiling(max(st$elev_m)))),
        checkboxInput("e_loess", "Show LOESS curve", TRUE),
        sliderInput("e_span", "LOESS span", min = 0.3, max = 1, value = 0.75, step = 0.05)),
      layout_columns(col_widths = c(4, 4, 4), uiOutput("e_b1"), uiOutput("e_b2"), uiOutput("e_b3")),
      card(plotOutput("e_plot", height = 470, hover = hoverOpts("e_hover", delay = 80, delayType = "debounce"))),
      div(class = "station-tip", uiOutput("e_tip")))),

  nav_panel("2 Map",
    p(class = "lead-note mt-3", "Shortages cluster in the northern foothills and on the south-east edge; the flat riverside is pale.",
      "Click a station for details."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        selectInput("m_metric", "Colour stations by", c("Morning shortage (dry)" = "am_empty", "Elevation (m)" = "elev_m",
                    "Rides a day" = "use_day", "Bikes added by riders a day" = "riders_in",
                    "Bikes added by other moves a day" = "other_in")),
        checkboxInput("m_cand", "Only merge candidates (bottom 20% of use, another station within 300 m)", FALSE),
        selectizeInput("m_gu", "Districts", districts, multiple = TRUE, options = list(placeholder = "All 25 districts"))),
      card(full_screen = TRUE, leafletOutput("m_map", height = 620)))),

  nav_panel("3 Merge candidates",
    p(class = "lead-note mt-3", "A ride-count rule picks low-use stations with a neighbour nearby. Many of them are already empty in the morning,",
      "most of all on the hills. Change the rule and see whether that holds."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        sliderInput("c_use", "Low use: bottom share of stations (%)", min = 5, max = 40, value = 20, step = 5),
        sliderInput("c_near", "Another station within (m)", min = 100, max = 500, value = 300, step = 50),
        sliderInput("c_gap", "Often empty: morning shortage of at least (%)", min = 10, max = 60, value = 30, step = 5)),
      layout_columns(col_widths = c(4, 4, 4), uiOutput("c_b1"), uiOutput("c_b2"), uiOutput("c_b3")),
      card(plotOutput("c_plot", height = 300)),
      card(card_header("Candidate stations, most often empty first"), DTOutput("c_table"),
           downloadButton("c_download", "Download as CSV", class = "btn-sm mt-2")))),

  nav_panel("4 Who refills the hills",
    p(class = "lead-note mt-3", "Over the day (06-23 h, dry weekdays), riders take bikes away from the hills and other moves,",
      "mostly rebalancing, bring them back. Between 7 and 9 am stock follows rides almost exactly, so the peak itself is not refilled."),
    layout_sidebar(
      sidebar = sidebar(width = 290,
        radioButtons("r_by", "Group stations by", c("Elevation band" = "band", "District" = "gu_en")),
        radioButtons("r_sort", "Sort districts by", c("Other moves" = "other", "Riders" = "riders", "Name" = "name"))),
      card(plotOutput("r_plot", height = 560)),
      p(class = "text-muted small", "Riders = returns minus rentals. Other moves = change in stock minus riders; they can also include repairs",
        "and gaps in the records. Stations with at least 30 dry weekdays."))),

  nav_panel("5 Station",
    p(class = "lead-note mt-3", "Look up any station: its terrain, how often it is empty, and when bikes leave and arrive."),
    layout_sidebar(
      sidebar = sidebar(width = 320,
        selectizeInput("s_id", "Station", choices = NULL, options = list(placeholder = "Type a name or number")),
        radioButtons("s_day", "Days", c("Weekdays" = "weekday", "Weekends" = "weekend"), inline = TRUE),
        p(class = "small text-muted", "Default: Singeumho Station exit 2 (Seongdong), the hill-top example in the talk.")),
      layout_columns(col_widths = c(3, 3, 3, 3), uiOutput("s_b1"), uiOutput("s_b2"), uiOutput("s_b3"), uiOutput("s_b4")),
      layout_columns(col_widths = c(7, 5),
        card(card_header("Rentals and returns by hour (2025 average)"), plotOutput("s_plot", height = 330)),
        card(card_header("Station facts"), tableOutput("s_facts"))))),

  nav_panel("About",
    div(class = "lead-note mt-3",
      h4("Look Before You Cut: Seoul's public bikes run out on the hills"),
      p("STA3115 Exploratory Data Analysis, Yonsei University, Fall 2026, Group 1."),
      h5("Question"),
      p("Ridership fell from 44.9 million rides (2023) to 37.4 million (2025). Merging the least-used stations is the obvious cut,",
        "but ride counts depend on supply: someone who finds no bike leaves no record. Are low-use stations short of demand, or of bikes?"),
      h5("Measures"),
      tags$ul(
        tags$li("Morning shortage: share of the 07, 08 and 09 h stock snapshots with zero bikes, on 2025 weekdays with no rain 06-10 h at the nearest KMA weather station."),
        tags$li("Often empty: morning shortage of 30% or more (9.8% of the 2,713 stations)."),
        tags$li("Merge candidate: bottom 20% of rides a day (24.2 or fewer) with another station within 300 m."),
        tags$li("Elevation: 90 m Copernicus DEM. Slope and climb: bare-earth terrain from Seoul 1:5,000 contours."),
        tags$li("Riders and other moves: daily (06-23 h) change in stock split into returns minus rentals and the rest.")),
      h5("Data (all public)"),
      tags$ul(
        tags$li("Seoul Open Data: station-to-station trips (OA-21229), bikes available per station by hour (OA-22382)."),
        tags$li("KMA automatic weather stations (27 in Seoul), hourly rain."),
        tags$li("Copernicus DEM 90 m; Seoul 1:5,000 contours and spot heights; Seoul living population; subway stations; universities.")),
      p(class = "small text-muted", "Observational data: the patterns are associations, not causes. Stock is recorded hourly, so short gaps are missed."))))

# ---- server ----
server <- function(input, output, session) {
  updateSelectizeInput(session, "s_id", choices = station_choices, selected = "04363", server = TRUE)

  # 1 Elevation
  e_data <- reactive({
    d <- st %>% mutate(y = switch(input$e_basis, dry = am_empty, wet = am_empty_wet, all = am_empty_all)) %>% filter(!is.na(y))
    if (length(input$e_gu)) d <- d %>% filter(gu_en %in% input$e_gu)
    d %>% filter(elev_m >= input$e_elev[1], elev_m <= input$e_elev[2])
  })
  band_box <- function(k) renderUI({
    d <- e_data() %>% filter(band == levels(st$band)[k])
    stat_box(levels(st$band)[k], if (nrow(d)) pct(mean(d$y)) else "none",
             paste(nrow(d), "stations, mean shortage"), colour = c(ink, blue, red)[k])
  })
  output$e_b1 <- band_box(1); output$e_b2 <- band_box(2); output$e_b3 <- band_box(3)
  output$e_plot <- renderPlot({
    d <- e_data()
    validate(need(nrow(d) >= 10, "Too few stations for this filter."))
    p <- ggplot(d, aes(elev_m, y)) +
      geom_vline(xintercept = c(20, 40), colour = muted, linetype = "dashed", linewidth = 0.4) +
      geom_point(aes(colour = band), alpha = 0.45, size = 1.6) +
      scale_colour_manual(values = band_cols, name = NULL) +
      scale_y_continuous(labels = function(x) pct(x, 0), limits = c(0, 1)) +
      labs(x = "Station elevation (m)", y = "Morning shortage (07-09 h)",
           caption = paste(nrow(d), "stations. Hover over a dot to name the station.")) + theme_app()
    if (isTRUE(input$e_loess) && nrow(d) >= 30)
      p <- p + geom_smooth(method = "loess", span = input$e_span, se = FALSE, colour = ink, linewidth = 1.3, formula = y ~ x)
    p
  }, res = 96)
  output$e_tip <- renderUI({
    h <- input$e_hover
    p0 <- if (!is.null(h)) nearPoints(e_data(), h, xvar = "elev_m", yvar = "y", maxpoints = 1, threshold = 8) else NULL
    if (is.null(p0) || !nrow(p0)) return(span("Hover over a dot to see the station."))
    HTML(sprintf("<b>%s</b> &nbsp; %s-gu &nbsp;|&nbsp; elevation %s m &nbsp;|&nbsp; morning shortage %s &nbsp;|&nbsp; %s rides a day%s",
                 htmltools::htmlEscape(p0$name), p0$gu_en, p0$elev_m, pct(p0$y), p0$use_day,
                 if (p0$use_day <= sort(st$use_day)[floor(nrow(st) * 0.2) + 1] && p0$nearest_station_m <= 300)
                   " &nbsp;|&nbsp; <span style='color:#ff9aa3'>merge candidate</span>" else ""))
  })

  # 2 Map
  m_data <- reactive({
    d <- st
    if (isTRUE(input$m_cand)) d <- d %>% filter(use_day <= sort(st$use_day)[floor(nrow(st) * 0.2) + 1], nearest_station_m <= 300)
    if (length(input$m_gu)) d <- d %>% filter(gu_en %in% input$m_gu)
    d %>% mutate(v = .data[[input$m_metric]]) %>% filter(!is.na(v))
  })
  output$m_map <- renderLeaflet({
    leaflet(options = leafletOptions(preferCanvas = TRUE)) %>% addProviderTiles(providers$CartoDB.Positron) %>%
      setView(126.99, 37.56, zoom = 11)
  })
  observe({
    d <- m_data()
    m <- input$m_metric
    pal <- switch(m,
      am_empty = colorNumeric(c("#e8f3ff", "#ffd4d8", red, "#a1192a"), c(0, 1)),
      elev_m = colorNumeric(c("#e8f3ff", light, blue, "#1b4a9c"), range(st$elev_m)),
      use_day = colorNumeric(c("#e8f3ff", light, blue, "#1b4a9c"), log10(range(st$use_day))),
      colorNumeric(c(red, "#ffd4d8", "#f2f4f6", "#c9e2ff", blue), c(-8, 8)))
    val <- switch(m, use_day = log10(d$v), am_empty = d$v, elev_m = d$v, pmin(pmax(d$v, -8), 8))
    title <- names(which(c("Morning shortage (dry)" = "am_empty", "Elevation (m)" = "elev_m", "Rides a day" = "use_day",
                           "Bikes added by riders a day" = "riders_in", "Bikes added by other moves a day" = "other_in") == m))
    pop <- sprintf("<b>%s</b><br>%s-gu, %s m<br>Morning shortage %s<br>%s rides a day<br>Riders %+.1f, other moves %+.1f bikes a day",
                   htmltools::htmlEscape(d$name), d$gu_en, d$elev_m, pct(d$am_empty), d$use_day,
                   coalesce(d$riders_in, 0), coalesce(d$other_in, 0))
    lp <- leafletProxy("m_map", data = d) %>% clearMarkers() %>% clearControls() %>%
      addCircleMarkers(~lon, ~lat, radius = 4.5, stroke = TRUE, weight = 0.6, color = "#ffffff", fillOpacity = 0.9,
                       fillColor = pal(val), popup = pop)
    if (m == "use_day") {
      lp %>% addLegend("bottomright", colors = pal(log10(c(2, 10, 50, 250))), labels = c("2", "10", "50", "250"), title = title)
    } else if (m %in% c("riders_in", "other_in")) {
      lp %>% addLegend("bottomright", pal = pal, values = c(-8, 8), title = paste(title, "(capped at 8)"))
    } else {
      lp %>% addLegend("bottomright", pal = pal, values = if (m == "am_empty") c(0, 1) else range(st$elev_m), title = title,
                       labFormat = if (m == "am_empty") labelFormat(suffix = "%", transform = function(x) 100 * x) else labelFormat())
    }
  })

  # 3 Merge candidates
  c_data <- reactive({
    q <- sort(st$use_day)[floor(nrow(st) * input$c_use / 100) + 1]
    st %>% filter(use_day <= q, nearest_station_m <= input$c_near) %>% mutate(gap = am_empty >= input$c_gap / 100)
  })
  output$c_b1 <- renderUI(stat_box("Merge candidates", nrow(c_data()),
                                   sprintf("bottom %d%% of use, another station within %d m", input$c_use, input$c_near)))
  output$c_b2 <- renderUI({
    d <- c_data()
    stat_box("Often empty in the morning", sprintf("%d (%s)", sum(d$gap), pct(mean(d$gap), 0)),
             sprintf("shortage of %d%% or more", input$c_gap), colour = red)
  })
  output$c_b3 <- renderUI({
    d <- c_data() %>% filter(band == "40 m and above")
    stat_box("Hill-top candidates already empty", if (nrow(d)) pct(mean(d$gap), 0) else "none",
             sprintf("%d of %d at 40 m and above", sum(d$gap), nrow(d)), colour = red)
  })
  output$c_plot <- renderPlot({
    d <- c_data() %>% count(band, gap, .drop = FALSE) %>%
      mutate(gap = factor(gap, c(FALSE, TRUE), c("Not often empty", "Often empty in the morning")), band = forcats::fct_rev(band))
    tot <- d %>% group_by(band) %>% summarise(n = sum(n), g = sum(n[gap == "Often empty in the morning"]), .groups = "drop")
    ggplot(d, aes(n, band, fill = gap)) + geom_col(width = 0.62) +
      geom_text(data = tot, aes(x = n, y = band, label = sprintf("  %d of %d (%s)", g, n, ifelse(n > 0, pct(g / n, 0), "-"))),
                inherit.aes = FALSE, hjust = 0, size = 4.6, colour = ink) +
      scale_fill_manual(values = c("Not often empty" = "#d1d6db", "Often empty in the morning" = red), name = NULL,
                        breaks = c("Often empty in the morning", "Not often empty")) +
      scale_x_continuous(expand = expansion(mult = c(0, 0.35))) + labs(x = "Merge candidates", y = NULL) + theme_app()
  }, res = 96)
  c_table <- reactive(c_data() %>% arrange(desc(am_empty)) %>%
    transmute(No = station_no, Station = name, District = gu_en, `Elevation (m)` = elev_m, `Rides a day` = use_day,
              `Morning shortage` = am_empty, `Nearest station (m)` = nearest_station_m, `Often empty` = ifelse(gap, "yes", "")))
  output$c_table <- renderDT(datatable(c_table(), rownames = FALSE, options = list(pageLength = 8, dom = "tip")) %>%
                               formatPercentage("Morning shortage", 1))
  output$c_download <- downloadHandler(function() sprintf("merge_candidates_%d_%dm_%d.csv", input$c_use, input$c_near, input$c_gap),
                                       function(file) write_csv(c_table(), file))

  # 4 Who refills the hills
  output$r_plot <- renderPlot({
    g <- input$r_by
    d <- st %>% filter(!is.na(riders_in)) %>% group_by(grp = .data[[g]]) %>%
      summarise(n = n(), riders = mean(riders_in), other = mean(other_in), .groups = "drop")
    if (g == "gu_en") {
      ord <- switch(input$r_sort, other = d$grp[order(d$other)], riders = d$grp[order(-d$riders)], name = sort(d$grp, decreasing = TRUE))
      d$grp <- factor(d$grp, ord)
    } else d$grp <- forcats::fct_rev(d$grp)
    dl <- bind_rows(d %>% transmute(grp, n, who = "Other moves (mostly rebalancing)", v = other),
                    d %>% transmute(grp, n, who = "Moved by riders", v = riders)) %>%
      mutate(who = factor(who, c("Other moves (mostly rebalancing)", "Moved by riders")))
    ggplot(dl, aes(v, grp, fill = who)) + geom_vline(xintercept = 0, colour = muted) +
      geom_col(position = position_dodge(width = 0.75), width = 0.7) +
      geom_text(aes(label = sprintf("%+.1f", v), hjust = ifelse(v >= 0, -0.15, 1.15)),
                position = position_dodge(width = 0.75), size = if (g == "band") 5 else 3.2, colour = ink) +
      scale_fill_manual(values = c("Moved by riders" = red, "Other moves (mostly rebalancing)" = blue), name = NULL,
                        breaks = c("Moved by riders", "Other moves (mostly rebalancing)")) +
      scale_x_continuous(expand = expansion(mult = 0.18)) +
      labs(x = "Bikes added to a station per day, 06-23 h (mean)", y = NULL) + theme_app() +
      theme(panel.grid.major.y = element_blank())
  }, res = 96)

  # 5 Station
  s_row <- reactive({ req(input$s_id); st %>% filter(station_no == input$s_id) })
  output$s_b1 <- renderUI({ s <- s_row(); stat_box("Elevation", paste(s$elev_m, "m"), sprintf("slope %.1f deg, climb %+.0f m", s$slope, s$climb)) })
  output$s_b2 <- renderUI({ s <- s_row(); stat_box("Morning shortage", pct(s$am_empty),
                                                    if (!is.na(s$am_empty_wet)) paste("wet mornings", pct(s$am_empty_wet)) else "dry weekdays",
                                                    colour = if (s$am_empty >= 0.3) red else ink) })
  output$s_b3 <- renderUI({ s <- s_row(); stat_box("Rides a day", s$use_day,
                                                    sprintf("more than %s of stations", pct(mean(st$use_day < s$use_day), 0))) })
  output$s_b4 <- renderUI({ s <- s_row(); stat_box("Other moves a day", if (is.na(s$other_in)) "n/a" else sprintf("%+.1f", s$other_in),
                                                    if (is.na(s$riders_in)) "" else sprintf("riders %+.1f", s$riders_in), colour = blue) })
  output$s_plot <- renderPlot({
    d <- hr %>% filter(station_no == input$s_id, daytype == input$s_day)
    validate(need(nrow(d) > 0, "No hourly records for this station."))
    dl <- bind_rows(d %>% transmute(hour, who = "Rentals (bikes leave)", v = dep), d %>% transmute(hour, who = "Returns (bikes arrive)", v = arr))
    ggplot(dl, aes(hour, v, colour = who)) + annotate("rect", xmin = 7, xmax = 9, ymin = -Inf, ymax = Inf, fill = "#f4f8ff") +
      geom_line(linewidth = 1.2) + geom_point(size = 1.6) +
      scale_colour_manual(values = c("Rentals (bikes leave)" = red, "Returns (bikes arrive)" = blue), name = NULL) +
      scale_x_continuous(breaks = seq(0, 23, 3), labels = paste0(seq(0, 23, 3), ":00")) +
      labs(x = NULL, y = "Trips per day", caption = "Shaded: 07-09 h, the commute hours behind the shortage measure.") + theme_app()
  }, res = 96)
  output$s_facts <- renderTable({
    s <- s_row()
    q20 <- sort(st$use_day)[floor(nrow(st) * 0.2) + 1]
    data.frame(Item = c("Station", "District", "Docks", "Nearest subway", "Nearest other bike station", "Merge candidate (20%, 300 m)",
                        "Often empty (30% or more)"),
               Value = c(paste(s$name, s$station_no), paste0(s$gu_en, "-gu"), s$docks, sprintf("%s, %d m", s$subway_name, s$subway_m),
                         paste(s$nearest_station_m, "m"), ifelse(s$use_day <= q20 & s$nearest_station_m <= 300, "yes", "no"),
                         ifelse(s$am_empty >= 0.3, "yes", "no")))
  }, colnames = FALSE, striped = FALSE, width = "100%")
}

shinyApp(ui, server)
