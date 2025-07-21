import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Analytics Dashboard", page_icon="🌍", layout="wide")

st.title("🌍 National Surveillance Dashboard (Module 4)")
st.markdown("This module provides a real-time overview of the national animal health situation.")

@st.cache_data
def load_data():
    import pandas as pd
    import geopandas as gpd
    
    data = {
        'disease': ['FMD', 'PPR', 'Anthrax'], 'woreda': ['Bena Tsemay', 'Dassenech', 'Hamer'],
        'cases': [50, 30, 5], 'latitude': [5.33, 4.88, 5.10], 'longitude': [36.75, 36.00, 36.60]
    }
    df = pd.DataFrame(data)
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")

outbreaks_gdf = load_data()

st.sidebar.header("Filters")
selected_disease = st.sidebar.selectbox("Select Disease", ["All"] + list(outbreaks_gdf['disease'].unique()))

display_gdf = outbreaks_gdf if selected_disease == "All" else outbreaks_gdf[outbreaks_gdf['disease'] == selected_disease]

st.subheader("Live Outbreak Map")
map_center = [display_gdf['latitude'].mean(), display_gdf['longitude'].mean()]
m = folium.Map(location=map_center, zoom_start=7, tiles="CartoDB positron")

for idx, row in display_gdf.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"<strong>{row['disease']}</strong><br>{row['cases']} cases<br>Woreda: {row['woreda']}",
        tooltip=row['disease']
    ).add_to(m)

st_folium(m, use_container_width=True, height=600)
st.dataframe(display_gdf)
