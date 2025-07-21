import streamlit as st
import folium
from streamlit_folium import st_folium
from src.core import risk_model as rm

st.set_page_config(page_title="Early Warning System", page_icon="🔮", layout="wide")

st.title("🔮 Predictive Modeling & Early Warning System (Module 9)")
st.markdown("Generate predictive risk maps using a knowledge-driven Multi-Criteria Decision Analysis (MCDA) model.")

# --- Load Base Risk Data ---
risk_gdf = rm.load_risk_factor_data()

if risk_gdf.empty:
    st.error("Risk factor data could not be loaded. Please run the data generation script.")
    st.stop()

# --- Sidebar for Model Configuration ---
st.sidebar.header("Risk Model Configuration")
st.sidebar.markdown("Define the importance of each risk factor for a specific disease.")

# Pre-defined models for demonstration
DISEASE_MODELS = {
    "Foot-and-mouth disease (FMD)": {
        "cattle_density": 0.40,
        "proximity_to_market": 0.30,
        "proximity_to_road": 0.20,
        "rainfall_anomaly": 0.05,
        "vegetation_index": 0.05
    },
    "Rift Valley Fever (RVF)": {
        "cattle_density": 0.10,
        "proximity_to_market": 0.05,
        "proximity_to_road": 0.05,
        "rainfall_anomaly": 0.50, # High importance for vector-borne
        "vegetation_index": 0.30
    },
    "Custom Model": {
        "cattle_density": 0.20,
        "proximity_to_market": 0.20,
        "proximity_to_road": 0.20,
        "rainfall_anomaly": 0.20,
        "vegetation_index": 0.20
    }
}

selected_model_name = st.sidebar.selectbox("Select a Disease Model", options=list(DISEASE_MODELS.keys()))

# --- Expert Weight Elicitation ---
st.sidebar.subheader("Adjust Factor Weights")
st.sidebar.caption("Weights should sum to 1.0 for a normalized score.")

weights = {}
if selected_model_name == "Custom Model":
    # Allow user to set weights for a custom model
    weights['cattle_density'] = st.sidebar.slider("Cattle Density", 0.0, 1.0, 0.2, 0.05)
    weights['proximity_to_market'] = st.sidebar.slider("Proximity to Market", 0.0, 1.0, 0.2, 0.05)
    weights['proximity_to_road'] = st.sidebar.slider("Proximity to Road", 0.0, 1.0, 0.2, 0.05)
    weights['rainfall_anomaly'] = st.sidebar.slider("Rainfall Anomaly", 0.0, 1.0, 0.2, 0.05)
    weights['vegetation_index'] = st.sidebar.slider("Vegetation Index (NDVI)", 0.0, 1.0, 0.2, 0.05)
else:
    # Use pre-defined weights
    weights = DISEASE_MODELS[selected_model_name]
    for factor, weight in weights.items():
        st.sidebar.text(f"{factor.replace('_', ' ').title()}: {weight:.2f}")

# --- Main Page Display ---
st.header(f"Predictive Risk Map for: {selected_model_name}")

# Calculate the final risk score
risk_map_gdf = rm.calculate_weighted_risk(risk_gdf, weights)

if not risk_map_gdf.empty:
    map_center = [risk_map_gdf.unary_union.centroid.y, risk_map_gdf.unary_union.centroid.x]
    m = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=risk_map_gdf.to_json(),
        data=risk_map_gdf,
        columns=['woreda_code', 'final_risk_score'],
        key_on='feature.properties.woreda_code',
        fill_color='PuRd',
        fill_opacity=0.8,
        line_opacity=0.2,
        legend_name=f'Predicted Relative Risk Score for {selected_model_name}'
    ).add_to(m)

    st_folium(m, use_container_width=True, height=600)
    
    st.subheader("Top 10 High-Risk Woredas")
    st.dataframe(
        risk_map_gdf[['woreda_name', 'final_risk_score']].sort_values(by='final_risk_score', ascending=False).head(10),
        use_container_width=True
    )