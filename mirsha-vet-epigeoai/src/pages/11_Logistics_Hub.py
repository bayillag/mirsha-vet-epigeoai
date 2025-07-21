import streamlit as st
import pandas as pd
from src.core import database as db

st.set_page_config(page_title="Logistics Hub", page_icon="🚚", layout="wide")

st.title("🚚 Resource Management & Logistics Hub (Module 10)")
st.markdown("Monitor and manage national veterinary resources for efficient outbreak response.")

# --- Load Data from Database ---
inventory_df = db.get_inventory_data()
personnel_df = db.get_personnel_data()
# For the planner, we need outbreak data
outbreaks_for_tracing = db.get_outbreaks_for_tracing()

# --- Main Page Layout with Tabs ---
tab1, tab2, tab3 = st.tabs(["Supply Inventory", "Personnel Roster", "Response Logistics Planner"])

# --- Tab 1: Supply Inventory ---
with tab1:
    st.header("National Veterinary Supply Inventory")

    if inventory_df.empty:
        st.warning("No inventory data found in the database.")
    else:
        # --- Inventory KPIs ---
        st.subheader("Inventory Overview")
        total_items = inventory_df['quantity'].sum()
        vaccine_doses = inventory_df[inventory_df['item_type'] == 'Vaccine']['quantity'].sum()
        num_locations = inventory_df['location'].nunique()

        col1, col2, col3 = st.columns(3)
        col1.metric("Storage Locations", num_locations)
        col2.metric("Total Vaccine Doses (All types)", f"{int(vaccine_doses):,}")
        col3.metric("Total Stock Items (Units)", f"{int(total_items):,}")
        
        # --- Filtering and Display ---
        st.subheader("Browse Inventory")
        location_filter = st.multiselect(
            "Filter by Storage Location",
            options=inventory_df['location'].unique(),
            default=inventory_df['location'].unique()
        )
        type_filter = st.multiselect(
            "Filter by Item Type",
            options=inventory_df['item_type'].unique(),
            default=inventory_df['item_type'].unique()
        )

        filtered_inventory = inventory_df[
            inventory_df['location'].isin(location_filter) &
            inventory_df['item_type'].isin(type_filter)
        ]

        st.dataframe(filtered_inventory, use_container_width=True)
        st.info("Note: To update inventory quantities, please use the dedicated stock management system (feature coming soon).")

# --- Tab 2: Personnel Roster ---
with tab2:
    st.header("National Veterinary Personnel Roster")
    
    if personnel_df.empty:
        st.warning("No personnel data found in the database.")
    else:
        # --- Personnel KPIs ---
        st.subheader("Personnel Overview")
        total_personnel = len(personnel_df)
        available_personnel = len(personnel_df[personnel_df['status'] == 'Available'])
        deployed_personnel = total_personnel - available_personnel

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Personnel", total_personnel)
        col2.metric("Available for Deployment", available_personnel)
        col3.metric("Currently Deployed", deployed_personnel)

        # --- Display Roster ---
        st.subheader("Browse Roster")
        st.dataframe(personnel_df, use_container_width=True)
        st.info("Note: To update personnel status, please use the HR management system (feature coming soon).")

# --- Tab 3: Response Logistics Planner ---
with tab3:
    st.header("Response Logistics Planner")
    st.info("Select an active outbreak to calculate the estimated resources required for a ring vaccination campaign.")

    if outbreaks_for_tracing.empty:
        st.warning("No active outbreaks available for planning.")
    else:
        # --- User Inputs for Planning ---
        outbreak_options = {
            f"ID: {row.outbreak_id} - {row.disease_name} in {row.woreda_name}": row.outbreak_id 
            for _, row in outbreaks_for_tracing.iterrows()
        }
        selected_option = st.selectbox("Select an Outbreak to Plan For", options=list(outbreak_options.keys()))
        
        st.subheader("Campaign Parameters")
        col1, col2 = st.columns(2)
        with col1:
            ring_radius_km = st.number_input("Ring Vaccination Radius (km)", min_value=1, max_value=50, value=10)
            # Placeholder for population data
            susceptible_pop = st.number_input("Estimated Susceptible Population in Zone", min_value=100, max_value=500000, value=5000)
        with col2:
            doses_per_animal = st.number_input("Vaccine Doses Required per Animal", min_value=1, max_value=3, value=1)
            teams_needed = st.number_input("Number of Vaccination Teams to Deploy", min_value=1, max_value=20, value=3)

        if st.button("Calculate Required Resources", type="primary"):
            # --- Perform Calculations ---
            total_doses_needed = susceptible_pop * doses_per_animal
            
            st.subheader("Estimated Resource Requirements")
            st.metric("Total Vaccine Doses Needed", f"{total_doses_needed:,}")

            # Check against inventory (simple check for demonstration)
            vaccine_name_placeholder = selected_option.split(' - ')[1].split(' in ')[0] + " Vaccine"
            available_doses = inventory_df[
                (inventory_df['item_type'] == 'Vaccine') & 
                (inventory_df['item_name'].str.contains(vaccine_name_placeholder, case=False))
            ]['quantity'].sum()

            if available_doses >= total_doses_needed:
                st.success(f"Sufficient Stock Available. Total national stock: {int(available_doses):,} doses.")
            else:
                st.error(f"Insufficient Stock! Only {int(available_doses):,} doses available nationally. Deficit of {int(total_doses_needed - available_doses):,} doses.")
            
            st.metric("Personnel Required", f"{teams_needed} Teams")
            
            # Suggest available personnel
            available_staff = personnel_df[personnel_df['status'] == 'Available']
            st.write("**Suggested Available Personnel for Deployment:**")
            if len(available_staff) >= teams_needed * 2: # Assuming 2 people per team
                 st.dataframe(available_staff.head(teams_needed * 2))
            else:
                 st.warning(f"Not enough staff available for {teams_needed} teams.")
                 st.dataframe(available_staff)