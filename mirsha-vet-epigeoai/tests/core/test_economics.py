import pandas as pd
from src.core import economics as econ

def test_calculate_direct_outbreak_cost():
    """
    Tests the direct outbreak cost calculation with a known dataset.
    """
    # 1. Prepare a simple test DataFrame
    test_data = pd.DataFrame([
        {"species": "Cattle", "cases": 10, "deaths": 2}, # 2 deaths * 30000 = 60000
        {"species": "Sheep", "cases": 50, "deaths": 10}  # 10 deaths * 4000 = 40000
    ])
    
    # Manually calculate expected morbidity cost
    # (10 cattle * 150 ETB/day * 21 days) + (50 sheep * 20 ETB/day * 21 days)
    expected_morbidity = (10 * 150 * 21) + (50 * 20 * 21) # 31500 + 21000 = 52500
    
    expected_mortality = (2 * 30000) + (10 * 4000) # 60000 + 40000 = 100000
    expected_total = expected_morbidity + expected_mortality # 152500

    # 2. Run the function
    result = econ.calculate_direct_outbreak_cost(test_data)

    # 3. Assert that the results are correct
    assert result["mortality_cost"] == expected_mortality
    assert result["morbidity_cost"] == expected_morbidity
    assert result["total_cost"] == expected_total

def test_run_cost_benefit_scenario():
    """
    Tests the cost-benefit scenario planner with a known set of inputs.
    """
    scenario_result = econ.run_cost_benefit_scenario(
        projected_cases=1000,
        projected_deaths=100,
        projected_species_distribution={"Cattle": 1.0}, # Simplify to only cattle
        intervention_cost=1_000_000,
        intervention_effectiveness_percent=90
    )

    # Expected Cost (No Action): 100 deaths * 30k + 1000 cases * 150/day * 21 days
    expected_cost_no_action = (100 * 30000) + (1000 * 150 * 21) # 3M + 3.15M = 6.15M
    
    # Expected ROI = (Benefits - Cost) / Cost
    # Benefits = 90% of 6.15M = 5,535,000
    # Net Benefit = 5,535,000 - 1,000,000 = 4,535,000
    # ROI = 4,535,000 / 1,000,000 = 453.5%
    
    assert scenario_result["cost_no_action"] == expected_cost_no_action
    assert round(scenario_result["roi_percent"], 1) == 453.5