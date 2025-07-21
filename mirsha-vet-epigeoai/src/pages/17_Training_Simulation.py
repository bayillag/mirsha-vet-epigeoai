import streamlit as st
import pandas as pd
from src.core import simulation as sim

st.set_page_config(page_title="Training & Simulation", page_icon="🎓", layout="wide")

st.title("🎓 Training, Simulation & Capacity Building (Module 16)")
st.markdown("A hands-on training environment for developing outbreak investigation and response skills.")

# --- Scenario Selection ---
st.header("1. Select a Training Scenario")
SCENARIO_LIST = {"Hypothetical FMD Outbreak (2021)": "fmd_scenario_2021"}
selected_scenario_name = st.selectbox("Choose a scenario to begin:", list(SCENARIO_LIST.keys()))

if st.button("Start New Simulation", type="primary"):
    scenario_file = SCENARIO_LIST[selected_scenario_name]
    scenario_df = sim.load_scenario_data(scenario_file)
    if not scenario_df.empty:
        sim.initialize_simulation_state(scenario_df)
        st.success(f"Simulation for '{selected_scenario_name}' started. Proceed to Step 2.")
        st.experimental_rerun()

# --- Main Simulation Interface ---
if st.session_state.get('simulation_active', False):
    st.markdown("---")
    st.header("2. Outbreak Simulation")

    # --- Time Control ---
    max_days = (st.session_state.scenario_data['event_date'].max() - st.session_state.scenario_data['event_date'].min()).days
    st.session_state.current_day = st.slider(
        "Simulation Day", 0, max_days, st.session_state.get('current_day', 0)
    )
    sim.get_events_for_day(st.session_state.current_day)
    
    current_date = st.session_state.scenario_data['event_date'].min() + pd.Timedelta(days=st.session_state.current_day)
    st.subheader(f"📅 Day {st.session_state.current_day} ({current_date.strftime('%Y-%m-%d')})")
    
    # --- Information & Action Panels ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Information Received")
        st.info("This is the information available to you on the current day.")
        
        events = st.session_state.get('events_revealed', pd.DataFrame())
        if events.empty:
            st.write("No new events.")
        else:
            st.dataframe(events[['event_date', 'event_type', 'woreda_name', 'complaint', 'result_details']].style.format({"event_date": "{:%Y-%m-%d}"}))
    
    with col2:
        st.subheader("Take Action")
        st.warning("Choose the most appropriate action based on the information you have.")

        action_options = [
            "Wait / Gather more information",
            "Initiate Investigation",
            "Collect Samples",
            "Implement Quarantine",
            "Start Contact Tracing",
            "Issue Public Alert"
        ]
        selected_action = st.selectbox("Select your next action:", action_options)
        action_details = st.text_input("Action Details (e.g., 'Bena Tsemay Woreda')")

        if st.button("Log Action"):
            sim.log_trainee_action(selected_action, action_details)
            sim.score_action(selected_action, action_details, events)
            st.success(f"Action '{selected_action}' logged for Day {st.session_state.current_day}.")

    # --- Debrief and Score ---
    st.markdown("---")
    st.header("3. Simulation Debrief")

    colA, colB = st.columns([1, 2])
    with colA:
        st.subheader("Your Score")
        st.metric("Total Score", st.session_state.get('score', 0))

        st.subheader("Your Actions")
        actions_df = pd.DataFrame(st.session_state.get('trainee_actions', []))
        if not actions_df.empty:
            st.dataframe(actions_df)
    
    with colB:
        st.subheader("Instructor Feedback")
        feedback_list = st.session_state.get('feedback', [])
        if not feedback_list:
            st.info("Take actions to receive feedback.")
        else:
            for fb in feedback_list:
                if "✅" in fb:
                    st.success(fb)
                else:
                    st.warning(fb)