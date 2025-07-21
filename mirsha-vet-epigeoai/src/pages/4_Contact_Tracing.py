import streamlit as st
import pandas as pd
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium
import datetime
from src.core import database as db

st.set_page_config(page_title="Contact Tracing", page_icon="🔗", layout="wide")

st.title("🔗 Contact Tracing Module (Module 3)")
st.markdown("Visualize and manage trace-back and trace-forward investigations for confirmed outbreaks.")

# --- Constants and Placeholders ---
LOCATION_TYPES = ["Farm", "Market", "Water Point", "Slaughterhouse", "Trader's Home"]
CONTACT_TYPES = ["Animal Movement", "Vehicle", "Personnel", "Shared Grazing", "Other"]
DISEASE_INCUBATION = { # In days, for the tracing window calculator
    "FMD": 14,
    "PPR": 21,
    "Anthrax": 7,
    "Default": 21
}

# --- Main Logic ---
outbreaks_to_trace = db.get_outbreaks_for_tracing()

if outbreaks_to_trace.empty:
    st.info("No confirmed or in-progress outbreaks are available for tracing.")
else:
    # Create a user-friendly list for the selectbox
    outbreak_options = {
        f"ID: {row.outbreak_id} - {row.disease_name} in {row.woreda_name} ({row.investigation_date})": row.outbreak_id 
        for index, row in outbreaks_to_trace.iterrows()
    }
    selected_option = st.selectbox("Select an Outbreak to Trace", options=["--Select--"] + list(outbreak_options.keys()))

    if selected_option != "--Select--":
        outbreak_id = outbreak_options[selected_option]
        
        # Fetch details for the selected outbreak
        index_case_details = db.get_outbreak_details(outbreak_id)
        if not index_case_details:
            st.error("Could not load details for the selected outbreak.")
            st.stop()

        # --- Tracing Window Calculator ---
        disease_name = outbreaks_to_trace.loc[outbreaks_to_trace['outbreak_id'] == outbreak_id, 'disease_name'].iloc[0]
        max_incubation = DISEASE_INCUBATION.get(disease_name, DISEASE_INCUBATION["Default"])
        onset_date = index_case_details.get('investigation_date', datetime.date.today()) # Fallback
        
        if onset_date:
            window_start = onset_date - datetime.timedelta(days=max_incubation)
            st.info(f"**Tracing Window for Source (Trace-back):** {window_start.strftime('%Y-%m-%d')} to {onset_date.strftime('%Y-%m-%d')}")
        
        # --- Display Map and Form side-by-side ---
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Contact Tracing Network Map")
            
            # Fetch existing links
            tracing_links_df = db.get_tracing_links(outbreak_id)

            # Create base map
            map_center = [index_case_details['latitude'], index_case_details['longitude']] if index_case_details.get('latitude') else [9.14, 40.48]
            m = folium.Map(location=map_center, zoom_start=9, tiles="CartoDB positron")

            # Add index case marker
            folium.Marker(
                location=map_center,
                popup=f"<strong>Index Outbreak #{outbreak_id}</strong><br>{index_case_details['woreda']}",
                tooltip="Index Outbreak",
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)

            # Add existing links to the map
            for _, link in tracing_links_df.iterrows():
                link_color = 'blue' if link['direction'] == 'Trace-back' else 'orange'
                
                # Marker for the linked location
                folium.Marker(
                    location=[link['latitude'], link['longitude']],
                    popup=f"<strong>{link['linked_location_name']}</strong><br>Type: {link['contact_type']}<br>Date: {link['contact_date']}",
                    tooltip=link['linked_location_name'],
                    icon=folium.Icon(color=link_color, icon='info-sign')
                ).add_to(m)
                
                # Animated path from index case to link
                path = AntPath(
                    locations=[map_center, [link['latitude'], link['longitude']]],
                    color=link_color,
                    dash_array=[10, 20],
                    weight=3
                )
                path.add_to(m)

            st_folium(m, use_container_width=True, height=600)

        with col2:
            st.subheader("Add New Contact Link")
            with st.form("add_link_form"):
                direction = st.radio("Direction", ["Trace-back (Source)", "Trace-forward (Spread)"], key="direction")
                location_name = st.text_input("Linked Location Name (e.g., 'Gode Market') *")
                location_type = st.selectbox("Location Type", options=LOCATION_TYPES, key="loc_type")
                contact_type = st.selectbox("Contact Type", options=CONTACT_TYPES, key="contact_type")
                contact_date = st.date_input("Date of Contact *")
                
                lat = st.number_input("Latitude", format="%.6f")
                lon = st.number_input("Longitude", format="%.6f")
                
                notes = st.text_area("Notes / Remarks")

                submit_link = st.form_submit_button("Add Link")
            
            if submit_link:
                if not location_name or not contact_date:
                    st.error("Location Name and Contact Date are required.")
                else:
                    direction_value = 'Trace-back' if direction == 'Trace-back (Source)' else 'Trace-forward'
                    success, message = db.add_tracing_link(
                        source_outbreak_id=outbreak_id,
                        name=location_name,
                        loc_type=location_type,
                        lat=lat if lat != 0.0 else None,
                        lon=lon if lon != 0.0 else None,
                        date=contact_date,
                        contact_type=contact_type,
                        direction=direction_value,
                        notes=notes
                    )
                    if success:
                        st.success(message)
                        st.experimental_rerun() # Refresh the page to show the new link on the map
                    else:
                        st.error(message)

            # Display existing links in a table
            if not tracing_links_df.empty:
                st.subheader("Existing Links")
                st.dataframe(tracing_links_df[['direction', 'linked_location_name', 'contact_type', 'contact_date']])
