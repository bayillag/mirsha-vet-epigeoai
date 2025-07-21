import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from src.core import database as db
from src.core import analysis as an

st.set_page_config(page_title="Analytics Dashboard", page_icon="🌍", layout="wide")

st.title("🌍 National Surveillance Dashboard (Module 4)")
st.markdown("Analyze national animal health data through interactive maps, charts, and spatial statistics.")

# --- Load Data ---
# This function is cached, so it only runs once per session unless the cache is cleared.
woredas_gdf, outbreaks_gdf = db.get_dashboard_data()

if woredas_gdf.empty:
    st.error("Could not load dashboard data from the database. Please check the connection and ensure data exists.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")
disease_list = ["All"] + sorted(woredas_gdf['disease_name'].dropna().unique().tolist())
selected_disease = st.sidebar.selectbox("Filter by Disease", disease_list)

# Filter the data based on selection
if selected_disease == "All":
    # Aggregate data across all diseases for each woreda
    woreda_summary = woredas_gdf.groupby('woreda_code').agg({
        'woreda_name': 'first', 'geom': 'first', 'total_cases': 'sum',
        'total_deaths': 'sum', 'total_susceptible': 'sum'
    }).reset_index()
    woreda_summary_gdf = gpd.GeoDataFrame(woreda_summary, geometry='geom', crs="EPSG:4326")
    point_display_gdf = outbreaks_gdf
else:
    woreda_summary_gdf = woredas_gdf[woredas_gdf['disease_name'] == selected_disease]
    point_display_gdf = outbreaks_gdf[outbreaks_gdf['disease_name'] == selected_disease]

# --- Main Page Layout with Tabs ---
tab1, tab2, tab3 = st.tabs(["Choropleth Map (Rates)", "Hotspot Analysis (LISA)", "Temporal Analysis (Epi Curve)"])

# --- Tab 1: Choropleth Map ---
with tab1:
    st.header("Choropleth Map of Disease Metrics")
    metric_to_map = st.selectbox(
        "Select Metric to Display:",
        options=["Total Cases", "Case Fatality Rate (%)", "Attack Rate (%)"],
        key="choropleth_metric"
    )

    metric_column_map = {
        "Total Cases": "total_cases",
        "Case Fatality Rate (%)": "cfr_percent",
        "Attack Rate (%)": "attack_rate_percent"
    }
    metric_column = metric_column_map[metric_to_map]

    map_center = [woredas_gdf.unary_union.centroid.y, woredas_gdf.unary_union.centroid.x]
    m_choro = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=woreda_summary_gdf.to_json(),
        data=woreda_summary_gdf,
        columns=['woreda_code', metric_column],
        key_on='feature.properties.woreda_code',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f"{metric_to_map} for {selected_disease}"
    ).add_to(m_choro)

    st_folium(m_choro, use_container_width=True, height=600)

# --- Tab 2: Hotspot Analysis (LISA) ---
with tab2:
    st.header("Hotspot & Coldspot Analysis (Local Moran's I)")
    st.info("This analysis identifies woredas with statistically significant spatial clustering of high or low case counts.")
    
    # Run LISA analysis
    lisa_gdf = an.calculate_lisa(woreda_summary_gdf, 'total_cases')

    m_lisa = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

    # Define colors for cluster types
    cluster_colors = {
        'High-High (Hotspot)': 'red',
        'Low-Low (Coldspot)': 'blue',
        'High-Low (Diamond)': 'orange',
        'Low-High (Doughnut)': 'yellow',
        'Not Significant': 'lightgray'
    }

    # Add styled GeoJSON layer for LISA results
    folium.GeoJson(
        lisa_gdf,
        style_function=lambda feature: {
            'fillColor': cluster_colors.get(feature['properties']['cluster_type'], 'gray'),
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7 if feature['properties']['cluster_type'] != 'Not Significant' else 0.2
        },
        tooltip=folium.GeoJsonTooltip(fields=['woreda_name', 'total_cases', 'cluster_type']),
        name='LISA Clusters'
    ).add_to(m_lisa)
    
    st_folium(m_lisa, use_container_width=True, height=600)

# --- Tab 3: Temporal Analysis ---
with tab3:
    st.header("Epidemic Curve")
    if not point_display_gdf.empty and 'investigation_date' in point_display_gdf.columns:
        point_display_gdf['investigation_date'] = pd.to_datetime(point_display_gdf['investigation_date'])
        
        # Resample data by week to create the epi curve
        epi_curve_data = point_display_gdf.set_index('investigation_date').resample('W')['outbreak_id'].count()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        epi_curve_data.plot(kind='bar', ax=ax, color='teal')
        ax.set_title(f"Epidemic Curve: Weekly New Outbreak Reports for {selected_disease}")
        ax.set_xlabel("Week")
        ax.set_ylabel("Number of New Outbreaks Reported")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.warning("No date information available to generate an epidemic curve for the selected filter.")