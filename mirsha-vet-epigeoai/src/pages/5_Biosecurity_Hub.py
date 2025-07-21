import streamlit as st
import pandas as pd
from src.core import protocols as proto

st.set_page_config(page_title="Biosecurity Hub", page_icon="🛡️", layout="wide")

st.title("🛡️ Biosecurity & Disinfection Protocols Hub (Module 5)")
st.markdown("An in-field knowledge base for implementing correct biosecurity measures during an outbreak.")

# --- Load Data ---
protocols_df, disinfectants_df = proto.load_protocol_data()

if protocols_df.empty or disinfectants_df.empty:
    st.stop()

# --- User Input ---
st.sidebar.header("Select Disease")
disease_list = sorted(protocols_df['disease_name'].unique().tolist())
selected_disease = st.sidebar.selectbox("Select a suspected or confirmed disease:", disease_list)

# --- Main Display ---
st.header(f"Protocols for: {selected_disease}")

# Get the specific protocols for the selected disease
disease_protocols = proto.get_protocols_for_disease(selected_disease, protocols_df)

if disease_protocols.empty:
    st.warning("No specific protocols found for the selected disease.")
else:
    # --- Tab 1: Recommended Actions ---
    tab1, tab2 = st.tabs(["Recommended Actions", "Decontamination Checklist"])

    with tab1:
        st.subheader("Recommended Actions by Item")
        st.markdown("These procedures are based on the FAO/OIE Field Manual.")

        for index, row in disease_protocols.iterrows():
            with st.expander(f"**Item to be Disinfected: {row['item']}**"):
                st.write(f"**Recommended Procedure:** {row['procedure']}")
                
                # Get and display details for the recommended disinfectants
                disinfectant_details = proto.get_disinfectant_details(row['disinfectant_codes'], disinfectants_df)
                
                if not disinfectant_details.empty:
                    st.write("**Applicable Disinfectants:**")
                    st.dataframe(
                        disinfectant_details[['name', 'concentration', 'contact_time', 'details']],
                        hide_index=True
                    )
                else:
                    st.info("Procedure does not specify chemical disinfectants (e.g., physical removal).")
    
    # --- Tab 2: Decontamination Checklist ---
    with tab2:
        st.subheader("On-Site Decontamination & Disinfection Checklist")
        st.markdown("Use this checklist to ensure all biosecurity steps are completed on an infected premises.")

        st.markdown("#### Decontamination Phase (Physical Cleaning)")
        st.checkbox("Transfer all animals to a secure, clean area.", key="step1")
        st.checkbox("Prepare soaps and/or detergents; wear appropriate PPE.", key="step2")
        st.checkbox("Cover all electrical outlets with plastic and masking tape.", key="step3")
        st.checkbox("Remove all organic material (manure, bedding, debris) from walls and floors.", key="step4")
        st.checkbox("Discard disposable items (cartons, rotting wood).", key="step5")
        st.checkbox("Ensure water can drain away from the working area.", key="step6")
        
        st.markdown("#### Disinfection Phase (Chemical Application)")
        st.checkbox("Ensure disinfectants are freshly mixed at the correct concentration (see 'Recommended Actions' tab).", key="step7")
        st.checkbox("Apply disinfectant from the TOP of the area (ceiling) and work downwards to the floor.", key="step8")
        st.checkbox("Ensure disinfectant makes physical contact for the required time.", key="step9")
        st.checkbox("Discard unused disinfectant safely and according to local regulations.", key="step10")
        
        if st.button("Generate Checklist Record"):
            st.success("A record of this checklist can be printed or saved (feature coming soon).")