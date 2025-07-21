import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime
from src.core import database as db

st.set_page_config(page_title="Communications Hub", page_icon="📢", layout="wide")

st.title("📢 Public Communication & Stakeholder Engagement (Module 15)")
st.markdown("Manage and disseminate clear, timely information to farmers, traders, and the public during an animal health event.")

# --- Mock Data ---
CURRENT_OFFICER = "Public Information Officer"

# --- Main Page Layout with Tabs ---
tab1, tab2, tab3 = st.tabs(["Communication Campaign Builder", "Public Outbreak Map", "Stakeholder Meeting Planner"])

# --- Tab 1: Communication Campaign Builder ---
with tab1:
    st.header("Communication Campaign Builder")
    st.info("Select a target audience and message type to generate standardized communication materials.")

    # --- User Inputs ---
    col1, col2 = st.columns(2)
    with col1:
        target_audience = st.text_input("Target Audience", "e.g., Farmers in Bena Tsemay Woreda")
    with col2:
        disease = st.selectbox("Relevant Disease", ["FMD", "PPR", "Anthrax", "Generic Biosecurity"])

    message_type = st.selectbox("Select Communication Type", ["SMS Alert", "Radio Script", "Printable Poster"])

    st.subheader("Generated Message Template")

    # --- Generate Templates ---
    message_content = ""
    if message_type == "SMS Alert":
        message_content = f"URGENT ANIMAL HEALTH ALERT: Suspected {disease} case in your area. Please restrict all animal movement and report any sick animals immediately to your local veterinary officer. - MoA"
        st.text_area("SMS Message (160 characters max):", message_content, height=100)
    
    elif message_type == "Radio Script":
        message_content = f"""
        **-- PUBLIC SERVICE ANNOUNCEMENT --**

        **(Sound of cattle/sheep)**

        **Announcer:** Attention all livestock owners. The Ministry of Agriculture has issued a health alert regarding {disease}. 
        
        If you are in the {target_audience} area, please be vigilant. Key signs to watch for are [Sign 1], [Sign 2], and [Sign 3].
        
        To protect your animals and your livelihood, please follow these biosecurity measures:
        1. Limit visitors to your farm.
        2. Do not move animals into or out of the area until further notice.
        3. Report any sick animals to your nearest veterinary professional immediately.
        
        This message is brought to you by the Ministry of Agriculture. A healthy animal is a healthy nation.

        **(Sound of cattle/sheep fades out)**
        """
        st.text_area("Radio Script (approx. 30-45 seconds):", message_content, height=300)

    elif message_type == "Printable Poster":
        st.markdown(f"""
        ### **⚠️ ANIMAL HEALTH ALERT: {disease} ⚠️**
        **Protect Your Livestock!**
        
        An outbreak of **{disease}** has been reported in our area.
        
        **WATCH FOR THESE SIGNS:**
        - Sign A (e.g., Blisters on mouth)
        - Sign B (e.g., Lameness)
        - Sign C (e.g., Not eating)

        **WHAT TO DO:**
        1.  **STOP** all animal movement.
        2.  **ISOLATE** any sick animals from the healthy ones.
        3.  **REPORT** immediately to your vet.

        *Do not buy or sell animals until the area is declared safe.*
        
        **Brought to you by the Ministry of Agriculture.**
        """)
        message_content = "Poster content generated as shown above."

    # --- Log the Activity ---
    if st.button(f"Log '{message_type}' Activity"):
        with st.spinner("Logging communication..."):
            success, msg = db.log_communication_activity(
                outbreak_id=None, # This is a general campaign, not linked to one outbreak
                activity_type=message_type,
                audience=target_audience,
                message=message_content,
                date=datetime.date.today(),
                officer=CURRENT_OFFICER
            )
        if success:
            st.success(msg)
        else:
            st.error(msg)


# --- Tab 2: Public Outbreak Map ---
with tab2:
    st.header("Public-Facing Outbreak Information Map")
    st.warning("🔒 This map is designed for public websites. It only shows general **woreda-level** control zones for confirmed outbreaks and **does not** reveal the location of individual farms to protect privacy.")

    public_gdf = db.get_public_outbreak_map_data()

    if public_gdf.empty:
        st.success("There are currently no active, confirmed outbreaks to display to the public.")
    else:
        map_center = [9.14, 40.48]
        m_public = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB positron")

        folium.GeoJson(
            public_gdf,
            style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'weight': 1, 'fillOpacity': 0.3},
            tooltip=folium.GeoJsonTooltip(fields=['woreda_name', 'disease_name', 'confirmation_date'], aliases=['Woreda:', 'Disease:', 'Confirmed On:']),
            name="Confirmed Outbreak Control Zones"
        ).add_to(m_public)
        
        st_folium(m_public, use_container_width=True, height=600)


# --- Tab 3: Stakeholder Meeting Planner ---
with tab3:
    st.header("Stakeholder Meeting Planner & Log")
    st.info("Organize and document village meetings to ensure effective community engagement.")

    with st.form("meeting_form"):
        st.subheader("Plan a New Village Meeting")
        
        meeting_date = st.date_input("Date of Meeting")
        woreda = st.selectbox("Woreda for Meeting", WOREDA_LIST)
        topic = st.text_input("Main Topic of Discussion", "e.g., FMD Control Measures and Quarantine Rules")
        attendees = st.text_area("List of Key Attendees (e.g., Village Elders, Farmer Association Leaders)")
        
        st.subheader("Meeting Log (to be filled after the meeting)")
        key_points = st.text_area("Summary of Key Discussion Points & Community Feedback", height=200)

        submit_meeting = st.form_submit_button("Log Meeting Record")

    if submit_meeting:
        if not woreda or not topic:
            st.error("Woreda and Topic are required fields.")
        else:
            # Consolidate message for database
            full_log_message = f"""
            **Topic:** {topic}
            **Attendees:** {attendees}
            **Summary/Feedback:** {key_points}
            """
            
            with st.spinner("Logging meeting record..."):
                success, msg = db.log_communication_activity(
                    outbreak_id=None,
                    activity_type="Village Meeting",
                    audience=f"Stakeholders in {woreda}",
                    message=full_log_message,
                    date=meeting_date,
                    officer=CURRENT_OFFICER
                )
            if success:
                st.success(msg)
            else:
                st.error(msg)