import streamlit as st

st.set_page_config(
    page_title="Homepage",
    page_icon="🏠",
)

st.title("Mirsha VetEpiGeoAI Platform Homepage 🏠")
st.markdown("---")
st.header("An Integrated System for Animal Health Management in Ethiopia")
st.write(
    """
    This platform provides a suite of tools to support the entire lifecycle of animal disease 
    outbreak investigation—from initial report to final analysis—while ensuring full compliance 
    with Ethiopian National Livestock Data Standards.
    """
)
st.subheader("Platform Divisions")
st.markdown(
    """
    - **I: Field Operations & Outbreak Response**: Tools for frontline personnel.
    - **II: Analytics & Laboratory Integration**: The analytical engine for data intelligence.
    - **III: Strategic Planning & Policy Support**: High-level tools for program design and economic justification.
    - **IV: Communication & Capacity Building**: Focuses on stakeholder engagement and workforce development.
    """
)
st.warning("Note: This is a multipage app. Use the sidebar to navigate to different modules.")
