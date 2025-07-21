import streamlit as st
import pandas as pd
from src.core import database as db

st.set_page_config(page_title="Sample Tracking", page_icon="🔬", layout="wide")

st.title("🔬 Sample Tracking Dashboard (Module 7)")
st.markdown("Monitor the status of all submitted samples from the field to the laboratory.")

# --- Load Data ---
samples_df = db.get_all_samples()

if st.button("🔄 Refresh Sample List"):
    st.cache_data.clear() # Clear the cache for the db function
    st.experimental_rerun()

if samples_df.empty:
    st.info("No samples have been submitted to the system yet.")
else:
    # --- Display Metrics ---
    st.subheader("Sample Status Overview")
    status_counts = samples_df['status'].value_counts()
    
    cols = st.columns(len(status_counts))
    for i, (status, count) in enumerate(status_counts.items()):
        cols[i].metric(label=status, value=count)

    # --- Full Sample Log ---
    st.subheader("Complete Sample Log")
    
    # Create a styled dataframe for better readability
    def style_status(status):
        if status == 'Results Available':
            color = 'lightgreen'
        elif status == 'Collected' or status == 'In Transit':
            color = 'lightyellow'
        elif status == 'Rejected':
            color = 'lightcoral'
        else:
            color = 'white'
        return f'background-color: {color}'

    st.dataframe(
        samples_df.style.applymap(style_status, subset=['status']),
        use_container_width=True,
        height=500
    )