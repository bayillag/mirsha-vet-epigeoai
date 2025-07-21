import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from src.core import database as db
from src.core import genomics as gen

st.set_page_config(page_title="Molecular Surveillance", page_icon="🧬", layout="wide")

st.title("🧬 Molecular & Genomic Surveillance Dashboard (Module 14)")
st.markdown("Integrate pathogen genetic data with spatial epidemiology to track the evolution and spread of specific disease strains.")

# --- Load Data ---
molecular_df = db.get_molecular_surveillance_data()

if molecular_df.empty:
    st.warning("No molecular data found. This module requires confirmed outbreaks with associated sample and genomic/serotype data.")
    st.info("To use this module, a laboratory must submit results and molecular data via the LIMS gateway.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
disease_list = sorted(molecular_df['disease_name'].unique().tolist())
selected_disease = st.sidebar.selectbox("Filter by Disease", disease_list)

# Filter data based on selection
display_df = molecular_df[molecular_df['disease_name'] == selected_disease]

# --- Main Page Layout with Tabs ---
tab1, tab2 = st.tabs(["Strain Distribution Map", "Geophylogenetics"])

# --- Tab 1: Strain Distribution Map ---
with tab1:
    st.header(f"Geographic Distribution of {selected_disease} Strains/Serotypes")
    
    # Use serotype for coloring, fallback to genotype if serotype is missing
    if 'serotype' in display_df.columns and display_df['serotype'].notna().any():
        strain_column = 'serotype'
    else:
        strain_column = 'genotype'
        
    st.info(f"Map points are colored by **{strain_column}**.")

    # Create a color map for the strains
    unique_strains = display_df[strain_column].unique()
    colors = plt.cm.get_cmap('viridis', len(unique_strains))
    strain_color_map = {strain: f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}" for strain, c in zip(unique_strains, colors.colors)}

    map_center = [display_df['latitude'].mean(), display_df['longitude'].mean()]
    m_strain = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

    # Add points to the map
    for _, row in display_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            color=strain_color_map.get(row[strain_column], 'gray'),
            fill=True,
            fill_color=strain_color_map.get(row[strain_column], 'gray'),
            fill_opacity=0.8,
            popup=f"<strong>Strain: {row[strain_column]}</strong><br>Woreda: {row['woreda_name']}<br>Date: {row['investigation_date']}",
            tooltip=f"Strain: {row[strain_column]}"
        ).add_to(m_strain)
    
    # Add a custom legend
    legend_html = f'<h4>{selected_disease} {strain_column.title()} Legend</h4>'
    for strain, color in strain_color_map.items():
        legend_html += f'<i style="background:{color}; width: 20px; height: 20px; border-radius: 50%; display: inline-block; margin-right: 5px;"></i>{strain}<br>'
    
    m_strain.get_root().html.add_child(folium.Element(f'<div style="position: fixed; top: 10px; right: 10px; z-index:9999; font-size:14px; background-color:white; padding:10px; border-radius:5px; border:1px solid grey;">{legend_html}</div>'))

    st_folium(m_strain, use_container_width=True, height=600)

# --- Tab 2: Geophylogenetics ---
with tab2:
    st.header("Phylogenetic Analysis")
    st.info("This chart shows the genetic relationship between samples. Samples close together on the tree are more genetically similar.")
    
    # For this demo, we'll use a placeholder Newick tree string.
    # In a real system, this would be fetched from the `phylogenetic_tree_newick` column.
    # This example tree shows two distinct clusters.
    placeholder_newick = "((Sample_A_Woreda1:0.1, Sample_B_Woreda1:0.2):0.3, (Sample_C_Woreda5:0.4, Sample_D_Woreda6:0.5):0.6);"
    
    fig = gen.create_phylogenetic_tree_from_newick(placeholder_newick)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No phylogenetic tree data available for the selected outbreak(s). This analysis requires a Newick tree format string in the database.")