import streamlit as st
import pandas as pd
from src.core import database as db
from src.core import economics as econ

st.set_page_config(page_title="Economic Impact Hub", page_icon="💰", layout="wide")

st.title("💰 Economic Impact & Cost-Benefit Analysis (Module 11)")
st.markdown("Quantify the economic impact of animal diseases and evaluate the return on investment of control measures.")

# --- Main Page Layout with Tabs ---
tab1, tab2 = st.tabs(["Outbreak Cost Calculator", "Cost-Benefit Scenario Planner"])

# --- Tab 1: Outbreak Cost Calculator ---
with tab1:
    st.header("Retrospective Outbreak Cost Calculator")
    st.info("Select a completed outbreak to estimate its direct economic cost based on reported data.")

    outbreaks_to_analyze = db.get_outbreaks_for_tracing() # Re-using this function for a list of valid outbreaks

    if outbreaks_to_analyze.empty:
        st.warning("No completed outbreaks with case data are available for analysis.")
    else:
        outbreak_options = {
            f"ID: {row.outbreak_id} - {row.disease_name} in {row.woreda_name}": row.outbreak_id 
            for _, row in outbreaks_to_analyze.iterrows()
        }
        selected_option = st.selectbox("Select an Outbreak to Analyze", options=list(outbreak_options.keys()))

        if st.button("Calculate Cost", key="cost_calc_btn"):
            outbreak_id = outbreak_options[selected_option]
            
            # Fetch the case data for this specific outbreak
            cases_df = db.get_cases_for_outbreak(outbreak_id)

            if cases_df.empty:
                st.error("No case line-list data found for this outbreak. Cannot calculate cost.")
            else:
                with st.spinner("Calculating economic impact..."):
                    costs = econ.calculate_direct_outbreak_cost(cases_df)
                
                st.subheader(f"Estimated Direct Economic Cost for Outbreak #{outbreak_id}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Estimated Cost (ETB)", f"{costs['total_cost']:,.0f}")
                col2.metric("Mortality Losses (ETB)", f"{costs['mortality_cost']:,.0f}")
                col3.metric("Morbidity Losses (ETB)", f"{costs['morbidity_cost']:,.0f}")

                st.write("---")
                st.write("Calculation based on the following reported data:")
                st.dataframe(cases_df[['species', 'total_susceptible', 'cases', 'deaths']])
                st.caption("Note: This is a simplified model and does not include indirect costs like trade disruption or control program expenses.")

# --- Tab 2: Cost-Benefit Scenario Planner ---
with tab2:
    st.header("Prospective Cost-Benefit Scenario Planner")
    st.info("Model the potential financial impact of a new control program to support policy decisions.")
    
    st.subheader("1. Define the 'No Action' Scenario")
    st.markdown("Estimate the expected number of cases and deaths over one year if no new intervention is made.")
    
    col1, col2 = st.columns(2)
    with col1:
        proj_cases = st.number_input("Projected Annual Cases", min_value=0, value=10000, step=100)
    with col2:
        proj_deaths = st.number_input("Projected Annual Deaths", min_value=0, value=500, step=50)

    st.markdown("**Projected Species Distribution (%):**")
    colA, colB, colC, colD = st.columns(4)
    species_dist = {
        "Cattle": colA.number_input("Cattle (%)", 0, 100, 60),
        "Sheep": colB.number_input("Sheep (%)", 0, 100, 20),
        "Goats": colC.number_input("Goats (%)", 0, 100, 15),
        "Camels": colD.number_input("Camels (%)", 0, 100, 5)
    }
    
    st.subheader("2. Define the 'Intervention' Scenario")
    intervention_cost = st.number_input("Total Estimated Cost of Intervention (ETB)", min_value=0, value=5000000, step=100000)
    intervention_effectiveness = st.slider("Intervention Effectiveness (% of cases prevented)", 0, 100, 80)
    
    if st.button("Run Cost-Benefit Analysis", type="primary"):
        if sum(species_dist.values()) != 100:
            st.error("Species distribution percentages must sum to 100%.")
        else:
            with st.spinner("Running scenario analysis..."):
                # Convert percentages to proportions
                species_proportions = {k: v / 100.0 for k, v in species_dist.items()}
                
                scenario = econ.run_cost_benefit_scenario(
                    projected_cases=proj_cases,
                    projected_deaths=proj_deaths,
                    projected_species_distribution=species_proportions,
                    intervention_cost=intervention_cost,
                    intervention_effectiveness_percent=intervention_effectiveness
                )
            
            st.subheader("Scenario Analysis Results")
            c1, c2, c3 = st.columns(3)
            c1.metric("Cost of 'No Action' (ETB)", f"{scenario['cost_no_action']:,.0f}")
            c2.metric("Total Cost with Intervention (ETB)", f"{scenario['cost_with_intervention']:,.0f}")
            c3.metric("Return on Investment (ROI)", f"{scenario['roi_percent']:.1f}%")

            st.success(f"**Net Benefit of Intervention (ETB): {scenario['net_benefit']:,.0f}**")
            st.markdown(f"The analysis projects that investing **{intervention_cost:,.0f} ETB** in this control program would avert **{scenario['benefits_averted_cost']:,.0f} ETB** in direct disease losses, resulting in a positive net benefit.")