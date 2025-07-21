import streamlit as st
import numpy as np
from pysal.lib import weights
from esda.moran import Moran_Local

@st.cache_data
def calculate_lisa(gdf, attribute_column):
    """
    Calculates Local Moran's I (LISA) for a given GeoDataFrame and attribute.
    Returns the GeoDataFrame with LISA results appended.
    """
    if gdf.empty or attribute_column not in gdf.columns or gdf[attribute_column].nunique() < 2:
        gdf['lisa_q'] = 0
        gdf['lisa_p'] = 1.0
        gdf['cluster_type'] = "Not Significant"
        return gdf

    try:
        # Create spatial weights matrix from polygon contiguity
        w = weights.Queen.from_dataframe(gdf)
        w.transform = 'r'  # Row-standardize

        # Calculate Local Moran's I
        lisa = Moran_Local(gdf[attribute_column], w, permutations=999)

        # Append results
        gdf['lisa_q'] = lisa.q
        gdf['lisa_p'] = lisa.p_sim

        # Define cluster types for mapping
        cluster_labels = {
            1: 'High-High (Hotspot)', 2: 'Low-High (Doughnut)',
            3: 'Low-Low (Coldspot)', 4: 'High-Low (Diamond)'
        }
        gdf['cluster_type'] = gdf['lisa_q'].map(cluster_labels)
        gdf.loc[gdf['lisa_p'] > 0.05, 'cluster_type'] = 'Not Significant'

        return gdf
    except Exception as e:
        st.warning(f"Could not perform LISA analysis. Error: {e}")
        gdf['cluster_type'] = "Analysis Error"
        return gdf