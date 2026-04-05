"""
Export script for SF Crime Data Visualizations
Generates HTML files for the GitHub Pages site.
Run from this directory with Python 3.13.
"""

import json
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap, HeatMapWithTime

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = r"c:/Users/frode/OneDrive/Skrivebord/DTU - Kandidat/02806 Social Data Analysis and Visualization"
GEOJSON_PATH = os.path.join(DATA_DIR, "sfpd.geojson.txt")
CSV_PATH = os.path.join(DATA_DIR, "sf_crime_merged_2003_present.csv")
VIZ_DIR = os.path.join(BASE, "visualizations")
IMG_DIR = os.path.join(BASE, "images")

os.makedirs(VIZ_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# ── Focus crimes (Unified Category names) ─────────────────────────────────
focus_crimes = [
    'Assault', 'Robbery', 'Burglary', 'Larceny Theft',
    'Motor Vehicle Theft', 'Drug Offense', 'Warrant', 'Other Offenses'
]

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading crime data (~3M rows, may take a moment)...")
df_all = pd.read_csv(CSV_PATH, low_memory=False)
print(f"Loaded {len(df_all):,} rows")

# ── Load GeoJSON ───────────────────────────────────────────────────────────
with open(GEOJSON_PATH, encoding='utf-8') as f:
    geojson = json.load(f)

for feature in geojson['features']:
    feature['id'] = feature['properties']['DISTRICT']

# ────────────────────────────────────────────────────────────────────────────
# VIZ 1: Choropleth — crime ratio by district (Larceny Theft)
# ────────────────────────────────────────────────────────────────────────────
print("\n[1/6] Choropleth: crime ratio by district...")

df_unified = df_all[['Unified Category', 'PdDistrict']].dropna()
crime_type = 'Larceny Theft'

df_filtered = df_unified[df_unified['Unified Category'] == crime_type]
crime_by_district = df_filtered['PdDistrict'].str.upper().value_counts()
total_crime_count = len(df_filtered)
p_crime_given_district = crime_by_district / total_crime_count

all_crimes_by_district = df_unified['PdDistrict'].str.upper().value_counts()
total_all_crimes = len(df_unified)
ratio = p_crime_given_district / (total_crime_count / total_all_crimes)

crime_ratio_df = pd.DataFrame({
    'DISTRICT': ratio.index,
    'ratio': ratio.values
})

fig_ratio = px.choropleth_mapbox(
    crime_ratio_df,
    geojson=geojson,
    locations='DISTRICT',
    color='ratio',
    color_continuous_scale="RdBu_r",
    range_color=(0.5, 1.5),
    mapbox_style="carto-positron",
    zoom=11,
    center={"lat": 37.7749, "lon": -122.4194},
    opacity=0.7,
    labels={'ratio': 'Ratio vs. city avg'},
    title=f'Larceny Theft concentration by district (ratio vs. city average)'
)
fig_ratio.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
fig_ratio.write_html(os.path.join(VIZ_DIR, "choropleth_larceny_ratio.html"), include_plotlyjs='cdn')
print("  Saved choropleth_larceny_ratio.html")

# ────────────────────────────────────────────────────────────────────────────
# VIZ 2: Choropleth — Sunday car theft risk
# ────────────────────────────────────────────────────────────────────────────
print("\n[2/6] Choropleth: Sunday car theft risk...")

df_mv = df_all[['DayOfWeek', 'Unified Category', 'PdDistrict']].dropna()
sunday_mask = df_mv['DayOfWeek'].astype(str).str.strip().str.upper() == 'SUNDAY'
theft_mask = df_mv['Unified Category'] == 'Motor Vehicle Theft'
sunday_theft = df_mv.loc[sunday_mask & theft_mask].copy()
sunday_theft['DISTRICT'] = sunday_theft['PdDistrict'].str.upper()

valid_districts = {f['properties']['DISTRICT'] for f in geojson['features']}
sunday_theft = sunday_theft[sunday_theft['DISTRICT'].isin(valid_districts)]

counts = (
    sunday_theft['DISTRICT'].value_counts()
    .reindex(sorted(valid_districts), fill_value=0)
    .rename_axis('DISTRICT').reset_index(name='theft_count')
)
safest = counts.loc[counts['theft_count'].idxmin(), 'DISTRICT']
worst  = counts.loc[counts['theft_count'].idxmax(), 'DISTRICT']

fig_sunday = px.choropleth_mapbox(
    counts, geojson=geojson, locations='DISTRICT', color='theft_count',
    color_continuous_scale='RdYlGn_r',
    range_color=(int(counts.theft_count.min()), int(counts.theft_count.max())),
    mapbox_style="carto-positron", zoom=11,
    center={"lat": 37.7749, "lon": -122.4194}, opacity=0.75,
    labels={'theft_count': 'Sunday vehicle thefts'},
    title=f'Sunday car-theft risk by district | Safest: {safest} | Worst: {worst}'
)
fig_sunday.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
fig_sunday.write_html(os.path.join(VIZ_DIR, "choropleth_sunday_theft.html"), include_plotlyjs='cdn')
print("  Saved choropleth_sunday_theft.html")

# ────────────────────────────────────────────────────────────────────────────
# VIZ 3: Folium — point scatter map (Drug Offense, Jun-Jul 2016)
# ────────────────────────────────────────────────────────────────────────────
print("\n[3/6] Folium: Drug Offense scatter map...")

df_coords = df_all[['Unified Category', 'Date', 'X', 'Y']].dropna(subset=['X', 'Y'])
df_drugs = df_coords[
    (df_coords['Unified Category'] == 'Drug Offense') &
    (pd.to_datetime(df_coords['Date'], errors='coerce') >= '2016-06-01') &
    (pd.to_datetime(df_coords['Date'], errors='coerce') < '2016-08-01')
].copy()

# Filter to valid SF coordinates
df_drugs = df_drugs[(df_drugs['Y'] > 37) & (df_drugs['Y'] < 38) &
                    (df_drugs['X'] > -123) & (df_drugs['X'] < -122)]

sf_map_scatter = folium.Map(
    location=[37.7749, -122.4194], zoom_start=13,
    tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attr='&copy; OpenStreetMap contributors &copy; CARTO'
)
for _, row in df_drugs.head(1000).iterrows():
    folium.CircleMarker(
        location=[row['Y'], row['X']], radius=3, color='#e94560',
        fill=True, fillColor='#e94560', fillOpacity=0.5, weight=0
    ).add_to(sf_map_scatter)

sf_map_scatter.save(os.path.join(VIZ_DIR, "folium_drug_scatter.html"))
print(f"  Saved folium_drug_scatter.html ({min(1000, len(df_drugs))} points)")

# ────────────────────────────────────────────────────────────────────────────
# VIZ 4: Folium — crime heatmap (Assault, all years)
# ────────────────────────────────────────────────────────────────────────────
print("\n[4/6] Folium: Assault heatmap...")

df_assault = df_all[df_all['Unified Category'] == 'Assault'][['X', 'Y']].dropna()
df_assault = df_assault[
    (df_assault['Y'] > 37) & (df_assault['Y'] < 38) &
    (df_assault['X'] > -123) & (df_assault['X'] < -122)
]

sf_heatmap = folium.Map(
    location=[37.7749, -122.4194], zoom_start=12,
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr='&copy; OpenStreetMap contributors &copy; CARTO'
)
heat_data = df_assault[['Y', 'X']].sample(min(20000, len(df_assault)), random_state=42).values.tolist()
HeatMap(heat_data, radius=8, blur=10, max_zoom=1).add_to(sf_heatmap)
sf_heatmap.save(os.path.join(VIZ_DIR, "folium_assault_heatmap.html"))
print(f"  Saved folium_assault_heatmap.html")

# ────────────────────────────────────────────────────────────────────────────
# VIZ 5: Plotly — interactive hourly crime bar chart
# ────────────────────────────────────────────────────────────────────────────
print("\n[5/6] Plotly: interactive hourly bar chart...")

df_focus = df_all[df_all['Unified Category'].isin(focus_crimes)].copy()
df_focus['Incident Datetime'] = pd.to_datetime(df_focus['Incident Datetime'], errors='coerce')
df_focus = df_focus.dropna(subset=['Incident Datetime'])
df_focus['Hour'] = df_focus['Incident Datetime'].dt.hour

crime_by_hour = (
    df_focus.groupby(['Hour', 'Unified Category'])
    .size().unstack(fill_value=0)
    .reindex(range(24), fill_value=0)
)
normalized = crime_by_hour.div(crime_by_hour.sum(axis=1), axis=0)
df_norm = normalized.reset_index().melt(id_vars='Hour', var_name='CrimeType', value_name='NormalizedCount')

fig_hourly = px.bar(
    df_norm, x='Hour', y='NormalizedCount', color='CrimeType',
    title='When Do Crimes Happen? Hourly Distribution by Crime Type',
    labels={'Hour': 'Hour of Day', 'NormalizedCount': 'Share of Daily Total', 'CrimeType': 'Crime Type'},
    barmode='overlay', opacity=0.7,
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_hourly.update_traces(visible='legendonly')
fig_hourly.update_layout(
    xaxis=dict(tickmode='linear', tick0=0, dtick=1, range=[-0.5, 23.5]),
    yaxis=dict(range=[0, 0.12]),
    legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
    paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e',
    font=dict(color='white'),
    title_font=dict(size=16)
)
fig_hourly.write_html(os.path.join(VIZ_DIR, "hourly_crime_interactive.html"), include_plotlyjs='cdn')
print("  Saved hourly_crime_interactive.html")

# ────────────────────────────────────────────────────────────────────────────
# VIZ 6: Plotly — animated hourly crime patterns over years
# ────────────────────────────────────────────────────────────────────────────
print("\n[6/6] Plotly: animated hourly patterns by year...")

df_focus['Year'] = df_focus['Incident Datetime'].dt.year
df_focus_years = df_focus[df_focus['Year'] < 2026].copy()

crime_by_year_hour = (
    df_focus_years.groupby(['Year', 'Hour', 'Unified Category'])
    .size().reset_index(name='Count')
)
yearly_totals = crime_by_year_hour.groupby(['Year', 'Unified Category'])['Count'].transform('sum')
crime_by_year_hour['NormalizedCount'] = crime_by_year_hour['Count'] / yearly_totals
crime_by_year_hour = crime_by_year_hour.rename(columns={'Unified Category': 'CrimeType'})

from itertools import product
years = sorted(crime_by_year_hour['Year'].unique())
all_combos = pd.DataFrame(
    list(product(years, range(24), focus_crimes)),
    columns=['Year', 'Hour', 'CrimeType']
)
df_animated = all_combos.merge(
    crime_by_year_hour[['Year', 'Hour', 'CrimeType', 'NormalizedCount']],
    on=['Year', 'Hour', 'CrimeType'], how='left'
).fillna(0)

fig_anim = px.line(
    df_animated, x='Hour', y='NormalizedCount', color='CrimeType',
    animation_frame='Year',
    title='How Have Hourly Crime Patterns Changed? (2003–2025)',
    labels={'Hour': 'Hour of Day', 'NormalizedCount': 'Share of Daily Total', 'CrimeType': 'Crime Type'},
    range_y=[0, 0.12], range_x=[-0.5, 23.5],
    color_discrete_sequence=px.colors.qualitative.Set2
)
for i, trace in enumerate(fig_anim.data):
    if i >= 2:
        trace.visible = 'legendonly'
for frame in fig_anim.frames:
    for i, trace in enumerate(frame.data):
        if i >= 2:
            trace.visible = 'legendonly'
fig_anim.update_layout(
    xaxis=dict(tickmode='linear', tick0=0, dtick=1),
    legend=dict(x=1.02, y=1, xanchor='left', yanchor='top'),
    paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e',
    font=dict(color='white'), title_font=dict(size=16)
)
fig_anim.write_html(os.path.join(VIZ_DIR, "animated_hourly_patterns.html"), include_plotlyjs='cdn')
print("  Saved animated_hourly_patterns.html")

# ────────────────────────────────────────────────────────────────────────────
# Static matplotlib: yearly crime trends
# ────────────────────────────────────────────────────────────────────────────
print("\nBonus: Matplotlib yearly crime trends (static PNG)...")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df_focus_years2 = df_all[df_all['Unified Category'].isin(focus_crimes)].copy()
df_focus_years2['Incident Datetime'] = pd.to_datetime(df_focus_years2['Incident Datetime'], errors='coerce')
df_focus_years2 = df_focus_years2.dropna(subset=['Incident Datetime'])
df_focus_years2['Year'] = df_focus_years2['Incident Datetime'].dt.year
df_focus_years2 = df_focus_years2[df_focus_years2['Year'] < 2026]

yearly = df_focus_years2.groupby(['Year', 'Unified Category']).size().unstack(fill_value=0)

fig_mpl, ax = plt.subplots(figsize=(12, 6))
fig_mpl.patch.set_facecolor('#1a1a2e')
ax.set_facecolor('#16213e')

colors = plt.cm.Set2.colors
for i, col in enumerate(focus_crimes):
    if col in yearly.columns:
        ax.plot(yearly.index, yearly[col], label=col, color=colors[i % len(colors)], linewidth=2)

ax.set_title('SF Crime Trends (2003–2025)', color='white', fontsize=16, pad=15)
ax.set_xlabel('Year', color='white')
ax.set_ylabel('Number of Incidents', color='white')
ax.tick_params(colors='white')
for spine in ax.spines.values():
    spine.set_edgecolor('#444')
ax.legend(facecolor='#16213e', labelcolor='white', framealpha=0.8, fontsize=9)
ax.axvspan(2020, 2021, alpha=0.15, color='white', label='COVID-19')
ax.grid(True, alpha=0.2, color='white')

plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, "yearly_crime_trends.png"), dpi=150, bbox_inches='tight',
            facecolor='#1a1a2e')
plt.close()
print("  Saved yearly_crime_trends.png")

print("\n✓ All visualizations exported!")
print(f"  → {VIZ_DIR}")
print(f"  → {IMG_DIR}")
