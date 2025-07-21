import pandas as pd
import streamlit as st

SCENARIO_PATH = "data/scenarios/fmd_scenario_2021.csv"

@st.cache_data
def load_scenario_data(scenario_name):
    """Loads a pre-packaged historical outbreak scenario from a CSV file."""
    try:
        df = pd.read_csv(f"data/scenarios/{scenario_name}.csv")
        df['event_date'] = pd.to_datetime(df['event_date'])
        return df
    except FileNotFoundError:
        st.error(f"Scenario file not found: {scenario_name}.csv")
        return pd.DataFrame()

def initialize_simulation_state(scenario_df):
    """Sets up the initial state for a new simulation session."""
    st.session_state['simulation_active'] = True
    st.session_state['scenario_data'] = scenario_df
    st.session_state['current_day'] = 0
    st.session_state['events_revealed'] = pd.DataFrame()
    st.session_state['trainee_actions'] = []
    st.session_state['score'] = 0
    st.session_state['feedback'] = []

def get_events_for_day(day_index):
    """Reveals events from the scenario that occur up to a certain day."""
    if 'scenario_data' not in st.session_state:
        return
        
    start_date = st.session_state['scenario_data']['event_date'].min()
    current_date = start_date + pd.Timedelta(days=day_index)
    
    # Get all events that have occurred up to the current date
    revealed_df = st.session_state['scenario_data'][
        st.session_state['scenario_data']['event_date'] <= current_date
    ]
    st.session_state['events_revealed'] = revealed_df

def log_trainee_action(action, details=""):
    """Logs an action taken by the trainee for scoring and review."""
    timestamp = st.session_state['scenario_data']['event_date'].min() + pd.Timedelta(days=st.session_state['current_day'])
    st.session_state['trainee_actions'].append({
        "day": st.session_state['current_day'],
        "date": timestamp.strftime('%Y-%m-%d'),
        "action": action,
        "details": details
    })

def score_action(action, details, events):
    """
    A simple scoring logic. Correct actions on the right day get points.
    This can be made much more sophisticated.
    """
    current_date_str = (st.session_state['scenario_data']['event_date'].min() + pd.Timedelta(days=st.session_state['current_day'])).strftime('%Y-%m-%d')
    
    # Example scoring rule
    if action == "Initiate Investigation" and any(events['event_type'] == 'initial_report'):
        st.session_state['score'] += 10
        st.session_state['feedback'].append(f"✅ Day {st.session_state['current_day']}: Good! You correctly initiated an investigation after the first report.")
        return True
        
    if action == "Implement Quarantine" and "Bena Tsemay" in details:
        lab_result_day = events[events['event_type'] == 'lab_result']['event_date'].min()
        if pd.notna(lab_result_day) and st.session_state['current_day'] >= (lab_result_day - events['event_date'].min()).days:
            st.session_state['score'] += 20
            st.session_state['feedback'].append(f"✅ Day {st.session_state['current_day']}: Excellent! You implemented quarantine quickly after lab confirmation.")
            return True

    st.session_state['feedback'].append(f"⚠️ Day {st.session_state['current_day']}: Action '{action}' was logged, but no points awarded for this timing.")
    return False