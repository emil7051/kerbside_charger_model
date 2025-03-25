"""
Monte Carlo simulation for the Kerbside Model.

This module contains functionality for running sensitivity analysis through
Monte Carlo simulations of the Kerbside Model with varying parameters.
"""

from typing import Dict, List, Any, Optional, TypedDict
import numpy as np
import pandas as pd
import streamlit as st
from src.utils.parameters import (
    DEFAULT_WACC,
    DEFAULT_RANDOM_SEED,
    DEFAULT_PARAMETER_RANGES
)
from src.model.kerbside_model import KerbsideModel, run_model_calculations
from src.utils.config import (
    MAX_MONTE_CARLO_SIMULATIONS,
    USE_PARALLEL_COMPUTATION,
    N_PARALLEL_JOBS
)


class MonteCarloResults(TypedDict):
    """Results of Monte Carlo simulations."""
    results_df: pd.DataFrame       # Individual simulation results
    summary_stats: Dict[str, Any]  # Statistical summary of simulations


@st.cache_data
def run_monte_carlo(base_model: KerbsideModel, n_simulations: int = 500, 
                   parameter_ranges: Optional[Dict[str, Dict[str, Any]]] = None) -> MonteCarloResults:
    """
    Run Monte Carlo simulations to analyze sensitivity to parameter variations.
    
    This function is cached using Streamlit's cache_data decorator to prevent
    unnecessary recalculations when the same parameters are used multiple times.
    
    Args:
        base_model: Base model with default parameters
        n_simulations: Number of simulations to run
        parameter_ranges: Optional dictionary of parameter distributions
        
    Returns:
        Dictionary with simulation results and statistics
    """
    # Use default parameter ranges if none provided
    if parameter_ranges is None:
        parameter_ranges = DEFAULT_PARAMETER_RANGES
    
    # WACC is fixed and not varied
    if "wacc" in parameter_ranges:
        del parameter_ranges["wacc"]
    
    # Ensure n_simulations doesn't exceed the maximum
    n_simulations = min(n_simulations, MAX_MONTE_CARLO_SIMULATIONS)
    
    # Set random seed for reproducibility
    rng = np.random.default_rng(DEFAULT_RANDOM_SEED)
    
    # Get base parameters to simulate from
    base_params = base_model.params.copy()
    
    # Run simulations and collect results
    if USE_PARALLEL_COMPUTATION:
        results = run_parallel_simulations(base_params, parameter_ranges, n_simulations, rng)
    else:
        results = run_sequential_simulations(base_params, parameter_ranges, n_simulations, rng)
    
    # Calculate summary statistics
    results_df = pd.DataFrame(results)
    summary_stats = calculate_monte_carlo_summary(results_df)
    
    return {
        "results_df": results_df,
        "summary_stats": summary_stats
    }

def run_sequential_simulations(base_params: Dict[str, Any], 
                              parameter_ranges: Dict[str, Dict[str, Any]],
                              n_simulations: int,
                              rng: np.random.Generator) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations sequentially.
    
    Args:
        base_params: Base model parameters
        parameter_ranges: Dictionary of parameter distributions
        n_simulations: Number of simulations to run
        rng: Random number generator
        
    Returns:
        List of simulation results
    """
    results = []
    for i in range(n_simulations):
        # Generate random parameters for this simulation
        sim_params = generate_simulation_parameters(base_params, parameter_ranges, rng)
        
        # Run model with these parameters using the cached calculation function
        model_results = run_model_calculations(
            chargers_per_year=sim_params["chargers_per_year"],
            deployment_years=sim_params["deployment_years"],
            deployment_delay=sim_params.get("deployment_delay", base_params["deployment_delay"]),
            capex_per_charger=sim_params["capex_per_charger"],
            opex_per_charger=sim_params["opex_per_charger"],
            asset_life=sim_params["asset_life"],
            wacc=sim_params["wacc"],
            customer_base=sim_params.get("customer_base", base_params["customer_base"]),
            third_party_revenue=sim_params.get("third_party_revenue", base_params["third_party_revenue"]),
            efficiency=sim_params["efficiency"],
            efficiency_degradation=sim_params.get("efficiency_degradation", base_params["efficiency_degradation"]),
            tech_obsolescence_rate=sim_params["tech_obsolescence_rate"],
            market_displacement=sim_params["market_displacement"]
        )
        
        # Extract and store key results
        sim_result = {
            "simulation": i,
            "avg_bill_impact": model_results["summary"]["avg_bill_impact"],
            "peak_bill_impact": model_results["summary"]["peak_bill_impact"],
            "npv_bill_impact": model_results["summary"]["npv_bill_impact"],
            "total_bill_impact": model_results["summary"]["total_bill_impact"],
            "final_efficiency_factor": model_results["summary"]["final_efficiency_factor"],
        }
        
        # Store parameter values used
        for param_name in parameter_ranges.keys():
            if param_name in sim_params:
                sim_result[f"param_{param_name}"] = sim_params[param_name]
        
        results.append(sim_result)
    
    return results

def run_parallel_simulations(base_params: Dict[str, Any], 
                            parameter_ranges: Dict[str, Dict[str, Any]],
                            n_simulations: int,
                            rng: np.random.Generator) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations in parallel.
    
    This is a placeholder for parallel implementation. Currently falls back to sequential.
    For actual implementation, libraries like joblib or concurrent.futures could be used.
    
    Args:
        base_params: Base model parameters
        parameter_ranges: Dictionary of parameter distributions
        n_simulations: Number of simulations to run
        rng: Random number generator
        
    Returns:
        List of simulation results
    """
    # For now, we'll fall back to sequential processing
    # In a future implementation, this would use joblib or concurrent.futures
    st.warning("Parallel computation is enabled in config but not yet implemented. Using sequential processing.")
    return run_sequential_simulations(base_params, parameter_ranges, n_simulations, rng)

def generate_simulation_parameters(base_params: Dict[str, Any],
                                  parameter_ranges: Dict[str, Dict[str, Any]],
                                  rng: np.random.Generator) -> Dict[str, Any]:
    """
    Generate random parameters for a Monte Carlo simulation.
    
    Args:
        base_params: Base model parameters dictionary
        parameter_ranges: Dictionary defining parameter distribution shapes and ranges
        rng: NumPy random number generator instance
        
    Returns:
        Dictionary of parameters for a single simulation run
    """
    sim_params = base_params.copy()
    
    for param_name, param_range in parameter_ranges.items():
        if param_name not in sim_params:
            continue
        
        dist_type = param_range.get("distribution", "uniform")
        
        if dist_type == "uniform":
            min_val = param_range.get("min", sim_params[param_name] * 0.8)
            max_val = param_range.get("max", sim_params[param_name] * 1.2)
            sim_params[param_name] = rng.uniform(min_val, max_val)
            
        elif dist_type == "triangular":
            min_val = param_range.get("min", sim_params[param_name] * 0.8)
            max_val = param_range.get("max", sim_params[param_name] * 1.2)
            mode = param_range.get("mode", sim_params[param_name])
            sim_params[param_name] = rng.triangular(min_val, mode, max_val)
        
        elif dist_type == "normal":
            mean = param_range.get("mean", sim_params[param_name])
            std = param_range.get("std", sim_params[param_name] * 0.1)
            sim_params[param_name] = rng.normal(mean, std)
    
    # WACC is always fixed
    sim_params["wacc"] = DEFAULT_WACC
    
    return sim_params

@st.cache_data
def calculate_monte_carlo_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics from Monte Carlo results.
    
    This function is cached using Streamlit's cache_data decorator to prevent
    unnecessary recalculations when the same results dataframe is processed multiple times.
    
    Args:
        results_df: DataFrame containing all Monte Carlo simulation results
        
    Returns:
        Dictionary of statistical summaries for each metric
    """
    # Identify metrics columns
    metrics = [col for col in results_df.columns 
              if not col.startswith("param_") and col != "simulation"]
    
    summary = {}
    
    # Calculate statistics for each metric
    for metric in metrics:
        values = results_df[metric].values
        
        summary[f"{metric}_mean"] = float(np.mean(values))
        summary[f"{metric}_median"] = float(np.median(values))
        summary[f"{metric}_std"] = float(np.std(values))
        summary[f"{metric}_min"] = float(np.min(values))
        summary[f"{metric}_max"] = float(np.max(values))
        summary[f"{metric}_p10"] = float(np.percentile(values, 10))
        summary[f"{metric}_p90"] = float(np.percentile(values, 90))
    
    # Calculate correlations between parameters and metrics
    param_cols = [col for col in results_df.columns if col.startswith("param_")]
    correlations = {}
    
    for metric in metrics:
        metric_corrs = {}
        
        for param in param_cols:
            param_name = param.replace("param_", "")
            corr = np.corrcoef(results_df[param], results_df[metric])[0, 1]
            metric_corrs[param_name] = float(corr)
        
        # Sort by correlation magnitude
        correlations[metric] = dict(sorted(
            metric_corrs.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ))
    
    summary["correlations"] = correlations
    
    return summary 