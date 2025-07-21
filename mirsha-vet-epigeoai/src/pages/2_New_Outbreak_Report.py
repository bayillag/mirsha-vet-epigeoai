import streamlit as st
import datetime

st.set_page_config(page_title="New Report", page_icon="📝")
st.title("📝 New Outbreak Report (Module 1)")
st.markdown("Use this form to log a new suspected outbreak.")

with st.form("outbreak_report_form"):
    st.subheader("Reporter and Location Details")
    reporter_name = st.text_input("Reporting Person Name *")
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude", format="%.6f", value=9.145000)
    with col2:
        longitude = st.number_input("Longitude", format="%.6f", value=40.489673)

    st.subheader("Outbreak Details")
    species = st.multiselect("Species Affected *", ["Cattle", "Sheep", "Goats", "Camels", "Poultry"])
    complaint = st.text_area("Description of Complaint / Clinical Signs *")
    submitted = st.form_submit_button("Submit Report")

if submitted:
    if not reporter_name or not species or not complaint:
        st.error("Please fill in all required fields marked with *.")
    else:
        st.success(f"Report for {', '.join(species)} submitted successfully by {reporter_name}.")
        st.info("The National Triage Team has been notified.")
        st.balloons()
