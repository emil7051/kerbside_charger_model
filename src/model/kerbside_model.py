"""
Kerbside Model - Simplified EV Charger RAB economic model.

This module provides a clean, centralized implementation of the EV Charger RAB model
with optimized calculations and streamlined parameter management.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass

# ===========================================
# Constants for the model
# ===========================================
DEFAULT_YEARS = 15  # Standard 15-year analysis period
CHARGERS_PER_YEAR = 5000  # Default annual charger deployment
CAPEX_PER_CHARGER = 6000  # Default capital cost per charger
OPEX_PER_CHARGER = 500   # Default operating cost per charger
DEFAULT_ASSET_LIFE = 8    # Default asset lifetime in years
DEFAULT_WACC = 0.058      # Default Weighted Average Cost of Capital
DEFAULT_CUSTOMER_BASE = 1800000  # Default utility customer base
DEFAULT_REVENUE_PER_CHARGER = 100  # Default third-party revenue per charger

# ===========================================
# Main Model Class
# ===========================================
class KerbsideModel:
    """
    Centralized EV Charger RAB economic model with simplified parameters and methods.
    
    This class encapsulates the entire model functionality, making it easier to
    manage parameters and run different scenarios.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the model with parameters.
        
        Args:
            params: Dictionary of model parameters (uses defaults for any missing)
        """
        # Core parameters with defaults
        self.params = {
            # Deployment parameters
            "chargers_per_year": CHARGERS_PER_YEAR,
            "deployment_years": 5,
            "deployment_delay": 1.0,  # Multiplier on deployment time (>1 means slower)
            
            # Financial parameters
            "capex_per_charger": CAPEX_PER_CHARGER,
            "opex_per_charger": OPEX_PER_CHARGER,
            "asset_life": DEFAULT_ASSET_LIFE,
            "wacc": DEFAULT_WACC,  # Single WACC parameter (can be adjusted by period)
            "wacc_periods": {  # Optional period adjustments
                "6-10": 0.06,
                "11-15": 0.055
            },
            "cost_escalation": 1.0,  # Cost multiplier
            "cost_decline_rate": 0.03,  # Annual technology cost decline
            
            # Customer parameters
            "customer_base": DEFAULT_CUSTOMER_BASE,
            "third_party_revenue": DEFAULT_REVENUE_PER_CHARGER,
            
            # Efficiency parameters (consolidated)
            "efficiency": 1.0,  # Combined efficiency factor (1.0 = fully efficient)
            "efficiency_degradation": 0.0,  # Annual efficiency degradation
            
            # Market parameters
            "market_displacement": 0.0,  # Private market displacement rate
            "innovation_rate": 0.02,  # Market innovation rate
            "monopoly_innovation_rate": 0.01,  # Monopoly innovation rate
            
            # Technology parameters
            "tech_obsolescence_rate": 0.0,  # Tech obsolescence rate
            "utilization": 0.7,  # Capacity utilization
            "risk_premium": 0.0,  # Additional risk premium
        }
        
        # Update with provided parameters
        if params:
            self.params.update(params)
        
        # Results storage
        self.results = {}

    def calculate_wacc(self, year: int) -> float:
        """Calculate the appropriate WACC for a given year."""
        base_wacc = self.params["wacc"]
        
        if "wacc_periods" in self.params:
            if year >= 11 and "11-15" in self.params["wacc_periods"]:
                return self.params["wacc_periods"]["11-15"]
            elif year >= 6 and "6-10" in self.params["wacc_periods"]:
                return self.params["wacc_periods"]["6-10"]
        
        # Add risk premium if specified
        if self.params.get("risk_premium", 0) > 0:
            # Risk premium decreases over time as technology matures
            adjustment = self.params["risk_premium"] * max(0, 1 - 0.05 * (year - 1))
            base_wacc += adjustment
            
        return base_wacc

    def run(self) -> Dict[str, Any]:
        """
        Run the complete model and return results.
        
        Returns:
            Dictionary of results and DataFrames
        """
        years = list(range(1, DEFAULT_YEARS + 1))
        
        # 1. Calculate charger rollout
        rollout_df = self._calculate_rollout(years)
        
        # 2. Calculate depreciation
        depreciation_df = self._calculate_depreciation(rollout_df, years)
        
        # 3. Calculate RAB evolution
        rab_df = self._calculate_rab(rollout_df, depreciation_df, years)
        
        # 4. Calculate revenue requirements
        revenue_df = self._calculate_revenue(rollout_df, rab_df, years)
        
        # 5. Calculate summary statistics
        summary = self._calculate_summary(rollout_df, rab_df, revenue_df)
        
        # 6. Calculate market competition effects
        market_df = self._calculate_market_effects(rollout_df, years)
        
        # Store results
        self.results = {
            "rollout": rollout_df,
            "depreciation": depreciation_df,
            "rab": rab_df,
            "revenue": revenue_df,
            "market": market_df,
            "summary": summary
        }
        
        return self.results
    
    def _calculate_rollout(self, years: List[int]) -> pd.DataFrame:
        """Calculate the charger rollout schedule."""
        df = pd.DataFrame(index=years)
        
        # Calculate deployment period with delay factor
        deployment_years = min(self.params["deployment_years"], len(years))
        if self.params.get("deployment_delay", 1.0) > 1.0:
            deployment_years = min(len(years), int(deployment_years * self.params["deployment_delay"]))
        
        # Calculate annual and cumulative chargers
        df["annual_chargers"] = 0
        
        # Distribute chargers evenly across deployment years
        chargers_per_year = self.params["chargers_per_year"] * self.params["deployment_years"] / deployment_years
        
        for i, year in enumerate(years):
            if i < deployment_years:
                df.loc[year, "annual_chargers"] = chargers_per_year
        
        # Calculate cumulative chargers
        df["cumulative_chargers"] = df["annual_chargers"].cumsum()
        
        # Calculate initial CapEx with cost escalation
        base_capex = self.params["capex_per_charger"] * self.params.get("cost_escalation", 1.0)
        
        # Apply cost decline over time
        cost_decline_rate = self.params.get("cost_decline_rate", 0.0)
        df["unit_capex"] = base_capex * np.power(1 - cost_decline_rate, np.array([y - 1 for y in years]))
        
        # Calculate total CapEx per year
        df["capex"] = df["annual_chargers"] * df["unit_capex"]
        
        return df
    
    def _calculate_depreciation(self, rollout_df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Calculate depreciation with adjustments for technological obsolescence."""
        depreciation_matrix = np.zeros((len(years), len(years)))
        
        for vintage_year in years:
            if rollout_df.loc[vintage_year, "annual_chargers"] == 0:
                continue
                
            # Get capex for this vintage
            capex = rollout_df.loc[vintage_year, "capex"]
            
            # Adjust asset life for technological obsolescence
            asset_life = self.params["asset_life"]
            if self.params.get("tech_obsolescence_rate", 0) > 0:
                # Calculate effective asset life considering obsolescence
                obsolescence_factor = 1 - self.params["tech_obsolescence_rate"] * (1 - np.exp(-vintage_year / 5))
                asset_life = max(1, asset_life * obsolescence_factor)
            
            # Calculate annual depreciation
            annual_depr = capex / asset_life
            
            # Apply depreciation for future years up to asset life
            for future_year in range(vintage_year, min(vintage_year + int(asset_life), len(years))):
                depreciation_matrix[future_year, vintage_year] = annual_depr
        
        # Create DataFrame with depreciation values
        depreciation_df = pd.DataFrame(index=years)
        depreciation_df["total_depreciation"] = depreciation_matrix.sum(axis=1)
        
        return depreciation_df
    
    def _calculate_rab(self, rollout_df: pd.DataFrame, depreciation_df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Calculate Regulated Asset Base (RAB) evolution."""
        rab_df = pd.DataFrame(index=years)
        rab_df["opening_rab"] = 0
        rab_df["additions"] = rollout_df["capex"]
        rab_df["depreciation"] = depreciation_df["total_depreciation"]
        rab_df["closing_rab"] = 0
        
        for i, year in enumerate(years):
            if i == 0:  # First year
                opening_rab = 0
            else:
                opening_rab = rab_df.loc[years[i-1], "closing_rab"]
            
            rab_df.loc[year, "opening_rab"] = opening_rab
            
            # Calculate technological obsolescence writeoffs
            if self.params.get("tech_obsolescence_rate", 0) > 0 and i > 0:
                obsolescence_writeoff = opening_rab * self.params["tech_obsolescence_rate"] * 0.1
            else:
                obsolescence_writeoff = 0
            
            rab_df.loc[year, "obsolescence_writeoff"] = obsolescence_writeoff
            
            # Calculate closing RAB
            closing_rab = (
                opening_rab + 
                rab_df.loc[year, "additions"] - 
                rab_df.loc[year, "depreciation"] -
                obsolescence_writeoff
            )
            
            rab_df.loc[year, "closing_rab"] = closing_rab
        
        # Calculate average RAB
        rab_df["average_rab"] = (rab_df["opening_rab"] + rab_df["closing_rab"]) / 2
        
        return rab_df
    
    def _calculate_revenue(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Calculate revenue requirements with efficiency adjustments."""
        revenue_df = pd.DataFrame(index=years)
        
        # Calculate OpEx with efficiency adjustments
        base_opex = rollout_df["cumulative_chargers"] * self.params["opex_per_charger"]
        
        # Apply efficiency factor and degradation
        efficiency = self.params.get("efficiency", 1.0)
        degradation = self.params.get("efficiency_degradation", 0.0)
        
        efficiency_factors = []
        for year in years:
            # Adjust year for calculation (subtract 1 to maintain same degradation pattern)
            adjusted_year = year - 1
            factor = efficiency * (1 + degradation * adjusted_year)
            efficiency_factors.append(factor)
        
        revenue_df["efficiency_factor"] = efficiency_factors
        revenue_df["opex"] = base_opex * revenue_df["efficiency_factor"]
        
        # Get depreciation from RAB
        revenue_df["depreciation"] = rab_df["depreciation"]
        
        # Calculate return on capital using year-specific WACC
        revenue_df["return_on_capital"] = 0
        for year in years:
            wacc = self.calculate_wacc(year)
            revenue_df.loc[year, "wacc"] = wacc
            revenue_df.loc[year, "return_on_capital"] = rab_df.loc[year, "average_rab"] * wacc
        
        # Calculate total revenue requirement
        revenue_df["total_revenue"] = (
            revenue_df["opex"] + 
            revenue_df["depreciation"] + 
            revenue_df["return_on_capital"]
        )
        
        # Calculate third-party revenue
        revenue_df["third_party_revenue"] = (
            rollout_df["cumulative_chargers"] * self.params["third_party_revenue"]
        )
        
        # Calculate net revenue requirement from customers
        revenue_df["net_revenue"] = revenue_df["total_revenue"] - revenue_df["third_party_revenue"]
        
        # Calculate per-customer bill impact
        revenue_df["bill_impact"] = revenue_df["net_revenue"] / self.params["customer_base"]
        
        # Calculate cumulative bill impact
        revenue_df["cumulative_bill_impact"] = revenue_df["bill_impact"].cumsum()
        
        return revenue_df
    
    def _calculate_summary(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, revenue_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for the model results."""
        years = rollout_df.index.tolist()
        
        # Calculate NPV of revenue
        npv_discount_rate = self.params["wacc"]
        discount_factors = 1 / (1 + npv_discount_rate) ** np.array(years)
        
        npv_revenue = sum(revenue_df["total_revenue"] * discount_factors)
        npv_bill_impact = sum(revenue_df["bill_impact"] * discount_factors)
        
        # Find peak values
        peak_rab = rab_df["closing_rab"].max()
        peak_rab_year = rab_df["closing_rab"].idxmax()
        
        peak_bill_impact = revenue_df["bill_impact"].max()
        peak_bill_year = revenue_df["bill_impact"].idxmax()
        
        # Calculate averages
        avg_bill_impact = revenue_df["bill_impact"].mean()
        total_bill_impact = revenue_df["bill_impact"].sum()
        total_revenue = revenue_df["total_revenue"].sum()
        total_opex = revenue_df["opex"].sum()
        
        # Final metrics
        final_chargers = rollout_df["cumulative_chargers"].iloc[-1]
        final_efficiency = revenue_df["efficiency_factor"].iloc[-1]
        
        # Create summary dictionary
        summary = {
            "total_chargers": float(final_chargers),
            "peak_rab": float(peak_rab),
            "peak_rab_year": int(peak_rab_year),
            "npv_revenue": float(npv_revenue),
            "npv_bill_impact": float(npv_bill_impact),
            "peak_bill_impact": float(peak_bill_impact),
            "peak_bill_year": int(peak_bill_year),
            "avg_bill_impact": float(avg_bill_impact),
            "total_bill_impact": float(total_bill_impact),
            "total_revenue": float(total_revenue),
            "total_opex": float(total_opex),
            "final_efficiency_factor": float(final_efficiency),
        }
        
        return summary
    
    def _calculate_market_effects(self, rollout_df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Calculate market competition effects."""
        market_df = pd.DataFrame(index=years)
        
        # RAB model chargers
        market_df["rab_chargers"] = rollout_df["cumulative_chargers"]
        
        # Calculate baseline private market development
        initial_private = 1000
        private_growth = 0.2
        
        # Adjust year values for calculations (subtract 1 to maintain same relative growth)
        year_values_zero_based = np.array([y - 1 for y in years])
        
        baseline_private = initial_private * np.power(1 + private_growth, year_values_zero_based)
        market_df["baseline_private"] = baseline_private
        
        # Calculate displacement due to RAB
        displacement_rate = self.params.get("market_displacement", 0)
        
        # Displacement increases over time but saturates
        saturation_factors = 1 - np.exp(-year_values_zero_based / 5)
        displacement_factors = displacement_rate * saturation_factors
        
        market_df["displaced_private"] = market_df["baseline_private"] * displacement_factors
        market_df["actual_private"] = market_df["baseline_private"] - market_df["displaced_private"]
        
        # Calculate total market with and without RAB
        market_df["total_with_rab"] = market_df["rab_chargers"] + market_df["actual_private"]
        market_df["total_without_rab"] = market_df["baseline_private"]
        
        # Calculate competitive vs. monopoly costs
        base_capex = self.params["capex_per_charger"]
        innovation_rate = self.params.get("innovation_rate", 0.02)
        monopoly_rate = self.params.get("monopoly_innovation_rate", 0.01)
        
        market_df["competitive_capex"] = base_capex * np.power(1 - innovation_rate, year_values_zero_based)
        market_df["monopoly_capex"] = base_capex * np.power(1 - monopoly_rate, year_values_zero_based)
        
        # Calculate innovation gap
        market_df["innovation_gap"] = market_df["monopoly_capex"] - market_df["competitive_capex"]
        market_df["innovation_gap_pct"] = market_df["innovation_gap"] / market_df["competitive_capex"] * 100
        
        return market_df

    def run_monte_carlo(self, n_simulations: int = 500, parameter_ranges: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation with parameter variations.
        
        Args:
            n_simulations: Number of simulations to run
            parameter_ranges: Dictionary of parameter distributions
            
        Returns:
            Dictionary with simulation results
        """
        if parameter_ranges is None:
            parameter_ranges = self._get_default_parameter_ranges()
        
        # Set random seed for reproducibility
        rng = np.random.default_rng(42)
        
        results = []
        
        for i in range(n_simulations):
            # Generate random parameters
            sim_params = self.params.copy()
            
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
            
            # Create model instance with simulation parameters
            model = KerbsideModel(sim_params)
            model_results = model.run()
            
            # Extract key results
            summary = model_results["summary"]
            
            # Store simulation results
            sim_result = {
                "simulation": i,
                "avg_bill_impact": summary["avg_bill_impact"],
                "peak_bill_impact": summary["peak_bill_impact"],
                "npv_bill_impact": summary["npv_bill_impact"],
                "total_bill_impact": summary["total_bill_impact"],
                "final_efficiency_factor": summary["final_efficiency_factor"],
            }
            
            # Store key parameter values
            for param_name in parameter_ranges.keys():
                if param_name in sim_params:
                    sim_result[f"param_{param_name}"] = sim_params[param_name]
            
            results.append(sim_result)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculate summary statistics
        summary_stats = self._calculate_monte_carlo_summary(results_df)
        
        return {
            "results_df": results_df,
            "summary_stats": summary_stats
        }
    
    def _get_default_parameter_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Get default parameter ranges for Monte Carlo simulation."""
        return {
            "capex_per_charger": {
                "distribution": "triangular",
                "min": 4500,
                "mode": 6000,
                "max": 8000
            },
            "opex_per_charger": {
                "distribution": "triangular",
                "min": 350,
                "mode": 500,
                "max": 700
            },
            "asset_life": {
                "distribution": "triangular", 
                "min": 6,
                "mode": 8,
                "max": 10
            },
            "wacc": {
                "distribution": "normal",
                "mean": 0.058,
                "std": 0.005
            },
            "efficiency": {
                "distribution": "triangular",
                "min": 0.9,
                "mode": 1.0,
                "max": 1.3
            },
            "tech_obsolescence_rate": {
                "distribution": "triangular",
                "min": 0.0,
                "mode": 0.05,
                "max": 0.1
            },
            "market_displacement": {
                "distribution": "triangular",
                "min": 0.0,
                "mode": 0.3,
                "max": 0.7
            }
        }
    
    def _calculate_monte_carlo_summary(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for Monte Carlo results."""
        metrics = [col for col in results_df.columns if not col.startswith("param_") and col != "simulation"]
        
        summary = {}
        
        for metric in metrics:
            values = results_df[metric].values
            
            summary[f"{metric}_mean"] = float(np.mean(values))
            summary[f"{metric}_median"] = float(np.median(values))
            summary[f"{metric}_std"] = float(np.std(values))
            summary[f"{metric}_min"] = float(np.min(values))
            summary[f"{metric}_max"] = float(np.max(values))
            summary[f"{metric}_p10"] = float(np.percentile(values, 10))
            summary[f"{metric}_p90"] = float(np.percentile(values, 90))
        
        # Calculate parameter sensitivities (correlations)
        param_cols = [col for col in results_df.columns if col.startswith("param_")]
        
        correlations = {}
        for metric in metrics:
            metric_corrs = {}
            
            for param in param_cols:
                param_name = param.replace("param_", "")
                corr = np.corrcoef(results_df[param], results_df[metric])[0, 1]
                metric_corrs[param_name] = float(corr)
            
            # Sort by absolute correlation
            correlations[metric] = dict(sorted(
                metric_corrs.items(), 
                key=lambda x: abs(x[1]), 
                reverse=True
            ))
        
        summary["correlations"] = correlations
        
        return summary 