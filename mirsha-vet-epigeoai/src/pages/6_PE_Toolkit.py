import streamlit as st
import pandas as pd
import datetime
from src.core import database as db

st.set_page_config(page_title="PE Toolkit", page_icon="👥", layout="wide")

st.title("👥 Participatory Epidemiology (PE) Toolkit (Module 6)")
st.markdown("Digitize and capture insights from community-based epidemiology exercises.")

# --- Mock Data & Session Setup ---
CURRENT_FACILITATOR = "Dr. Chala"
WOREDA_LIST = ["Bena Tsemay", "Dassenech", "Hamer", "Nyangatom", "Other"] # Should be fetched from DB
DISEASE_LIST = ["FMD", "PPR", "Anthrax", "LSD", "CBPP", "Other"] # Should be fetched from DB
CLINICAL_SIGNS = ["Fever", "Lameness", "Salivation", "Skin Lesions", "Sudden Death"]

# --- Sidebar for Session Details ---
st.sidebar.header("Session Details")
session_date = st.sidebar.date_input("Date of Session", datetime.date.today())
woreda_name = st.sidebar.selectbox("Woreda", options=WOREDA_LIST)
# Optional: Link this session to a specific, existing outbreak
# For now, we'll leave this as a manual entry or None
outbreak_id_input = st.sidebar.text_input("Link to Outbreak ID (Optional)")
outbreak_id = int(outbreak_id_input) if outbreak_id_input.isdigit() else None


# --- Main Page Layout with Tabs for each PE Method ---
tab1, tab2, tab3 = st.tabs(["Proportional Piling", "Matrix Scoring", "Semi-Structured Interview Guide"])

# --- Tab 1: Proportional Piling ---
with tab1:
    st.header("Proportional Piling Exercise")
    st.info("Use this tool to understand community priorities. Ask the group to score items by dividing 100 'stones'.")

    with st.form("piling_form"):
        piling_question = st.text_input(
            "Question for the Community", 
            "What are the most important animal health problems affecting your livelihood?"
        )
        
        # Use an editable dataframe for input
        piling_data = pd.DataFrame([
            {"Item": "Problem 1", "Score (stones)": 0},
            {"Item": "Problem 2", "Score (stones)": 0},
            {"Item": "Problem 3", "Score (stones)": 0},
        ])
        edited_piling_df = st.data_editor(piling_data, num_rows="dynamic", key="piling_editor")
        
        submit_piling = st.form_submit_button("Save Piling Results")

    if submit_piling:
        total_score = edited_piling_df["Score (stones)"].sum()
        if total_score != 100:
            st.error(f"The total score must be exactly 100, but it is currently {total_score}. Please adjust the scores.")
        else:
            st.subheader("Results: Community Priorities")
            st.bar_chart(edited_piling_df.set_index("Item")["Score (stones)"])
            
            # --- Save to Database ---
            with st.spinner("Saving results..."):
                # Convert dataframe to a dictionary for JSONB storage
                data_payload = {
                    "question": piling_question,
                    "results": edited_piling_df.to_dict('records')
                }
                # Get woreda code
                # In a real app, you would fetch this from a dropdown map
                woreda_code_placeholder = "ET_W_001" 
                
                success, message = db.save_pe_session_results(
                    outbreak_id=outbreak_id,
                    woreda_code=woreda_code_placeholder,
                    session_date=session_date,
                    facilitator=CURRENT_FACILITATOR,
                    method="Proportional Piling",
                    data_payload=data_payload
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

# --- Tab 2: Matrix Scoring ---
with tab2:
    st.header("Matrix Scoring Exercise")
    st.info("Use this tool to create a local case definition. Ask the group to score how strongly each sign relates to each disease.")

    # Let the facilitator define the items for the matrix
    diseases_to_score = st.multiselect("Select Diseases to Score", options=DISEASE_LIST, default=DISEASE_LIST[:3])
    signs_to_score = st.multiselect("Select Clinical Signs to Score", options=CLINICAL_SIGNS, default=CLINICAL_SIGNS[:4])
    
    if diseases_to_score and signs_to_score:
        # Create an empty dataframe with diseases as columns and signs as rows
        matrix_df = pd.DataFrame(0, index=signs_to_score, columns=diseases_to_score)
        
        st.write("Enter the scores (e.g., 0-10) in the matrix below:")
        edited_matrix_df = st.data_editor(matrix_df, key="matrix_editor")

        if st.button("Save Matrix Results"):
            st.subheader("Results: Disease-Sign Matrix")
            # Display a heatmap of the results for better visualization
            st.dataframe(edited_matrix_df.style.background_gradient(cmap='viridis', axis=None))

            # --- Save to Database ---
            with st.spinner("Saving results..."):
                data_payload = {
                    "diseases": diseases_to_score,
                    "signs": signs_to_score,
                    "matrix": edited_matrix_df.to_dict('index')
                }
                woreda_code_placeholder = "ET_W_001" 
                success, message = db.save_pe_session_results(
                    outbreak_id=outbreak_id,
                    woreda_code=woreda_code_placeholder,
                    session_date=session_date,
                    facilitator=CURRENT_FACILITATOR,
                    method="Matrix Scoring",
                    data_payload=data_payload
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

# --- Tab 3: Semi-Structured Interview Guide ---
with tab3:
    st.header("Semi-Structured Interview Guide")
    st.info("Use these open-ended questions as a guide to probe for deeper insights during community discussions. Record key findings below.")
    
    st.markdown("""
    #### Key Probing Questions (from FAO/OIE Manual)
    - **Why?** (e.g., *Why* do you think this animal became sick?)
    - **How?** (e.g., *How* does this disease usually spread in the village?)
    - **Who?** (e.g., *Who* is most affected by this problem?)
    - **What?** (e.g., *What* do you call this disease in your language?)
    - **When?** (e.g., *When* did you first notice a problem like this?)
    - **Where?** (e.g., *Where* do sick animals usually graze?)
    """)
    
    st.subheader("Interview Notes")
    interview_notes = st.text_area("Record key themes, direct quotes, and observations here.", height=300)
    
    if st.button("Save Interview Notes"):
        # --- Save to Database ---
        with st.spinner("Saving results..."):
            data_payload = {"notes": interview_notes}
            woreda_code_placeholder = "ET_W_001"
            success, message = db.save_pe_session_results(
                outbreak_id=outbreak_id,
                woreda_code=woreda_code_placeholder,
                session_date=session_date,
                facilitator=CURRENT_FACILITATOR,
                method="Semi-Structured Interview",
                data_payload=data_payload
            )
            if success:
                st.success(message)
            else:
                st.error(message)