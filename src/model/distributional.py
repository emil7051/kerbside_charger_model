"""Income quintile impact analysis for the EV charger model."""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from ..data.defaults import INCOME_QUINTILES

def calculate_distributional_impact(
    revenue_df: pd.DataFrame,
    income_quintiles: Dict[str, Dict[str, Any]] = INCOME_QUINTILES
) -> pd.DataFrame:
    """
    Calculate the distributional impact across income quintiles.
    
    Args:
        revenue_df: Revenue requirements DataFrame from the base model
        income_quintiles: Dictionary of income quintile data
        
    Returns:
        DataFrame with impact metrics for each quintile
    """
    # Extract bill impact
    annual_bill_impacts = revenue_df["per_customer_impact"].values
    avg_annual_impact = np.mean(annual_bill_impacts)
    
    # Calculate impact for each income quintile
    results = []
    
    for quintile, data in income_quintiles.items():
        annual_income = data["income"]
        electricity_spend = data["electricity_spend"]
        
        # Calculate impacts
        impact_pct_income = (avg_annual_impact / annual_income) * 100
        impact_pct_bill = (avg_annual_impact / electricity_spend) * 100
        
        results.append({
            "quintile": quintile,
            "annual_income": annual_income,
            "electricity_spend": electricity_spend,
            "bill_impact": avg_annual_impact,
            "impact_pct_income": impact_pct_income,
            "impact_pct_bill": impact_pct_bill,
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Calculate regressivity metrics
    lowest_quintile = df[df["quintile"] == "Q1"].iloc[0]
    highest_quintile = df[df["quintile"] == "Q5"].iloc[0]
    
    regressivity_ratio_income = (
        lowest_quintile["impact_pct_income"] / highest_quintile["impact_pct_income"]
        if highest_quintile["impact_pct_income"] > 0 else float('inf')
    )
    
    regressivity_ratio_bill = (
        lowest_quintile["impact_pct_bill"] / highest_quintile["impact_pct_bill"]
        if highest_quintile["impact_pct_bill"] > 0 else float('inf')
    )
    
    # Add regressivity metrics to each row for easy access
    df["regressivity_ratio_income"] = regressivity_ratio_income
    df["regressivity_ratio_bill"] = regressivity_ratio_bill
    
    return df

def calculate_lifetime_distributional_impact(
    revenue_df: pd.DataFrame,
    income_quintiles: Dict[str, Dict[str, Any]] = INCOME_QUINTILES,
    income_growth_rate: float = 0.02  # Annual income growth rate
) -> pd.DataFrame:
    """
    Calculate the distributional impact over the entire model timeframe.
    
    Args:
        revenue_df: Revenue requirements DataFrame from the base model
        income_quintiles: Dictionary of income quintile data
        income_growth_rate: Annual rate of income growth
        
    Returns:
        DataFrame with lifecycle impact metrics for each quintile
    """
    years = revenue_df.index.tolist()
    results_by_year = []
    
    # Calculate impact for each year
    for year in years:
        year_impact = revenue_df.loc[year, "per_customer_impact"]
        
        for quintile, data in income_quintiles.items():
            # Apply income growth
            annual_income = data["income"] * (1 + income_growth_rate) ** year
            # Electricity spend grows at a slower rate than income
            electricity_spend = data["electricity_spend"] * (1 + income_growth_rate * 0.8) ** year
            
            # Calculate impacts
            impact_pct_income = (year_impact / annual_income) * 100
            impact_pct_bill = (year_impact / electricity_spend) * 100
            
            results_by_year.append({
                "year": year,
                "quintile": quintile,
                "annual_income": annual_income,
                "electricity_spend": electricity_spend,
                "bill_impact": year_impact,
                "impact_pct_income": impact_pct_income,
                "impact_pct_bill": impact_pct_bill,
            })
    
    # Convert to DataFrame
    df_by_year = pd.DataFrame(results_by_year)
    
    # Calculate summary metrics by quintile
    summary = []
    
    for quintile in income_quintiles.keys():
        quintile_data = df_by_year[df_by_year["quintile"] == quintile]
        
        # Sum impacts across years
        total_bill_impact = quintile_data["bill_impact"].sum()
        
        # Calculate average metrics
        avg_impact_pct_income = quintile_data["impact_pct_income"].mean()
        avg_impact_pct_bill = quintile_data["impact_pct_bill"].mean()
        
        # Calculate peak impacts
        peak_impact_pct_income = quintile_data["impact_pct_income"].max()
        peak_impact_pct_bill = quintile_data["impact_pct_bill"].max()
        
        summary.append({
            "quintile": quintile,
            "total_bill_impact": total_bill_impact,
            "avg_impact_pct_income": avg_impact_pct_income,
            "avg_impact_pct_bill": avg_impact_pct_bill,
            "peak_impact_pct_income": peak_impact_pct_income,
            "peak_impact_pct_bill": peak_impact_pct_bill,
        })
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary)
    
    # Calculate regressivity metrics
    lowest_quintile = summary_df[summary_df["quintile"] == "Q1"].iloc[0]
    highest_quintile = summary_df[summary_df["quintile"] == "Q5"].iloc[0]
    
    regressivity_ratio_income = (
        lowest_quintile["avg_impact_pct_income"] / highest_quintile["avg_impact_pct_income"]
        if highest_quintile["avg_impact_pct_income"] > 0 else float('inf')
    )
    
    # Add regressivity metrics to the summary DataFrame
    summary_df["regressivity_ratio_income"] = regressivity_ratio_income
    
    return summary_df, df_by_year 