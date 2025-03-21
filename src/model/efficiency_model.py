"""Operational inefficiency modelling for the EV charger model."""

from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from .base_model import run_ev_charger_model

def calculate_efficiency_metrics(
    rollout_df: pd.DataFrame,
    revenue_df: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate efficiency metrics for the model."""
    years = rollout_df.index.tolist()
    metrics = {}
    
    # Calculate efficiency factor over time
    efficiency_factor = params.get("EfficiencyFactor", 1.0)
    efficiency_degradation = params.get("EfficiencyDegradation", 0.0)
    
    efficiency_factors = []
    for year in years:
        year_factor = efficiency_factor * (1 + efficiency_degradation * year)
        efficiency_factors.append(year_factor)
    
    metrics["efficiency_factors"] = efficiency_factors
    
    # Calculate efficient OpEx (without inefficiency)
    efficient_opex = []
    actual_opex = revenue_df["opex"].values
    
    for year in years:
        base_opex = rollout_df.loc[year, "cumulative_chargers"] * params["OpExPerCharger"]
        efficient_opex.append(base_opex)
    
    metrics["efficient_opex"] = efficient_opex
    metrics["actual_opex"] = actual_opex
    metrics["inefficiency_premium"] = np.array(actual_opex) - np.array(efficient_opex)
    
    # Calculate efficiency impact on bill
    efficient_bill = []
    actual_bill = revenue_df["per_customer_impact"].values
    
    # Create a hypothetical scenario with perfect efficiency
    efficient_params = params.copy()
    efficient_params["EfficiencyFactor"] = 1.0
    efficient_params["EfficiencyDegradation"] = 0.0
    efficient_params["OperationalEfficiency"] = 1.0
    efficient_params["DeploymentDelay"] = 1.0
    efficient_params["CostEscalation"] = 1.0
    efficient_params["skip_ext_calcs"] = True  # Skip distributional and competitive calcs
    
    # Run the model with efficient parameters
    (_, _, _, efficient_revenue_df, _, _, _) = run_ev_charger_model(efficient_params)
    
    efficient_bill = efficient_revenue_df["per_customer_impact"].values
    metrics["efficient_bill"] = efficient_bill
    metrics["actual_bill"] = actual_bill
    metrics["inefficiency_bill_premium"] = np.array(actual_bill) - np.array(efficient_bill)
    
    # Calculate total inefficiency premium
    metrics["total_inefficiency_premium"] = sum(metrics["inefficiency_premium"])
    metrics["total_bill_inefficiency"] = sum(metrics["inefficiency_bill_premium"])
    metrics["percent_bill_inefficiency"] = (
        metrics["total_bill_inefficiency"] / sum(efficient_bill) * 100
        if sum(efficient_bill) > 0 else 0
    )
    
    return metrics

def run_efficiency_sensitivity(
    base_params: Dict[str, Any],
    efficiency_params: List[str],
    ranges: Dict[str, Tuple[float, float, int]]
) -> Dict[str, pd.DataFrame]:
    """
    Run sensitivity analysis on efficiency parameters.
    
    Args:
        base_params: Base parameter set
        efficiency_params: List of efficiency parameter names to analyse
        ranges: Dictionary of parameter ranges {param_name: (min, max, steps)}
    
    Returns:
        Dictionary of DataFrames with sensitivity results
    """
    sensitivity_results = {}
    
    for param_name in efficiency_params:
        if param_name not in base_params or param_name not in ranges:
            continue
            
        param_min, param_max, steps = ranges[param_name]
        param_values = np.linspace(param_min, param_max, steps)
        
        results = []
        for value in param_values:
            # Create a parameter set with this value
            params = base_params.copy()
            params[param_name] = value
            params["skip_ext_calcs"] = True
            
            # Run the model
            (rollout_df, _, _, revenue_df, summary_stats, _, _) = run_ev_charger_model(params)
            
            # Calculate efficiency metrics
            efficiency_metrics = calculate_efficiency_metrics(rollout_df, revenue_df, params)
            
            # Store results
            results.append({
                "param_value": value,
                "avg_bill_impact": summary_stats["Average Annual Bill Impact"],
                "total_bill_impact": summary_stats["Cumulative Bill Impact/Customer"],
                "total_inefficiency_premium": efficiency_metrics["total_inefficiency_premium"],
                "percent_bill_inefficiency": efficiency_metrics["percent_bill_inefficiency"],
            })
            
        # Convert to DataFrame
        sensitivity_results[param_name] = pd.DataFrame(results)
    
    return sensitivity_results 