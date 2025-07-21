import streamlit as st
import pandas as pd
import datetime
from src.core import database as db

st.set_page_config(page_title="Field Investigation Hub", page_icon="🔍", layout="wide")

st.title("🔍 Field Investigation Hub (Module 2)")
st.markdown("Select an assigned outbreak to begin your investigation and file the full report.")

# --- Mock Data and Placeholders ---
# In a real app, this would come from a user authentication system
CURRENT_INVESTIGATOR = "Dr. Alemayehu" 
CLINICAL_SIGNS_LIST = [ # From Ethiopian Data Standard / FAO Manual
    "Fever", "Bleeding/haemorrhage", "Drooling saliva", "Anorexia",
    "Jaundice", "Abortion", "Blisters on mouth/feet/udder", "Neurological signs", "Diarrhoea"
]
LABORATORIES = ["Animal Health Institute (AHI)", "Jinka Regional Lab", "Other"]
SAMPLE_TYPES = ["Blood (Serum)", "Blood (Whole)", "Tissue", "Swab", "Other"]
SPECIES_LIST = ["Cattle", "Sheep", "Goats", "Camels", "Poultry"]

# --- Main Logic ---
st.header(f"Welcome, {CURRENT_INVESTIGATOR}")

# Fetch outbreaks assigned to the current user
assigned_outbreaks = db.get_assigned_outbreaks(CURRENT_INVESTIGATOR)

if assigned_outbreaks.empty:
    st.info("You have no pending investigations assigned to you. Well done!")
else:
    outbreak_options = {f"ID: {row.outbreak_id} - {row.woreda_name} ({row.report_date})": row.outbreak_id for index, row in assigned_outbreaks.iterrows()}
    selected_option = st.selectbox("Select an Outbreak to Investigate", options=["--Select--"] + list(outbreak_options.keys()))

    if selected_option != "--Select--":
        outbreak_id = outbreak_options[selected_option]
        
        # Fetch and display initial details for context
        details = db.get_outbreak_details(outbreak_id)
        if details:
            with st.expander("View Initial Report Details", expanded=True):
                st.markdown(f"**Woreda:** {details['woreda']} | **Reporter:** {details['reporter']}")
                st.markdown(f"**Species:** {', '.join(details['species'])}")
                st.markdown(f"**Initial Complaint:**")
                st.info(details['complaint'])

        # --- The Main Investigation Form ---
        with st.form("investigation_form"):
            st.markdown("---")
            st.header("Full Investigation Report")

            # Section 2: Index Case
            st.subheader("Section 2: Index Case & Onset")
            investigation_date = st.date_input("Date of this Investigation *", datetime.date.today())
            first_signs_date = st.date_input("Date First Signs were Noted *", value=details['date'])

            # Section 3: List of Cases (Line Listing)
            st.subheader("Section 3: List of Cases (Line Listing)")
            st.markdown("Add a row for each group of animals (e.g., by species).")
            case_data = pd.DataFrame(
                [
                    {"Species": SPECIES_LIST[0], "Susceptible": 0, "Cases": 0, "Deaths": 0, "Date": datetime.date.today()}
                ]
            )
            line_list_df = st.data_editor(
                case_data, 
                num_rows="dynamic",
                column_config={
                    "Species": st.column_config.SelectboxColumn("Species", options=SPECIES_LIST, required=True),
                    "Susceptible": st.column_config.NumberColumn("Total Susceptible", min_value=0, step=1, required=True),
                    "Cases": st.column_config.NumberColumn("Number of Cases", min_value=0, step=1, required=True),
                    "Deaths": st.column_config.NumberColumn("Number of Deaths", min_value=0, step=1, required=True),
                    "Date": st.column_config.DateColumn("Date of Onset", required=True),
                },
                key="line_list"
            )

            # Section 4: Clinical & Sample Collection
            st.subheader("Section 4: Clinical Investigation & Sampling")
            selected_signs = st.multiselect("Observed Clinical Signs", options=CLINICAL_SIGNS_LIST)
            
            st.markdown("**4.3 Sample Collection**")
            sample_data = pd.DataFrame(columns=["Field ID", "Sample Type", "Laboratory", "Submission Date"])
            samples_df = st.data_editor(
                sample_data, 
                num_rows="dynamic",
                column_config={
                    "Field ID": st.column_config.TextColumn("Field Sample ID", required=True),
                    "Sample Type": st.column_config.SelectboxColumn("Sample Type", options=SAMPLE_TYPES, required=True),
                    "Laboratory": st.column_config.SelectboxColumn("Destination Lab", options=LABORATORIES, required=True),
                    "Submission Date": st.column_config.DateColumn("Submission Date", required=True)
                },
                key="samples"
            )
            
            # Section 5 & 6: Environment & Risk Factors
            st.subheader("Section 5 & 6: Environment & Aetiology")
            husbandry_type = st.radio("Animal Husbandry in Area", ["Farm/Stable", "Grazing in defined area", "Free-grazing", "Other"])
            shared_water = st.text_area("Details of any shared water sources")
            nearby_markets = st.text_area("Livestock markets or slaughterhouses within 10km radius")

            # Submit button for the entire form
            submitted = st.form_submit_button("Submit Final Investigation Report")

        if submitted:
            # Consolidate form data into a dictionary for JSONB storage
            form_data_payload = {
                "first_signs_date": first_signs_date.isoformat(),
                "clinical_signs": selected_signs,
                "husbandry_type": husbandry_type,
                "shared_water_sources": shared_water,
                "nearby_markets": nearby_markets
            }
            
            with st.spinner("Submitting full report..."):
                success, message = db.submit_full_investigation(
                    outbreak_id=outbreak_id,
                    investigation_date=investigation_date,
                    form_data=form_data_payload,
                    line_list_df=line_list_df,
                    samples_df=samples_df
                )

            if success:
                st.success(message)
            else:
                st.error(message)