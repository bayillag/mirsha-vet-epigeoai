import streamlit as st
import datetime
from src.core import database as db

st.set_page_config(page_title="New Outbreak Report", page_icon="📝")

st.title("📝 New Outbreak Report (Module 1)")
st.markdown("Use this form to log a new suspected outbreak. All fields marked with `*` are required.")

# --- Data for Dropdowns ---
# In a real app, this would be fetched from the database
WOREDA_LIST = ["Bena Tsemay", "Dassenech", "Hamer", "Nyangatom", "Other"] 
SPECIES_LIST = ["Cattle", "Sheep", "Goats", "Camels", "Poultry", "Other"]

with st.form("outbreak_report_form"):
    st.subheader("Reporter and Location Details")
    reporter_name = st.text_input("Reporting Person Name *")
    
    woreda_name = st.selectbox("Woreda Name *", options=WOREDA_LIST)
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude (Optional)", format="%.6f", help="GPS coordinate of the outbreak location.")
    with col2:
        longitude = st.number_input("Longitude (Optional)", format="%.6f")

    st.subheader("Outbreak Details")
    report_date = st.date_input("Date of Report *", datetime.date.today())
    species = st.multiselect("Species Affected *", SPECIES_LIST)
    complaint = st.text_area("Description of Complaint / Clinical Signs *")

    submitted = st.form_submit_button("Submit Report")

if submitted:
    # --- Form Validation ---
    if not reporter_name or not woreda_name or not species or not complaint:
        st.error("Please fill in all required fields marked with *.")
    else:
        with st.spinner("Submitting report to the database..."):
            # --- Call the database function ---
            success, message = db.add_new_outbreak_report(
                reporter_name=reporter_name,
                woreda_name=woreda_name,
                lat=latitude if latitude != 0.0 else None,
                lon=longitude if longitude != 0.0 else None,
                species=species,
                complaint=complaint,
                report_date=report_date
            )
        
        if success:
            st.success(message)
            st.balloons()
        else:
            st.error(f"Failed to submit report: {message}")
