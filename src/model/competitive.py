"""Market displacement and innovation effects for the EV charger model."""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from .base_model import run_ev_charger_model

def calculate_private_market_development(
    years: List[int],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate private market development with and without RAB displacement.
    
    Args:
        years: List of years for analysis
        params: Model parameters
        
    Returns:
        DataFrame with private market charger deployment
    """
    df = pd.DataFrame(index=years)
    
    # Get parameters
    initial_private_chargers = params.get("InitialPrivateChargers", 1000)
    baseline_growth_rate = params.get("BaselinePrivateGrowth", 0.1)
    private_market_displacement = params.get("PrivateMarketDisplacement", 0.0)
    
    # Calculate baseline private market (without RAB)
    baseline_private = []
    
    for year in years:
        chargers = initial_private_chargers * (1 + baseline_growth_rate) ** year
        baseline_private.append(chargers)
    
    df["baseline_private"] = baseline_private
    
    # Calculate RAB chargers
    rab_chargers = []
    annual_chargers = params.get("ChargersPerYear", 5000)
    deployment_years = min(5, len(years))
    
    cumulative = 0
    for year in years:
        if year < deployment_years:
            cumulative += annual_chargers
        rab_chargers.append(cumulative)
    
    df["rab_chargers"] = rab_chargers
    
    # Calculate displacement factor
    displacement_factors = []
    
    for year in years:
        if year == 0:
            displacement_factors.append(0)
        else:
            # Displacement increases over time but saturates
            saturation_factor = 1 - np.exp(-year / 5)
            year_factor = private_market_displacement * saturation_factor
            displacement_factors.append(year_factor)
    
    df["displacement_factor"] = displacement_factors
    
    # Calculate actual private market (with RAB)
    actual_private = []
    
    for year in years:
        displaced = baseline_private[year] * (1 - displacement_factors[year])
        actual_private.append(displaced)
    
    df["actual_private"] = actual_private
    
    # Calculate total market with and without RAB
    df["total_with_rab"] = df["rab_chargers"] + df["actual_private"]
    df["total_without_rab"] = df["baseline_private"]
    
    # Calculate displacement percentage
    df["displacement_percentage"] = (
        (df["baseline_private"] - df["actual_private"]) / df["baseline_private"] * 100
    )
    
    return df

def calculate_innovation_impact(
    years: List[int],
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate innovation impact on costs between competitive and monopoly markets.
    
    Args:
        years: List of years for analysis
        params: Model parameters
        
    Returns:
        DataFrame with innovation impacts
    """
    df = pd.DataFrame(index=years)
    
    # Get parameters
    initial_capex = params.get("CapExPerCharger", 6000)
    innovation_rate = params.get("InnovationRate", 0.02)
    monopoly_innovation_rate = params.get("MonopolyInnovationRate", 0.01)
    
    # Calculate cost trajectories
    competitive_capex = []
    monopoly_capex = []
    
    for year in years:
        comp_capex = initial_capex * (1 - innovation_rate) ** year
        mono_capex = initial_capex * (1 - monopoly_innovation_rate) ** year
        
        competitive_capex.append(comp_capex)
        monopoly_capex.append(mono_capex)
    
    df["competitive_capex"] = competitive_capex
    df["monopoly_capex"] = monopoly_capex
    
    # Calculate innovation gap
    df["innovation_gap"] = df["monopoly_capex"] - df["competitive_capex"]
    df["innovation_gap_pct"] = (
        df["innovation_gap"] / df["competitive_capex"] * 100
    )
    
    # Calculate cumulative innovation gap
    # This is the additional cost paid for equivalent chargers
    df["cumulative_gap"] = df["innovation_gap"].cumsum()
    
    return df

def run_comparative_scenario(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a comparative analysis between regulated and competitive models.
    
    Args:
        params: Base parameter set
        
    Returns:
        Dictionary of metrics and DataFrames comparing the two models
    """
    # First, run the RAB model
    (rollout_df, _, rab_df, revenue_df, summary_stats, _, _) = run_ev_charger_model(params)
    years = rollout_df.index.tolist()
    
    # Calculate private market development
    market_df = calculate_private_market_development(years, params)
    
    # Calculate innovation impact
    innovation_df = calculate_innovation_impact(years, params)
    
    # Create a competitive market scenario
    comp_params = params.copy()
    comp_params["PrivateMarketDisplacement"] = 0.0
    comp_params["InnovationRate"] = params.get("InnovationRate", 0.02)
    
    # Create a combined DataFrame for market analysis
    combined_df = pd.DataFrame(index=years)
    combined_df["rab_chargers"] = market_df["rab_chargers"]
    combined_df["private_chargers_with_rab"] = market_df["actual_private"]
    combined_df["private_chargers_without_rab"] = market_df["baseline_private"]
    combined_df["total_chargers_with_rab"] = market_df["total_with_rab"]
    combined_df["total_chargers_without_rab"] = market_df["total_without_rab"]
    
    # Calculate net market effect
    combined_df["net_market_effect"] = (
        combined_df["total_chargers_with_rab"] - combined_df["total_chargers_without_rab"]
    )
    
    # Calculate cost differential
    combined_df["rab_cost_per_charger"] = innovation_df["monopoly_capex"]
    combined_df["competitive_cost_per_charger"] = innovation_df["competitive_capex"]
    
    # Calculate total costs
    combined_df["rab_total_cost"] = combined_df["rab_chargers"] * combined_df["rab_cost_per_charger"]
    combined_df["competitive_total_cost"] = (
        combined_df["total_chargers_without_rab"] * combined_df["competitive_cost_per_charger"]
    )
    
    # Calculate cost differential
    combined_df["cost_differential"] = combined_df["rab_total_cost"] - combined_df["competitive_total_cost"]
    
    # Calculate summary metrics
    final_year = years[-1]
    
    total_rab_chargers = combined_df.loc[final_year, "rab_chargers"]
    total_private_with_rab = combined_df.loc[final_year, "private_chargers_with_rab"]
    total_private_without_rab = combined_df.loc[final_year, "private_chargers_without_rab"]
    
    total_with_rab = combined_df.loc[final_year, "total_chargers_with_rab"]
    total_without_rab = combined_df.loc[final_year, "total_chargers_without_rab"]
    
    market_growth_percentage = (
        (total_with_rab - total_without_rab) / total_without_rab * 100
        if total_without_rab > 0 else 0
    )
    
    private_displacement_percentage = (
        (total_private_without_rab - total_private_with_rab) / total_private_without_rab * 100
        if total_private_without_rab > 0 else 0
    )
    
    # Create summary metrics dictionary
    metrics = {
        "total_rab_chargers": float(total_rab_chargers),
        "total_private_with_rab": float(total_private_with_rab),
        "total_private_without_rab": float(total_private_without_rab),
        "total_chargers_with_rab": float(total_with_rab),
        "total_chargers_without_rab": float(total_without_rab),
        "market_growth_percentage": float(market_growth_percentage),
        "private_displacement_percentage": float(private_displacement_percentage),
        "final_innovation_gap_pct": float(innovation_df.loc[final_year, "innovation_gap_pct"]),
        "total_innovation_cost": float(combined_df["cost_differential"].sum()),
    }
    
    return {
        "metrics": metrics,
        "market_df": market_df,
        "innovation_df": innovation_df,
        "combined_df": combined_df,
    } 