"""
Kerbside Model - EV Charger RAB economic model.

This model simulates the financial impacts of deploying electric vehicle (EV) chargers 
through a Regulated Asset Base (RAB) approach.
"""

from typing import Dict, List, Any, Optional, TypedDict
import numpy as np
import pandas as pd
import streamlit as st
from src.utils.parameters import (
    DEFAULT_YEARS, 
    DEFAULT_CHARGERS_PER_YEAR, 
    DEFAULT_CAPEX_PER_CHARGER, 
    DEFAULT_OPEX_PER_CHARGER,
    DEFAULT_ASSET_LIFE, 
    DEFAULT_WACC, 
    DEFAULT_CUSTOMER_BASE, 
    DEFAULT_REVENUE_PER_CHARGER,
    DEFAULT_DEPLOYMENT_YEARS, 
    DEFAULT_DEPLOYMENT_DELAY,
    DEFAULT_EFFICIENCY,
    DEFAULT_EFFICIENCY_DEGRADATION,
    DEFAULT_TECH_OBSOLESCENCE_RATE,
    DEFAULT_MARKET_DISPLACEMENT,
    DEFAULT_INITIAL_PRIVATE_CHARGERS, 
    DEFAULT_PRIVATE_GROWTH_RATE,
    DEFAULT_SATURATION_TIME_CONSTANT,
    DEFAULT_OBSOLESCENCE_FACTOR
)

# Type definitions for model outputs
class ModelResults(TypedDict):
    rollout: pd.DataFrame      # Charger deployment data
    depreciation: pd.DataFrame # Depreciation calculations
    rab: pd.DataFrame          # Regulated Asset Base evolution
    revenue: pd.DataFrame      # Revenue requirements and bill impacts
    market: pd.DataFrame       # Market competition effects
    summary: Dict[str, float]  # Key performance metrics

# Define a standalone cached function for calculations
@st.cache_data
def run_model_calculations(
    chargers_per_year: float,
    deployment_years: int,
    deployment_delay: float,
    capex_per_charger: float,
    opex_per_charger: float,
    asset_life: int,
    wacc: float,
    customer_base: int,
    third_party_revenue: float,
    efficiency: float,
    efficiency_degradation: float,
    tech_obsolescence_rate: float,
    market_displacement: float
) -> ModelResults:
    """
    Run model calculations with caching.
    
    This standalone function allows for proper Streamlit caching by avoiding 
    class methods with 'self' parameters that cannot be hashed.
    
    Parameters:
        chargers_per_year: Annual charger deployment rate
        deployment_years: Period over which chargers are deployed
        deployment_delay: Factor to adjust deployment speed
        capex_per_charger: Capital expenditure per charger
        opex_per_charger: Annual operating expense per charger
        asset_life: Expected lifetime of charger assets
        wacc: Weighted Average Cost of Capital
        customer_base: Number of utility customers
        third_party_revenue: Revenue per charger from third parties
        efficiency: Operational efficiency factor
        efficiency_degradation: Annual change in efficiency
        tech_obsolescence_rate: Rate of technology obsolescence
        market_displacement: Rate at which RAB deployment displaces private investment
        
    Returns:
        Dictionary with model results and metrics
    """
    # Create model instance and set parameters
    model = KerbsideModel({
        "chargers_per_year": chargers_per_year,
        "deployment_years": deployment_years,
        "deployment_delay": deployment_delay,
        "capex_per_charger": capex_per_charger,
        "opex_per_charger": opex_per_charger,
        "asset_life": asset_life,
        "wacc": wacc,
        "customer_base": customer_base,
        "third_party_revenue": third_party_revenue,
        "efficiency": efficiency,
        "efficiency_degradation": efficiency_degradation,
        "tech_obsolescence_rate": tech_obsolescence_rate,
        "market_displacement": market_displacement
    })
    
    # Run model calculations but bypass the run method's cache check
    return model._run_calculations()

class KerbsideModel:
    """
    This model calculates:
    - Deployment schedule for EV chargers
    - Asset depreciation and RAB evolution
    - Revenue requirements and customer bill impacts
    - Market competition effects
    - Monte Carlo simulations for sensitivity analysis
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialise the model with parameters."""
        # Default model parameters
        self.params = {
            # Deployment parameters
            "chargers_per_year": DEFAULT_CHARGERS_PER_YEAR,
            "deployment_years": DEFAULT_DEPLOYMENT_YEARS,
            "deployment_delay": DEFAULT_DEPLOYMENT_DELAY,
            
            # Financial parameters
            "capex_per_charger": DEFAULT_CAPEX_PER_CHARGER,
            "opex_per_charger": DEFAULT_OPEX_PER_CHARGER,
            "asset_life": DEFAULT_ASSET_LIFE,
            "wacc": DEFAULT_WACC,
            
            # Customer parameters
            "customer_base": DEFAULT_CUSTOMER_BASE,
            "third_party_revenue": DEFAULT_REVENUE_PER_CHARGER,
            
            # Efficiency & market parameters
            "efficiency": DEFAULT_EFFICIENCY,
            "efficiency_degradation": DEFAULT_EFFICIENCY_DEGRADATION,
            "market_displacement": DEFAULT_MARKET_DISPLACEMENT,
            "tech_obsolescence_rate": DEFAULT_TECH_OBSOLESCENCE_RATE,
        }
        
        # Update with any provided parameters
        if params:
            self.params.update(params)
        
        # Validate parameters to prevent edge cases
        self._validate_parameters()
        
        self.results = {}

    def _validate_parameters(self):
        """Validate model parameters to prevent edge cases."""
        # Ensure no divide-by-zero errors
        if self.params["asset_life"] <= 0:
            self.params["asset_life"] = DEFAULT_ASSET_LIFE
            print(f"Warning: Asset life must be positive. Reset to default value: {DEFAULT_ASSET_LIFE}")
            
        if self.params["customer_base"] <= 0:
            self.params["customer_base"] = DEFAULT_CUSTOMER_BASE
            print(f"Warning: Customer base must be positive. Reset to default value: {DEFAULT_CUSTOMER_BASE}")
            
        # Ensure reasonable values for percentage-based parameters
        if self.params["wacc"] < 0:
            self.params["wacc"] = DEFAULT_WACC
            print(f"Warning: WACC must be non-negative. Reset to default value: {DEFAULT_WACC}")
            
        if self.params["tech_obsolescence_rate"] < 0:
            self.params["tech_obsolescence_rate"] = DEFAULT_TECH_OBSOLESCENCE_RATE
            print(f"Warning: Technology obsolescence rate must be non-negative. Reset to default value: {DEFAULT_TECH_OBSOLESCENCE_RATE}")
            
        if self.params["market_displacement"] < 0 or self.params["market_displacement"] > 1:
            self.params["market_displacement"] = DEFAULT_MARKET_DISPLACEMENT
            print(f"Warning: Market displacement must be between 0 and 1. Reset to default value: {DEFAULT_MARKET_DISPLACEMENT}")

    def run(self) -> ModelResults:
        """
        Run the complete model and return results.
        
        This method uses a cached standalone function to perform calculations
        to avoid issues with caching methods that have 'self' parameters.
        
        Returns:
            Dictionary with model results and metrics
        """
        # Call the standalone cached function with parameters as explicit arguments
        results = run_model_calculations(
            chargers_per_year=self.params["chargers_per_year"],
            deployment_years=self.params["deployment_years"],
            deployment_delay=self.params["deployment_delay"],
            capex_per_charger=self.params["capex_per_charger"],
            opex_per_charger=self.params["opex_per_charger"],
            asset_life=self.params["asset_life"],
            wacc=self.params["wacc"],
            customer_base=self.params["customer_base"],
            third_party_revenue=self.params["third_party_revenue"],
            efficiency=self.params["efficiency"],
            efficiency_degradation=self.params["efficiency_degradation"],
            tech_obsolescence_rate=self.params["tech_obsolescence_rate"],
            market_displacement=self.params["market_displacement"]
        )
        
        # Store results in the instance
        self.results = results
        return results
    
    def _run_calculations(self) -> ModelResults:
        """
        Run the core model calculations without caching.
        This method should not be called directly - use run() instead.
        """
        years = list(range(1, DEFAULT_YEARS + 1))
        
        # Run calculations in sequence
        rollout_df = self._calculate_rollout(years)
        depreciation_df = self._calculate_depreciation(rollout_df, years)
        rab_df = self._calculate_rab(rollout_df, depreciation_df, years)
        revenue_df = self._calculate_revenue(rollout_df, rab_df, years)
        market_df = self._calculate_market_effects(rollout_df, years)
        summary = self._calculate_summary(rollout_df, rab_df, revenue_df)
        
        # Return results
        return {
            "rollout": rollout_df,
            "depreciation": depreciation_df,
            "rab": rab_df,
            "revenue": revenue_df,
            "market": market_df,
            "summary": summary
        }
    
    def _calculate_rollout(self, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """Calculate charger deployment schedule and capital expenditure."""
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Create DataFrame with years as index
        df = pd.DataFrame(index=years)
        
        # Determine deployment period (with optional delay factor)
        deployment_years = min(params["deployment_years"], len(years))
        if params.get("deployment_delay", DEFAULT_DEPLOYMENT_DELAY) > 1.0:
            deployment_years = min(len(years), int(deployment_years * params["deployment_delay"]))
        
        # Calculate chargers deployed annually (vectorised)
        total_chargers = params["chargers_per_year"] * params["deployment_years"]
        chargers_per_year = total_chargers / deployment_years
        
        # Initialize annual chargers column with zeros
        df["annual_chargers"] = 0
        
        # Set values for deployment years (vectorised)
        deployment_mask = df.index <= deployment_years
        df.loc[deployment_mask, "annual_chargers"] = chargers_per_year
        
        # Calculate cumulative chargers (vectorised)
        df["cumulative_chargers"] = df["annual_chargers"].cumsum()
        
        # Calculate capital expenditure (vectorised)
        df["unit_capex"] = params["capex_per_charger"]
        df["capex"] = df["annual_chargers"] * df["unit_capex"]
        
        return df
    
    def _calculate_depreciation(self, rollout_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate asset depreciation, adjusting for technological obsolescence.
        
        This function calculates the depreciation schedule for assets based on their 
        installation year and expected lifetime. It accounts for technological
        obsolescence by reducing the effective asset life.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize depreciation dataframe
        depreciation_df = pd.DataFrame(index=years, columns=["total_depreciation"], data=0.0)
        
        # Get parameters
        base_asset_life = params["asset_life"]
        obsolescence_rate = params.get("tech_obsolescence_rate", DEFAULT_TECH_OBSOLESCENCE_RATE)
        
        # Get non-zero deployment years for vectorization
        active_vintage_years = rollout_df[rollout_df["annual_chargers"] > 0].index
        
        if len(active_vintage_years) == 0:
            return depreciation_df
            
        # Pre-calculate obsolescence factors and asset lives for all vintage years at once
        if obsolescence_rate > 0:
            # Calculate obsolescence factors based on when assets were deployed
            # Earlier deployments have longer life reduction due to technology advances
            obsolescence_factors = 1 - obsolescence_rate * (1 - np.exp(-np.array(active_vintage_years) / DEFAULT_SATURATION_TIME_CONSTANT))
            asset_lives = np.maximum(1, base_asset_life * obsolescence_factors)
        else:
            asset_lives = np.full(len(active_vintage_years), base_asset_life)
            
        # Create a matrix for depreciation calculation
        # Rows represent vintage years, columns represent calendar years
        depreciation_matrix = np.zeros((len(active_vintage_years), len(years)))
        
        for i, vintage_year in enumerate(active_vintage_years):
            capex = rollout_df.loc[vintage_year, "capex"]
            asset_life = asset_lives[i]
            annual_depr = capex / asset_life
            
            # Calculate applicable years for this vintage
            start_idx = years.index(vintage_year)
            end_idx = min(start_idx + int(asset_life), len(years))
            
            # Add depreciation to the matrix for these years
            depreciation_matrix[i, start_idx:end_idx] = annual_depr
            
        # Sum depreciation across all vintages for each calendar year
        depreciation_df["total_depreciation"] = np.sum(depreciation_matrix, axis=0)
        
        return depreciation_df
    
    def _calculate_rab(self, rollout_df: pd.DataFrame, depreciation_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate Regulated Asset Base (RAB) evolution over time.
        
        The RAB is calculated by tracking the opening balance, adding new investments,
        subtracting depreciation and obsolescence writeoffs, and calculating the
        closing balance for each year. The average RAB is used for return calculations.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize RAB DataFrame 
        rab_df = pd.DataFrame(index=years)
        
        # Set initial columns (vectorised)
        rab_df["opening_rab"] = 0.0
        rab_df["additions"] = rollout_df["capex"]
        rab_df["depreciation"] = depreciation_df["total_depreciation"]
        rab_df["obsolescence_writeoff"] = 0.0
        rab_df["closing_rab"] = 0.0
        
        # Get obsolescence rate
        obsolescence_rate = params.get("tech_obsolescence_rate", DEFAULT_TECH_OBSOLESCENCE_RATE)
        
        # Calculate RAB evolution (still requires loop due to sequential nature)
        for i, year in enumerate(years):
            # Set opening RAB from previous closing RAB
            if i > 0:
                rab_df.loc[year, "opening_rab"] = rab_df.loc[years[i-1], "closing_rab"]
            
            # Calculate obsolescence writeoff (vectorised calculation)
            if obsolescence_rate > 0 and i > 0:
                opening_rab = rab_df.loc[year, "opening_rab"]
                rab_df.loc[year, "obsolescence_writeoff"] = opening_rab * obsolescence_rate * DEFAULT_OBSOLESCENCE_FACTOR
            
            # Calculate closing RAB (vectorised)
            rab_df.loc[year, "closing_rab"] = (
                rab_df.loc[year, "opening_rab"] + 
                rab_df.loc[year, "additions"] - 
                rab_df.loc[year, "depreciation"] -
                rab_df.loc[year, "obsolescence_writeoff"]
            )
        
        # Calculate average RAB (vectorised)
        rab_df["average_rab"] = (rab_df["opening_rab"] + rab_df["closing_rab"]) / 2
        
        return rab_df
    
    def _calculate_revenue(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate revenue requirements and customer bill impacts.
        
        Revenue requirements have three components:
        1. Operating expenses - based on cumulative chargers and efficiency factor
        2. Depreciation - from RAB calculations
        3. Return on capital - WACC applied to average RAB
        
        Bill impacts are calculated by dividing net revenue by the customer base.
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize revenue DataFrame
        revenue_df = pd.DataFrame(index=years)
        
        # Calculate efficiency factors (vectorised)
        base_efficiency = params.get("efficiency", DEFAULT_EFFICIENCY)
        degradation_rate = params.get("efficiency_degradation", DEFAULT_EFFICIENCY_DEGRADATION)
        years_array = np.array(years) - 1  # Convert to 0-based years
        revenue_df["efficiency_factor"] = base_efficiency * (1 + degradation_rate * years_array)
        
        # Calculate revenue components (all vectorised)
        # 1. Operating expenses
        revenue_df["opex"] = rollout_df["cumulative_chargers"] * params["opex_per_charger"] * revenue_df["efficiency_factor"]
        
        # 2. Depreciation
        revenue_df["depreciation"] = rab_df["depreciation"]
        
        # 3. Return on capital
        wacc = params["wacc"]
        revenue_df["wacc"] = wacc
        revenue_df["return_on_capital"] = rab_df["average_rab"] * wacc
        
        # Calculate total revenue (vectorised)
        revenue_df["total_revenue"] = (
            revenue_df["opex"] + 
            revenue_df["depreciation"] + 
            revenue_df["return_on_capital"]
        )
        
        # Calculate third-party revenue (vectorised)
        revenue_df["third_party_revenue"] = rollout_df["cumulative_chargers"] * params["third_party_revenue"]
        
        # Calculate bill impacts (vectorised)
        revenue_df["net_revenue"] = revenue_df["total_revenue"] - revenue_df["third_party_revenue"]
        revenue_df["bill_impact"] = revenue_df["net_revenue"] / params["customer_base"]
        revenue_df["cumulative_bill_impact"] = revenue_df["bill_impact"].cumsum()
        
        return revenue_df
    
    def _calculate_summary(self, rollout_df: pd.DataFrame, rab_df: pd.DataFrame, revenue_df: pd.DataFrame, params: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate key performance metrics for the model.
        
        This function computes various summary metrics including:
        - Net Present Value (NPV) calculations for revenue and bill impacts
        - Peak values and their corresponding years
        - Averages and totals for key metrics
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        years = rollout_df.index.tolist()
        
        # Calculate NPV metrics (vectorised)
        wacc = params["wacc"]
        discount_factors = 1 / (1 + wacc) ** np.array(years)
        npv_revenue = (revenue_df["total_revenue"] * discount_factors).sum()
        npv_bill_impact = (revenue_df["bill_impact"] * discount_factors).sum()
        
        # Identify peak values and years (vectorised operations)
        peak_rab = rab_df["closing_rab"].max()
        peak_rab_year = rab_df["closing_rab"].idxmax()
        peak_bill_impact = revenue_df["bill_impact"].max()
        peak_bill_year = revenue_df["bill_impact"].idxmax()
        
        # Return key metrics
        return {
            "total_chargers": float(rollout_df["cumulative_chargers"].iloc[-1]),
            "peak_rab": float(peak_rab),
            "peak_rab_year": int(peak_rab_year),
            "npv_revenue": float(npv_revenue),
            "npv_bill_impact": float(npv_bill_impact),
            "peak_bill_impact": float(peak_bill_impact),
            "peak_bill_year": int(peak_bill_year),
            "avg_bill_impact": float(revenue_df["bill_impact"].mean()),
            "total_bill_impact": float(revenue_df["bill_impact"].sum()),
            "total_revenue": float(revenue_df["total_revenue"].sum()),
            "total_opex": float(revenue_df["opex"].sum()),
            "final_efficiency_factor": float(revenue_df["efficiency_factor"].iloc[-1]),
        }
    
    def _calculate_market_effects(self, rollout_df: pd.DataFrame, years: List[int], params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Calculate private market effects of the regulated deployment.
        
        This function models how regulated asset deployment affects private market investment:
        1. Baseline private market is projected based on initial market and growth rate
        2. Market displacement effect is calculated based on time and displacement rate
        3. The actual private market is the baseline minus displacement
        4. Total charger deployment with and without RAB is calculated for comparison
        """
        # Use self.params if no parameters are provided
        if params is None:
            params = self.params
            
        # Initialize market DataFrame
        market_df = pd.DataFrame(index=years)
        
        # Perform all calculations with vectorised operations
        # 1. RAB deployment
        market_df["rab_chargers"] = rollout_df["cumulative_chargers"]
        
        # 2. Baseline private market (vectorised)
        years_zero_based = np.array(years) - 1
        market_df["baseline_private"] = DEFAULT_INITIAL_PRIVATE_CHARGERS * (1 + DEFAULT_PRIVATE_GROWTH_RATE) ** years_zero_based
        
        # 3. Calculate market displacement (vectorised)
        displacement_rate = params.get("market_displacement", DEFAULT_MARKET_DISPLACEMENT)
        saturation_factors = 1 - np.exp(-years_zero_based / DEFAULT_SATURATION_TIME_CONSTANT)
        
        market_df["displacement_factor"] = displacement_rate * saturation_factors
        market_df["displaced_private"] = market_df["baseline_private"] * market_df["displacement_factor"]
        market_df["actual_private"] = market_df["baseline_private"] - market_df["displaced_private"]
        
        # 4. Calculate total markets (vectorised)
        market_df["total_with_rab"] = market_df["rab_chargers"] + market_df["actual_private"]
        market_df["total_without_rab"] = market_df["baseline_private"]
        
        return market_df 