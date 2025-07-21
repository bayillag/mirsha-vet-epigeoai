import pandas as pd
import streamlit as st
import numpy as np

# --- Economic Model Parameters ---
# In a real-world system, these would be in a configuration file or database table
# that can be updated annually by economists.
ANIMAL_MARKET_VALUES = {
    "Cattle": 30000, # ETB
    "Sheep": 4000,
    "Goats": 3500,
    "Camels": 60000,
    "Poultry": 250,
    "Default": 10000
}

# Estimated daily production loss per sick animal (e.g., milk, weight gain)
DAILY_MORBIDITY_LOSS = {
    "Cattle": 150, # ETB/day
    "Sheep": 20,
    "Goats": 18,
    "Camels": 200,
    "Poultry": 5,
    "Default": 50
}

AVG_DISEASE_DURATION_DAYS = 21 # Assumed average duration of production loss

# --- Main Calculation Functions ---

@st.cache_data
def calculate_direct_outbreak_cost(outbreak_cases_df):
    """
    Calculates the estimated direct economic cost of a single or multiple outbreaks.
    
    Args:
        outbreak_cases_df (DataFrame): A DataFrame of case data, typically from
                                       the 'outbreak_cases' table.
    
    Returns:
        dict: A dictionary containing the calculated costs.
    """
    if outbreak_cases_df.empty:
        return {"total_cost": 0, "mortality_cost": 0, "morbidity_cost": 0}

    # Calculate mortality cost
    outbreak_cases_df['animal_value'] = outbreak_cases_df['species'].map(ANIMAL_MARKET_VALUES).fillna(ANIMAL_MARKET_VALUES["Default"])
    mortality_cost = (outbreak_cases_df['deaths'] * outbreak_cases_df['animal_value']).sum()
    
    # Calculate morbidity cost
    outbreak_cases_df['daily_loss_value'] = outbreak_cases_df['species'].map(DAILY_MORBIDITY_LOSS).fillna(DAILY_MORBIDITY_LOSS["Default"])
    morbidity_cost = (outbreak_cases_df['cases'] * outbreak_cases_df['daily_loss_value'] * AVG_DISEASE_DURATION_DAYS).sum()
    
    total_cost = mortality_cost + morbidity_cost
    
    return {
        "total_cost": total_cost,
        "mortality_cost": mortality_cost,
        "morbidity_cost": morbidity_cost
    }

def run_cost_benefit_scenario(
    projected_cases, projected_deaths, projected_species_distribution, 
    intervention_cost, intervention_effectiveness_percent
):
    """
    Runs a cost-benefit analysis for a proposed intervention.
    
    Args:
        projected_cases (int): Estimated cases in a 'No Action' scenario.
        projected_deaths (int): Estimated deaths in a 'No Action' scenario.
        projected_species_distribution (dict): Proportions of affected species.
        intervention_cost (float): Total cost of the control program.
        intervention_effectiveness_percent (int): Percentage of cases that will be prevented.
    
    Returns:
        dict: A dictionary summarizing the scenario analysis.
    """
    # Create a dummy DataFrame to represent the "No Action" scenario
    no_action_df = pd.DataFrame([
        {
            "species": species,
            "cases": projected_cases * proportion,
            "deaths": projected_deaths * proportion
        }
        for species, proportion in projected_species_distribution.items()
    ])
    
    # Cost of doing nothing
    cost_no_action = calculate_direct_outbreak_cost(no_action_df)['total_cost']
    
    # Calculate the impact of the intervention
    effectiveness_factor = intervention_effectiveness_percent / 100.0
    cases_prevented = projected_cases * effectiveness_factor
    deaths_prevented = projected_deaths * effectiveness_factor
    
    # Create a dummy DataFrame for the cases that still occur WITH the intervention
    with_intervention_df = pd.DataFrame([
        {
            "species": species,
            "cases": (projected_cases * proportion) * (1 - effectiveness_factor),
            "deaths": (projected_deaths * proportion) * (1 - effectiveness_factor)
        }
        for species, proportion in projected_species_distribution.items()
    ])
    
    cost_with_intervention_disease = calculate_direct_outbreak_cost(with_intervention_df)['total_cost']
    
    # Total cost of the intervention scenario is the program cost + remaining disease cost
    total_cost_with_intervention = intervention_cost + cost_with_intervention_disease
    
    # Benefits are the costs that were AVERTED
    benefits_averted_cost = cost_no_action - cost_with_intervention_disease
    
    # Net benefit
    net_benefit = benefits_averted_cost - intervention_cost
    
    # Return on Investment (ROI)
    roi = (net_benefit / intervention_cost) * 100 if intervention_cost > 0 else 0

    return {
        "cost_no_action": cost_no_action,
        "cost_with_intervention": total_cost_with_intervention,
        "benefits_averted_cost": benefits_averted_cost,
        "net_benefit": net_benefit,
        "roi_percent": roi
    }