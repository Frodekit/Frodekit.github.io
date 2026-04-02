# SF Crime: Two Decades of Data

Live site: **[frodekit.github.io](https://frodekit.github.io)**

Data visualization project for DTU course 02806 — Social Data Analysis and Visualization (Spring 2026).

## About

Interactive exploration of San Francisco Police Department incident reports from 2003 to 2025, covering over 3 million incidents across 10 police districts.

## Visualizations

| Type | Description | File |
|------|-------------|------|
| Plotly choropleth | Larceny theft concentration by district | `visualizations/choropleth_larceny_ratio.html` |
| Plotly choropleth | Sunday car-theft risk by district | `visualizations/choropleth_sunday_theft.html` |
| Folium scatter | Drug offense locations (Jun–Jul 2016) | `visualizations/folium_drug_scatter.html` |
| Folium heatmap | Assault density heatmap (all years) | `visualizations/folium_assault_heatmap.html` |
| Plotly bar chart | Interactive hourly crime distribution | `visualizations/hourly_crime_interactive.html` |
| Plotly animated | Hourly patterns animated by year (2003–2025) | `visualizations/animated_hourly_patterns.html` |
| Matplotlib PNG | Yearly crime trends (static) | `images/yearly_crime_trends.png` |

## Focus Crimes

Assault · Robbery · Burglary · Larceny Theft · Motor Vehicle Theft · Drug Offense · Warrant · Other Offenses

## Data Sources

- [SFPD Incident Reports 2018–Present](https://data.sfgov.org/Public-Safety/Police-Department-Incident-Reports-2018-to-Present/wg3w-h783)
- [SFPD Incident Reports Historical 2003–2018](https://data.sfgov.org/Public-Safety/Police-Department-Incident-Reports-Historical-2003/tmnf-yvry)

## Built with

- Python (pandas, matplotlib, plotly, folium)
- Plain HTML/CSS — no build tools
- Hosted on GitHub Pages
