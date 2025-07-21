import streamlit as st
import pandas as pd
import datetime
from src.core import database as db

st.set_page_config(page_title="Lab Results Entry", page_icon="🧪")

# --- Password Protection (Simple Simulation) ---
# In a real app, this would be a proper login system (e.g., OAuth)
def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Show the password input
    password = st.text_input("Enter Laboratory Access Password", type="password")
    if password == st.secrets.get("LAB_PASSWORD", "veteplab123"): # Fallback for local dev
        st.session_state["password_correct"] = True
        st.experimental_rerun()
    elif password:
        st.error("Password incorrect.")
    return False

# --- Main App ---
st.title("🧪 Laboratory Results Entry (Module 7)")

if not check_password():
    st.stop() # Do not render the rest of the app if password is not correct

st.success("Authenticated as Laboratory Personnel.")
st.markdown("Use this secure portal to submit diagnostic results for a given Field Sample ID.")

# --- Results Entry Form ---
field_id = st.text_input("Enter the Field Sample ID to search for:")

if field_id:
    sample_details = db.get_sample_by_field_id(field_id)
    
    if sample_details:
        st.info(f"**Sample Found:** ID #{sample_details['id']} | **Current Status:** {sample_details['status']}")
        
        with st.form("results_form"):
            st.subheader(f"Submit Results for: {sample_details['field_id']}")
            result = st.selectbox("Test Result *", ["Positive", "Negative", "Inconclusive", "Rejected"])
            result_details = st.text_area("Result Details (e.g., 'FMD-Type O', 'Brucella abortus', 'Sample hemolyzed')")
            result_date = st.date_input("Date of Result *", datetime.date.today())
            
            submit_button = st.form_submit_button("Submit Final Result")

        if submit_button:
            with st.spinner("Submitting result and updating outbreak status..."):
                success, message = db.submit_lab_result(
                    sample_id=sample_details['id'],
                    outbreak_id=sample_details['outbreak_id'],
                    result=result,
                    result_details=result_details,
                    result_date=result_date
                )
            
            if success:
                st.success(message)
            else:
                st.error(message)

    else:
        st.error("No sample found with that Field Sample ID. Please check the ID and try again.")