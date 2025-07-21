import pandas as pd
import geopandas as gpd
import streamlit as st

RISK_DATA_PATH = "data/external/risk_factors/woreda_risk_factors.gpkg"

@st.cache_data
def load_risk_factor_data():
    """Loads the pre-generated risk factor GeoDataFrame."""
    try:
        gdf = gpd.read_file(RISK_DATA_PATH)
        return gdf
    except Exception as e:
        st.error(f"Error loading risk factor data from '{RISK_DATA_PATH}'. Did you run the generation script? Details: {e}")
        return gpd.GeoDataFrame()

def calculate_weighted_risk(risk_gdf, weights_dict):
    """
    Calculates the final risk score using a Weighted Linear Combination (WLC).
    
    Args:
        risk_gdf (GeoDataFrame): GDF containing normalized risk factor columns.
        weights_dict (dict): Dictionary of weights for each risk factor.

    Returns:
        GeoDataFrame: The input GDF with a new 'final_risk_score' column.
    """
    if risk_gdf.empty:
        return risk_gdf

    # Make a copy to avoid modifying the cached original
    gdf = risk_gdf.copy()
    
    # Initialize the score
    gdf['final_risk_score'] = 0.0

    # Apply the weights
    for factor, weight in weights_dict.items():
        if factor in gdf.columns:
            # Note: For factors like proximity, a lower value means higher risk.
            # This logic can be inverted here if needed, but for simplicity, we assume
            # all factors are positively correlated with risk (0=low risk, 1=high risk).
            gdf['final_risk_score'] += gdf[factor] * weight
        else:
            st.warning(f"Risk factor '{factor}' not found in the data and will be ignored.")

    # Normalize the final score to be between 0 and 1 for consistent coloring
    total_weight = sum(weights_dict.values())
    if total_weight > 0:
        gdf['final_risk_score'] = gdf['final_risk_score'] / total_weight

    return gdf