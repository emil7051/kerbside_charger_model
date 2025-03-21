"""Base model for Regulated Asset Base (RAB) EV charger deployment analysis."""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd

def calculate_wacc(year: int, params: Dict[str, Any]) -> float:
    """Calculate the Weighted Average Cost of Capital for a given year."""
    if year < 5:
        return params["WACC1to5"]
    elif year < 10:
        return params["WACC6to10"]
    else:
        return params["WACC11to15"]

def calculate_npv(
    cash_flows: List[float],
    wacc: float,
    initial_investment: float = 0
) -> float:
    """Calculate Net Present Value."""
    years = np.arange(len(cash_flows))
    discount_factors = 1 / (1 + wacc) ** years
    return -initial_investment + np.sum(np.array(cash_flows) * discount_factors)

def calculate_irr(cash_flows: List[float]) -> float:
    """Calculate Internal Rate of Return."""
    try:
        # Manual IRR calculation using numeric method
        def npv_equation(rate, cash_flow_array):
            return np.sum(cash_flow_array / ((1 + rate) ** np.arange(len(cash_flow_array))))
        
        cash_flow_array = np.array(cash_flows)
        
        # Check if IRR calculation makes sense (cash flows must change sign)
        if np.all(cash_flow_array >= 0) or np.all(cash_flow_array <= 0):
            return float('nan')
        
        from scipy import optimize
        result = optimize.newton(lambda r: npv_equation(r, cash_flow_array), x0=0.1, maxiter=1000, tol=1e-6)
        return float(result)
    except (ValueError, RuntimeError):
        return float('nan')

def run_ev_charger_model(params: Dict[str, Any]) -> Tuple:
    """
    Runs the EV Charger RAB model.
    
    Parameters:
        params (dict): Model parameters
    
    Returns:
        tuple: (
            rollout_df,           # Charger deployment schedule
            depreciation_df,      # Asset depreciation schedule
            rab_df,               # Regulated Asset Base evolution
            revenue_df,           # Revenue requirements
            summary_stats,        # Summary statistics
            distributional_df,    # Distributional impact data
            competitiveness_df    # Market competition data
        )
    """
    # Set up time horizon
    years = list(range(15))  # 15-year analysis period
    
    # 1. Calculate charger rollout schedule
    rollout_df = calculate_rollout_schedule(years, params)
    
    # 2. Calculate asset depreciation
    depreciation_df = calculate_depreciation_schedule(rollout_df, params)
    
    # 3. Calculate Regulated Asset Base evolution
    rab_df = calculate_rab_evolution(rollout_df, depreciation_df, params)
    
    # 4. Calculate revenue requirements
    revenue_df = calculate_revenue_requirements(rab_df, rollout_df, params)
    
    # 5. Calculate summary statistics
    summary_stats = calculate_summary_statistics(rollout_df, rab_df, revenue_df, params)
    
    # Return minimal data if the other components aren't needed
    if "skip_ext_calcs" in params and params["skip_ext_calcs"]:
        # Return empty dataframes for the other components
        distributional_df = pd.DataFrame()
        competitiveness_df = pd.DataFrame()
        return (rollout_df, depreciation_df, rab_df, revenue_df, summary_stats, 
                distributional_df, competitiveness_df)
    
    # These will be implemented in their respective modules
    # Placeholder for now
    distributional_df = pd.DataFrame()
    competitiveness_df = pd.DataFrame()
    
    return (rollout_df, depreciation_df, rab_df, revenue_df, summary_stats, 
            distributional_df, competitiveness_df)

def calculate_rollout_schedule(years: List[int], params: Dict[str, Any]) -> pd.DataFrame:
    """Calculate the charger rollout schedule."""
    df = pd.DataFrame(index=years)
    
    # Basic charger deployment (5 years)
    df["annual_chargers"] = 0
    deployment_years = min(5, len(years))
    
    for year in years[:deployment_years]:
        # Apply deployment delay if specified
        delay_factor = params.get("DeploymentDelay", 1.0)
        df.loc[year, "annual_chargers"] = params["ChargersPerYear"] / delay_factor
    
    # Cumulative chargers
    df["cumulative_chargers"] = df["annual_chargers"].cumsum()
    
    # Capital expenditure
    df["capex"] = df["annual_chargers"] * params["CapExPerCharger"]
    
    # Apply cost escalation if specified
    if "CostEscalation" in params and params["CostEscalation"] != 1.0:
        df["capex"] = df["capex"] * params["CostEscalation"]
    
    return df

def calculate_depreciation_schedule(rollout_df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Calculate the asset depreciation schedule."""
    years = rollout_df.index.tolist()
    asset_life = params["AssetLife"]
    
    # Create a matrix for tracking depreciation
    # Each row is a year, each column is a vintage of assets
    depreciation_matrix = np.zeros((len(years), len(years)))
    
    for vintage_year in years:
        capex = rollout_df.loc[vintage_year, "capex"]
        if capex == 0:
            continue
            
        # Calculate straight-line depreciation for this vintage
        annual_depreciation = capex / asset_life
        
        # Apply depreciation to future years, up to asset life
        for future_year in range(vintage_year, min(vintage_year + asset_life, len(years))):
            depreciation_matrix[future_year, vintage_year] = annual_depreciation
    
    # Convert to DataFrame
    depreciation_df = pd.DataFrame(
        depreciation_matrix, 
        index=years, 
        columns=[f"vintage_{year}" for year in years]
    )
    
    # Add total annual depreciation
    depreciation_df["total_depreciation"] = depreciation_df.sum(axis=1)
    
    return depreciation_df

def calculate_rab_evolution(
    rollout_df: pd.DataFrame, 
    depreciation_df: pd.DataFrame, 
    params: Dict[str, Any]
) -> pd.DataFrame:
    """Calculate the Regulated Asset Base evolution."""
    years = rollout_df.index.tolist()
    
    rab_df = pd.DataFrame(index=years)
    rab_df["opening_rab"] = 0
    rab_df["capex"] = rollout_df["capex"]
    rab_df["depreciation"] = depreciation_df["total_depreciation"]
    
    # Calculate closing RAB for each year
    for year in years:
        if year == 0:
            rab_df.loc[year, "opening_rab"] = 0
        else:
            rab_df.loc[year, "opening_rab"] = rab_df.loc[year-1, "closing_rab"]
        
        rab_df.loc[year, "closing_rab"] = (
            rab_df.loc[year, "opening_rab"] + 
            rab_df.loc[year, "capex"] - 
            rab_df.loc[year, "depreciation"]
        )
    
    # Calculate average RAB for return calculation
    rab_df["average_rab"] = (rab_df["opening_rab"] + rab_df["closing_rab"]) / 2
    
    return rab_df

def calculate_revenue_requirements(
    rab_df: pd.DataFrame, 
    rollout_df: pd.DataFrame, 
    params: Dict[str, Any]
) -> pd.DataFrame:
    """Calculate revenue requirements."""
    years = rab_df.index.tolist()
    
    revenue_df = pd.DataFrame(index=years)
    revenue_df["opex"] = rollout_df["cumulative_chargers"] * params["OpExPerCharger"]
    
    # Apply operational efficiency if specified
    if "OperationalEfficiency" in params and params["OperationalEfficiency"] != 1.0:
        revenue_df["opex"] = revenue_df["opex"] / params["OperationalEfficiency"]
    
    revenue_df["depreciation"] = rab_df["depreciation"]
    
    # Calculate return on capital
    revenue_df["return_on_capital"] = 0
    for year in years:
        wacc = calculate_wacc(year, params)
        revenue_df.loc[year, "return_on_capital"] = rab_df.loc[year, "average_rab"] * wacc
    
    # Calculate total revenue requirement
    revenue_df["total_revenue_requirement"] = (
        revenue_df["opex"] + 
        revenue_df["depreciation"] + 
        revenue_df["return_on_capital"]
    )
    
    # Calculate third party revenue
    revenue_df["third_party_revenue"] = rollout_df["cumulative_chargers"] * params["ThirdPartyRevenue"]
    
    # Calculate shared asset offset if applicable
    if "SharedAssetOffset" in params and params["SharedAssetOffset"] > 0:
        revenue_df["shared_asset_offset"] = rollout_df["cumulative_chargers"] * params["SharedAssetOffset"]
    else:
        revenue_df["shared_asset_offset"] = 0
    
    # Calculate net revenue requirement from customers
    revenue_df["net_revenue_requirement"] = (
        revenue_df["total_revenue_requirement"] - 
        revenue_df["third_party_revenue"] - 
        revenue_df["shared_asset_offset"]
    )
    
    # Calculate impact per customer
    revenue_df["per_customer_impact"] = revenue_df["net_revenue_requirement"] / params["CustomerBase"]
    
    return revenue_df

def calculate_summary_statistics(
    rollout_df: pd.DataFrame, 
    rab_df: pd.DataFrame, 
    revenue_df: pd.DataFrame, 
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate summary statistics."""
    years = rollout_df.index.tolist()
    
    # Calculate NPV of revenue requirement
    npv_values = []
    for year in years:
        npv_values.append(revenue_df.loc[year, "total_revenue_requirement"])
    
    # Use WACC for 1-5 years as discount rate for NPV
    discount_rate = params["WACC1to5"]
    npv = calculate_npv(npv_values, discount_rate)
    
    # Calculate total bill impact
    total_bill_impact = revenue_df["per_customer_impact"].sum()
    avg_annual_bill_impact = total_bill_impact / len(years)
    
    # Calculate peak RAB
    peak_rab = rab_df["average_rab"].max()
    
    # Peak annual bill impact
    peak_bill_impact = revenue_df["per_customer_impact"].max()
    
    # Total chargers deployed
    total_chargers = rollout_df["cumulative_chargers"].max()
    
    # Cost per charger (including return)
    total_revenue = revenue_df["total_revenue_requirement"].sum()
    cost_per_charger = total_revenue / total_chargers if total_chargers > 0 else 0
    
    return {
        "Total Chargers": int(total_chargers),
        "NPV of Revenue Requirement": float(npv),
        "Cumulative Bill Impact/Customer": float(total_bill_impact),
        "Average Annual Bill Impact": float(avg_annual_bill_impact),
        "Peak RAB": float(peak_rab),
        "Peak Annual Bill Impact": float(peak_bill_impact),
        "Cost per Charger": float(cost_per_charger),
    } 