"""Monte Carlo simulation engine for the EV charger model."""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from .base_model import run_ev_charger_model
from .distributional import calculate_distributional_impact
from .competitive import calculate_private_market_development, calculate_innovation_impact
from ..data.distributions import generate_parameter_set

def run_monte_carlo_simulation(
    base_params: Dict[str, Any],
    n_simulations: int = 500,
    custom_dist_params: Optional[Dict[str, Dict[str, Any]]] = None,
    seed: Optional[int] = None,
    include_distributional: bool = True,
    include_competitive: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run a Monte Carlo simulation of the model.
    
    Args:
        base_params: Base parameters for the model
        n_simulations: Number of simulations to run
        custom_dist_params: Custom parameter distributions
        seed: Random seed for reproducibility
        include_distributional: Whether to include distributional analysis
        include_competitive: Whether to include competitive market analysis
        
    Returns:
        Tuple of (results_df, summary_stats)
    """
    # Initialise random number generator
    rng = np.random.default_rng(seed)
    
    # Results storage
    results = []
    
    # Run simulations
    for sim_idx in range(n_simulations):
        # Generate parameter set for this simulation
        params = generate_parameter_set(rng)
        
        # Update with base parameters as defaults
        for key, value in base_params.items():
            if key not in params:
                params[key] = value
        
        # Skip extended calculations for performance
        params["skip_ext_calcs"] = True
        
        # Run the model
        (rollout_df, depreciation_df, rab_df, revenue_df, summary_stats, _, _) = run_ev_charger_model(params)
        
        # Create a result entry
        result = {
            "simulation": sim_idx,
            "total_chargers": summary_stats["Total Chargers"],
            "npv_revenue": summary_stats["NPV of Revenue Requirement"],
            "total_bill_impact": summary_stats["Cumulative Bill Impact/Customer"],
            "avg_annual_bill": summary_stats["Average Annual Bill Impact"],
            "peak_rab": summary_stats["Peak RAB"],
            "peak_bill_impact": summary_stats["Peak Annual Bill Impact"],
        }
        
        # Add parameter values
        for key, value in params.items():
            if isinstance(value, (int, float, bool)) and key != "skip_ext_calcs":
                result[f"param_{key}"] = value
        
        # Run distributional analysis if requested
        if include_distributional:
            dist_df = calculate_distributional_impact(revenue_df)
            
            # Extract key distributional metrics
            q1_data = dist_df[dist_df["quintile"] == "Q1"].iloc[0]
            q5_data = dist_df[dist_df["quintile"] == "Q5"].iloc[0]
            
            result["q1_pct_income"] = q1_data["impact_pct_income"]
            result["q5_pct_income"] = q5_data["impact_pct_income"]
            result["regressivity_ratio"] = q1_data["regressivity_ratio_income"]
        
        # Run competitive market analysis if requested
        if include_competitive:
            years = rollout_df.index.tolist()
            
            # Calculate private market development
            market_df = calculate_private_market_development(years, params)
            
            # Calculate innovation impact
            innovation_df = calculate_innovation_impact(years, params)
            
            # Extract key metrics
            final_year = years[-1]
            
            result["private_displacement_pct"] = market_df.loc[final_year, "displacement_percentage"]
            result["innovation_gap_pct"] = innovation_df.loc[final_year, "innovation_gap_pct"]
            result["final_private_market"] = market_df.loc[final_year, "actual_private"]
            result["final_total_market"] = market_df.loc[final_year, "total_with_rab"]
        
        results.append(result)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Calculate summary statistics
    summary_stats = calculate_monte_carlo_summary(results_df)
    
    return results_df, summary_stats

def calculate_monte_carlo_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics for Monte Carlo results.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        
    Returns:
        Dictionary of summary statistics
    """
    # Calculate statistics for key metrics
    metrics = [
        "total_chargers", "npv_revenue", "total_bill_impact", "avg_annual_bill",
        "peak_rab", "peak_bill_impact"
    ]
    
    # Add distributional metrics if available
    if "regressivity_ratio" in results_df.columns:
        metrics.extend(["q1_pct_income", "q5_pct_income", "regressivity_ratio"])
    
    # Add competitive metrics if available
    if "private_displacement_pct" in results_df.columns:
        metrics.extend(["private_displacement_pct", "innovation_gap_pct", 
                       "final_private_market", "final_total_market"])
    
    summary = {}
    
    for metric in metrics:
        if metric not in results_df.columns:
            continue
            
        values = results_df[metric].values
        
        summary[f"{metric}_mean"] = float(np.mean(values))
        summary[f"{metric}_median"] = float(np.median(values))
        summary[f"{metric}_std"] = float(np.std(values))
        summary[f"{metric}_min"] = float(np.min(values))
        summary[f"{metric}_max"] = float(np.max(values))
        summary[f"{metric}_p10"] = float(np.percentile(values, 10))
        summary[f"{metric}_p25"] = float(np.percentile(values, 25))
        summary[f"{metric}_p75"] = float(np.percentile(values, 75))
        summary[f"{metric}_p90"] = float(np.percentile(values, 90))
    
    # Calculate correlation matrix for parameter sensitivities
    param_cols = [col for col in results_df.columns if col.startswith("param_")]
    
    if param_cols and metrics:
        # Calculate correlations between parameters and outcomes
        correlations = {}
        
        for metric in metrics:
            if metric not in results_df.columns:
                continue
                
            metric_corrs = {}
            
            for param in param_cols:
                corr = np.corrcoef(results_df[param], results_df[metric])[0, 1]
                if not np.isnan(corr):
                    metric_corrs[param.replace("param_", "")] = corr
            
            # Sort by absolute correlation value
            correlations[metric] = dict(sorted(
                metric_corrs.items(), 
                key=lambda x: abs(x[1]), 
                reverse=True
            ))
        
        summary["correlations"] = correlations
    
    return summary

def run_scenario_comparison(
    scenarios: Dict[str, Dict[str, Any]],
    n_simulations: int = 100,
    include_distributional: bool = True,
    include_competitive: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulations for multiple scenarios and compare results.
    
    Args:
        scenarios: Dictionary of scenarios to compare {name: params}
        n_simulations: Number of simulations per scenario
        include_distributional: Whether to include distributional analysis
        include_competitive: Whether to include competitive market analysis
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with results for each scenario
    """
    results = {}
    
    for scenario_name, params in scenarios.items():
        # Run Monte Carlo simulation for this scenario
        results_df, summary_stats = run_monte_carlo_simulation(
            params,
            n_simulations=n_simulations,
            include_distributional=include_distributional,
            include_competitive=include_competitive,
            seed=seed
        )
        
        # Store results
        results[scenario_name] = {
            "results_df": results_df,
            "summary_stats": summary_stats
        }
    
    return results 