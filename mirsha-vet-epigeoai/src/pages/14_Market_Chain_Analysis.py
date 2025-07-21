import streamlit as st
import pandas as pd
import datetime
from src.core import database as db
from src.core import network_analysis as net_an
import streamlit.components.v1 as components

st.set_page_config(page_title="Market Chain Analysis", page_icon="🌐", layout="wide")

st.title("🌐 Livestock Movement & Market Chain Analysis (Module 13)")
st.markdown("Visualize and analyze the network of animal movements between markets, districts, and other key locations.")

# --- Sidebar Filters ---
st.sidebar.header("Network Filters")
SPECIES_LIST = ["All", "Cattle", "Sheep", "Goats", "Camels"]
selected_species = st.sidebar.selectbox("Filter by Species", SPECIES_LIST)

# Default to the last 90 days
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=90)

date_range = st.sidebar.date_input(
    "Select Date Range",
    (start_date, end_date),
    format="YYYY-MM-DD"
)

# Ensure we have a start and end date
if len(date_range) == 2:
    start, end = date_range
    
    # --- Load and Process Data ---
    movement_df = db.get_movement_network_data(start, end, selected_species)

    if movement_df.empty:
        st.warning("No movement data found for the selected filters. Try a different date range or species.")
    else:
        # Build the network graph
        G = net_an.build_network_graph(movement_df)

        st.header("Interactive Movement Network")
        st.info("Nodes represent locations (markets, woredas). Edges represent animal movements. Node size is based on the number of connections (centrality).")
        
        # --- Generate and display the interactive visualization ---
        with st.spinner("Generating network visualization..."):
            html_path = net_an.create_interactive_network_viz(G, movement_df)
        
        if html_path:
            with open(html_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            components.html(source_code, height=800)
        else:
            st.error("Failed to generate network graph.")

        # --- Display Analytics ---
        st.header("Network Analytics")
        if G:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 5 Most Connected Locations (Hubs)")
                centrality = pd.Series(nx.get_node_attributes(G, 'centrality')).sort_values(ascending=False)
                st.dataframe(centrality.head(5).rename("Centrality Score"))
            
            with col2:
                st.subheader("Top 5 Busiest Routes")
                top_routes = movement_df.sort_values(by='total_animals', ascending=False).head(5)
                st.dataframe(top_routes[['origin_name', 'destination_name', 'total_animals']])
else:
    st.error("Please select a valid date range.")