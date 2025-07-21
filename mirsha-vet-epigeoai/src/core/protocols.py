import pandas as pd
import streamlit as st

PROTOCOL_DATA_PATH = "data/raw/protocols/biosecurity_protocols.csv"
DISINFECTANT_DATA_PATH = "data/raw/protocols/disinfectant_details.csv"

@st.cache_data
def load_protocol_data():
    """Loads and prepares the biosecurity and disinfectant data from CSV files."""
    try:
        protocols_df = pd.read_csv(PROTOCOL_DATA_PATH)
        disinfectants_df = pd.read_csv(DISINFECTANT_DATA_PATH)
        return protocols_df, disinfectants_df
    except FileNotFoundError:
        st.error(f"Error: Protocol data files not found. Ensure '{PROTOCOL_DATA_PATH}' and '{DISINFECTANT_DATA_PATH}' exist.")
        return pd.DataFrame(), pd.DataFrame()

def get_protocols_for_disease(disease_name, protocols_df):
    """Filters the main protocol dataframe for a specific disease."""
    return protocols_df[protocols_df['disease_name'] == disease_name]

def get_disinfectant_details(codes_str, disinfectants_df):
    """
    Takes a string of comma-separated codes (e.g., '1,2a,3b') and returns a
    dataframe with the details for those disinfectants.
    """
    if pd.isna(codes_str):
        return pd.DataFrame() # Return empty if no codes
    
    code_list = [code.strip() for code in codes_str.split(',')]
    return disinfectants_df[disinfectants_df['code'].isin(code_list)]