import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.stats as stats

# Set a professional style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['figure.dpi'] = 100

# ========================
# 1. Model Parameters
# ========================

# Default parameters that replicate the Inputs sheet from the Excel model.
default_params = {
    "ChargersPerYear": 5000,
    "CapExPerCharger": 6000,
    "OpExPerCharger": 500,
    "AssetLife": 8,
    "WACC1to5": 0.058,     # Post-tax Weighted Average Cost of Capital for Years 1-5
    "WACC6to10": 0.06,     # For Years 6-10
    "WACC11to15": 0.055,   # For Years 11-15
    "CustomerBase": 1800000,
    "ThirdPartyRevenue": 100,
    "SharedAssetOffset": 0,
    # New parameters
    "EfficiencyFactor": 1.0,  # Default is no inefficiency premium
    "EfficiencyDegradation": 0.0,  # Annual degradation in efficiency
    "DeploymentDelay": 1.0,  # Deployment time multiplier (1.0 = no delay)
    "CostEscalation": 1.0,  # Cost escalation factor (1.0 = no escalation)
    "OperationalEfficiency": 1.0,  # How efficiently chargers are operated (1.0 = fully efficient)
    "PrivateMarketDisplacement": 0.0,  # Percentage of private market displaced
    "InnovationRate": 0.02,  # Annual innovation rate in competitive market
    "MonopolyInnovationRate": 0.01,  # Annual innovation rate in monopoly market
    # New enhanced parameters for better financial credibility
    "TechObsolescenceRate": 0.05,  # Technology obsolescence rate (% of assets becoming obsolete per year)
    "DemandUtilization": 0.7,  # Average utilization of chargers (1.0 = full utilization)
    "UtilizationGrowthRate": 0.05,  # Annual growth in utilization as EV adoption increases
    "UseRiskPremium": True,  # Whether to apply risk premium to WACC for uncertain technology
    "RiskPremium": 0.01,  # Additional risk premium for WACC for new technology investments
    "CostDeclineRate": 0.03,  # Annual decline in CapEx costs due to technology improvements
    "EVAdoptionRate": 0.15,  # Annual growth rate of EV adoption
    "EnvironmentalBenefitPerCharger": 250,  # Annual environmental benefit ($) per charger
    "IncludeEnvironmentalBenefits": False,  # Whether to include environmental benefits in analysis
    "PublicPrivateRatio": 0.5,  # Optimal ratio of public to private chargers
}

# High-Plus scenario overrides (worse-case assumptions)
high_plus_params = {
    "CapExPerCharger": 9000,
    "OpExPerCharger": 750,
    "WACC1to5": 0.0585,
    "EfficiencyFactor": 1.2,
    "EfficiencyDegradation": 0.03,
    "DeploymentDelay": 1.3,
    "CostEscalation": 1.2,
    "OperationalEfficiency": 0.8,
}

# Income quintiles for distributional analysis
income_quintiles = {
    "Q1": {"income": 25000, "electricity_spend": 1900, "pct_of_customers": 0.2, "ev_ownership_rate": 0.03},
    "Q2": {"income": 45000, "electricity_spend": 2100, "pct_of_customers": 0.2, "ev_ownership_rate": 0.05},
    "Q3": {"income": 65000, "electricity_spend": 2300, "pct_of_customers": 0.2, "ev_ownership_rate": 0.08},
    "Q4": {"income": 95000, "electricity_spend": 2500, "pct_of_customers": 0.2, "ev_ownership_rate": 0.12},
    "Q5": {"income": 150000, "electricity_spend": 2900, "pct_of_customers": 0.2, "ev_ownership_rate": 0.20}
}

# Monte Carlo simulation distributions
mc_distributions = {
    "CapExPerCharger": {"type": "triangular", "min": 4500, "mode": 6000, "max": 9000},
    "OpExPerCharger": {"type": "triangular", "min": 350, "mode": 500, "max": 750},
    "AssetLife": {"type": "discrete", "values": [5, 6, 7, 8, 9], "probs": [0.1, 0.2, 0.3, 0.3, 0.1]},
    "WACC1to5": {"type": "normal", "mean": 0.058, "std": 0.005},
    "EfficiencyFactor": {"type": "triangular", "min": 1.0, "mode": 1.1, "max": 1.4},
    "DeploymentDelay": {"type": "triangular", "min": 1.0, "mode": 1.2, "max": 1.5}
}

# ========================
# 2. Helper Functions for Monte Carlo and Enhanced Analysis
# ========================

def generate_monte_carlo_params(n_simulations=1000):
    """Generate parameter sets for Monte Carlo simulation"""
    param_sets = []
    
    for _ in range(n_simulations):
        params = default_params.copy()
        
        # Generate random values for each parameter based on its distribution
        for param, dist in mc_distributions.items():
            if dist["type"] == "triangular":
                params[param] = stats.triang.rvs(
                    c=(dist["mode"] - dist["min"]) / (dist["max"] - dist["min"]),
                    loc=dist["min"],
                    scale=(dist["max"] - dist["min"])
                )
            elif dist["type"] == "normal":
                params[param] = stats.norm.rvs(
                    loc=dist["mean"], 
                    scale=dist["std"]
                )
            elif dist["type"] == "discrete":
                params[param] = np.random.choice(
                    dist["values"], 
                    p=dist["probs"]
                )
        
        param_sets.append(params)
    
    return param_sets

def calculate_competitive_market(years, chargers_per_year, innovation_rate):
    """Model competitive market outcomes"""
    
    # Initialize outputs
    private_market_chargers = []
    competitive_capex = []
    competitive_opex = []
    cumulative_chargers = 0
    
    # Initial values
    capex = default_params["CapExPerCharger"]
    opex = default_params["OpExPerCharger"]
    
    for y in range(1, years+1):
        # More aggressive private deployment due to competition
        if y <= 6:
            # During deployment years, competitive market deploys 80% of RAB model
            chargers = int(chargers_per_year * 0.8)
        else:
            # After initial deployment, competitive market continues growing
            chargers = int(max(0, chargers_per_year * 0.5 * (1 - (y-6)/10)))
        
        cumulative_chargers += chargers
        private_market_chargers.append(chargers)
        
        # Competitive market drives down costs each year
        capex = capex * (1 - innovation_rate)
        opex = opex * (1 - innovation_rate * 0.5)  # OpEx improves but more slowly
        
        competitive_capex.append(capex)
        competitive_opex.append(opex)
    
    return {
        "years": list(range(1, years+1)),
        "chargers": private_market_chargers,
        "cumulative_chargers": np.cumsum(private_market_chargers),
        "capex": competitive_capex,
        "opex": competitive_opex
    }

def calculate_private_market_displacement(rab_chargers, private_market_displacement_rate):
    """Calculate private market displacement due to RAB model"""
    
    # Calculate how many private market chargers would be installed without RAB
    baseline_private = np.array([0, 1500, 3500, 6000, 9000, 12000, 15000, 17000, 18500, 19500, 
                                20500, 21500, 22500, 23000, 23500])
    
    # Calculate displacement based on RAB deployment
    displacement_factor = private_market_displacement_rate * np.cumsum(rab_chargers) / 30000
    displacement_factor = np.minimum(displacement_factor, 0.8)  # Cap at 80% displacement
    
    # Calculate actual private market deployment with RAB
    actual_private = baseline_private * (1 - displacement_factor)
    
    return {
        "baseline_private": baseline_private,
        "actual_private": actual_private,
        "displaced_chargers": baseline_private - actual_private
    }

def calculate_distributional_impacts(bill_impact, income_quintiles):
    """Calculate distributional impacts across income quintiles"""
    
    results = []
    
    for quintile, data in income_quintiles.items():
        annual_income = data["income"]
        electricity_spend = data["electricity_spend"]
        
        # Calculate impacts
        impact_pct_income = (bill_impact / annual_income) * 100
        impact_pct_bill = (bill_impact / electricity_spend) * 100
        
        results.append({
            "quintile": quintile,
            "annual_income": annual_income,
            "electricity_spend": electricity_spend,
            "bill_impact": bill_impact,
            "impact_pct_income": impact_pct_income,
            "impact_pct_bill": impact_pct_bill
        })
    
    return pd.DataFrame(results)

def calculate_tech_obsolescence(years, asset_life, tech_obsolescence_rate):
    """
    Models technological obsolescence of EV chargers over time.
    
    Parameters:
        years (int): Number of years to model
        asset_life (int): Original expected asset life
        tech_obsolescence_rate (float): Annual rate of technological obsolescence
        
    Returns:
        dict: Technological obsolescence factors by year
    """
    # Initialize outputs
    tech_obsolescence = {}
    
    for y in range(1, years+1):
        # Calculate cumulative obsolescence based on technology change
        # This accelerates as technology improves
        cumulative_obsolescence = 1 - (1 - tech_obsolescence_rate) ** y
        
        # Cap maximum obsolescence at 80%
        cumulative_obsolescence = min(cumulative_obsolescence, 0.8)
        
        # Calculate effective asset life reduction
        effective_asset_life = asset_life * (1 - cumulative_obsolescence)
        
        # Store values
        tech_obsolescence[y] = {
            "cumulative_obsolescence": cumulative_obsolescence,
            "effective_asset_life": effective_asset_life
        }
    
    return tech_obsolescence

def calculate_demand_utilization(years, initial_utilization, utilization_growth_rate, ev_adoption_rate):
    """
    Models the utilization of EV chargers based on EV adoption and charging patterns.
    
    Parameters:
        years (int): Number of years to model
        initial_utilization (float): Initial utilization rate of chargers
        utilization_growth_rate (float): Annual growth in utilization
        ev_adoption_rate (float): Annual EV adoption growth rate
        
    Returns:
        dict: Utilization factors and EV adoption by year
    """
    # Initialize outputs
    utilization = {}
    ev_adoption = 0.02  # Starting EV adoption (2%)
    
    for y in range(1, years+1):
        # EV adoption follows S-curve growth
        if y <= 5:
            # Early growth phase
            ev_adoption *= (1 + ev_adoption_rate)
        elif y <= 10:
            # Accelerated growth phase
            ev_adoption *= (1 + ev_adoption_rate * 1.2)
        else:
            # Saturation phase
            ev_adoption = min(ev_adoption * (1 + ev_adoption_rate * 0.8), 0.95)
        
        # Utilization increases with EV adoption but with diminishing returns
        current_utilization = min(
            initial_utilization * (1 + utilization_growth_rate) ** (y-1),
            0.9  # Cap at 90% utilization
        )
        
        # Store values
        utilization[y] = {
            "ev_adoption": ev_adoption,
            "charger_utilization": current_utilization,
            "effective_revenue_factor": current_utilization / initial_utilization
        }
    
    return utilization

def calculate_environmental_benefits(years, chargers_per_year, benefit_per_charger, deployment_years):
    """
    Calculates environmental benefits from EV charger deployment.
    
    Parameters:
        years (int): Number of years to model
        chargers_per_year (int): Chargers installed per year
        benefit_per_charger (float): Environmental benefit per charger
        deployment_years (int): Number of years over which chargers are deployed
        
    Returns:
        dict: Environmental benefits by year
    """
    # Initialize outputs
    benefits = {}
    cumulative_chargers = 0
    
    for y in range(1, years+1):
        # Calculate new chargers installed this year
        new_chargers = chargers_per_year if y <= deployment_years else 0
        cumulative_chargers += new_chargers
        
        # Calculate environmental benefits
        # Benefits grow over time as more EVs are adopted
        annual_benefit_per_charger = benefit_per_charger * (1 + 0.03 * (y-1))
        total_annual_benefit = cumulative_chargers * annual_benefit_per_charger
        
        # Store values
        benefits[y] = {
            "cumulative_chargers": cumulative_chargers,
            "annual_benefit_per_charger": annual_benefit_per_charger,
            "total_annual_benefit": total_annual_benefit
        }
    
    return benefits

def calculate_optimal_charger_mix(years, public_chargers, private_market_chargers, optimal_ratio):
    """
    Analyzes whether the mix of public and private chargers is optimal.
    
    Parameters:
        years (int): Number of years to model
        public_chargers (list): Cumulative public chargers by year
        private_market_chargers (list): Cumulative private chargers by year
        optimal_ratio (float): Optimal ratio of public to private chargers
        
    Returns:
        dict: Analysis of charger mix optimality
    """
    # Initialize outputs
    optimality = {}
    
    for y in range(1, years+1):
        idx = y - 1  # Convert to 0-based index
        
        # Get current charger counts
        public = public_chargers[idx] if idx < len(public_chargers) else public_chargers[-1]
        private = private_market_chargers[idx] if idx < len(private_market_chargers) else private_market_chargers[-1]
        
        # Avoid division by zero
        if private == 0:
            private = 1
            
        # Calculate actual ratio
        actual_ratio = public / private
        
        # Calculate optimality (1.0 = perfect, lower is suboptimal)
        if actual_ratio > optimal_ratio:
            # Too many public chargers
            optimality_score = optimal_ratio / actual_ratio
            imbalance = "Too many public chargers"
        else:
            # Too many private chargers or optimal
            optimality_score = actual_ratio / optimal_ratio
            imbalance = "Too many private chargers" if optimality_score < 0.9 else "Near optimal"
        
        # Store values
        optimality[y] = {
            "public_chargers": public,
            "private_chargers": private,
            "actual_ratio": actual_ratio,
            "optimal_ratio": optimal_ratio,
            "optimality_score": optimality_score,
            "imbalance": imbalance
        }
    
    return optimality

# ========================
# 3. Enhanced Model Calculation Functions
# ========================
def run_ev_charger_model(params):
    """
    Runs the enhanced EV Charger Regulatory Asset Base (RAB) model with all improvements.
    
    Parameters:
      params (dict): Dictionary of model parameters.
      
    Returns:
      rollout_df (DataFrame): Yearly rollout details.
      depreciation_df (DataFrame): Depreciation amounts per year.
      rab_df (DataFrame): RAB roll-forward details.
      revenue_df (DataFrame): Revenue and bill impact details.
      summary_stats (dict): Key summary metrics.
      distributional_df (DataFrame): Distributional impacts analysis.
      competitiveness_df (DataFrame): Competitiveness analysis.
    """
    # Ensure all required parameters exist
    required_params = ["ChargersPerYear", "CapExPerCharger", "OpExPerCharger", "AssetLife", 
                     "WACC1to5", "WACC6to10", "WACC11to15", "CustomerBase", 
                     "ThirdPartyRevenue", "SharedAssetOffset", "EfficiencyFactor", 
                     "EfficiencyDegradation", "DeploymentDelay", "CostEscalation", 
                     "OperationalEfficiency", "PrivateMarketDisplacement", 
                     "InnovationRate", "MonopolyInnovationRate"]
    
    for param in required_params:
        if param not in params:
            params[param] = default_params.get(param, 0)
    
    # Calculate technological obsolescence, if enabled
    tech_obsolescence = calculate_tech_obsolescence(
        years=15, 
        asset_life=params.get("AssetLife", default_params["AssetLife"]),
        tech_obsolescence_rate=params.get("TechObsolescenceRate", default_params["TechObsolescenceRate"])
    )
    
    # Calculate demand utilization
    demand_utilization = calculate_demand_utilization(
        years=15,
        initial_utilization=params.get("DemandUtilization", default_params["DemandUtilization"]),
        utilization_growth_rate=params.get("UtilizationGrowthRate", default_params["UtilizationGrowthRate"]),
        ev_adoption_rate=params.get("EVAdoptionRate", default_params["EVAdoptionRate"])
    )
    
    # A) Build Rollout (Years 1 to 15) with technology cost decline
    years = range(1, 16)
    
    # Apply deployment delay to extend deployment period if delay > 1.0
    deployment_years = min(15, int(6 * params["DeploymentDelay"]))
    deployment_years = max(1, deployment_years)  # Ensure at least 1 deployment year
    adj_chargers_per_year = int(params["ChargersPerYear"] * 6 / deployment_years)

    rollout_data = []
    cumulative = 0
    
    # Get cost decline rate or use default
    cost_decline_rate = params.get("CostDeclineRate", default_params["CostDeclineRate"])
    
    for y in years:
        chargers_installed = adj_chargers_per_year if y <= deployment_years else 0
        
        # Apply cost escalation to CapEx, but also factor in technology cost declines
        adjusted_capex = params["CapExPerCharger"] * params["CostEscalation"] * ((1 - cost_decline_rate) ** (y-1))
        
        capex = chargers_installed * adjusted_capex
        cumulative += chargers_installed
        rollout_data.append([y, chargers_installed, capex, cumulative, adjusted_capex])
        
    rollout_df = pd.DataFrame(rollout_data, columns=["Year", "ChargersInstalled", "CapEx", "CumulativeChargers", "UnitCapEx"])

    # Calculate environmental benefits if enabled
    if params.get("IncludeEnvironmentalBenefits", default_params["IncludeEnvironmentalBenefits"]):
        env_benefits = calculate_environmental_benefits(
            years=15,
            chargers_per_year=adj_chargers_per_year,
            benefit_per_charger=params.get("EnvironmentalBenefitPerCharger", default_params["EnvironmentalBenefitPerCharger"]),
            deployment_years=deployment_years
        )
    else:
        # Create zero benefits if not enabled
        env_benefits = {y: {"total_annual_benefit": 0} for y in years}

    # B) Depreciation Matrix using Straight-line Depreciation with technological obsolescence
    depreciation_dict = {y: 0 for y in years}
    for cohort in range(1, deployment_years + 1):
        try:
            cohort_capex = rollout_df.loc[rollout_df["Year"] == cohort, "CapEx"].values[0]
            
            # Apply technological obsolescence to asset life
            if params.get("TechObsolescenceRate", 0) > 0:
                # Use effective asset life based on obsolescence
                effective_asset_life = max(1, tech_obsolescence[cohort]["effective_asset_life"])
            else:
                # Use standard asset life
                effective_asset_life = max(1, params["AssetLife"])
            
            # Depreciate the cost evenly over effective asset life years
            for y in range(cohort, cohort + int(effective_asset_life)):
                if y in depreciation_dict:
                    depreciation_dict[y] += cohort_capex / effective_asset_life
        except Exception as e:
            print(f"Error in depreciation calculation for cohort {cohort}: {str(e)}")
            continue
            
    depreciation_data = [[y, depreciation_dict[y]] for y in years]
    depreciation_df = pd.DataFrame(depreciation_data, columns=["Year", "TotalDepreciation"])

    # C) RAB Roll-forward with accelerated depreciation due to technological obsolescence
    rab_data = []
    opening_rab = 0
    for y in years:
        try:
            additions = rollout_df.loc[rollout_df["Year"] == y, "CapEx"].values[0]
            depr = depreciation_df.loc[depreciation_df["Year"] == y, "TotalDepreciation"].values[0]
            
            # Apply any additional write-offs due to technological obsolescence
            # This represents assets that become completely obsolete
            if params.get("TechObsolescenceRate", 0) > 0 and y > 1:
                obsolescence_writeoff = opening_rab * params.get("TechObsolescenceRate", 0) * 0.1
            else:
                obsolescence_writeoff = 0
                
            # Total reduction in RAB
            total_reduction = depr + obsolescence_writeoff
            
            # Calculate closing RAB
            closing = opening_rab + additions - total_reduction
            
            rab_data.append([
                y, opening_rab, additions, depr, 
                obsolescence_writeoff, total_reduction, closing
            ])
            
            opening_rab = closing
        except Exception as e:
            print(f"Error in RAB calculation for year {y}: {str(e)}")
            # Use reasonable fallback values
            additions = 0
            depr = 0
            obsolescence_writeoff = 0
            total_reduction = 0
            closing = opening_rab
            
            rab_data.append([
                y, opening_rab, additions, depr, 
                obsolescence_writeoff, total_reduction, closing
            ])
            
            opening_rab = closing
            
    rab_df = pd.DataFrame(rab_data, columns=[
        "Year", "OpeningRAB", "Additions", "Depreciation", 
        "ObsolescenceWriteoff", "TotalRABReduction", "ClosingRAB"
    ])

    # D) Revenue & Bill Impact Calculations with efficiency factors
    rev_data = []
    for y in years:
        try:
            # Average RAB in year y (average of opening and closing RAB)
            row_rab = rab_df.loc[rab_df["Year"] == y]
            avg_rab = (row_rab["OpeningRAB"].values[0] + row_rab["ClosingRAB"].values[0]) / 2

            # Use WACC based on the year (reflecting regulatory periods)
            if y <= 5:
                wacc = params["WACC1to5"]
            elif y <= 10:
                wacc = params["WACC6to10"]
            else:
                wacc = params["WACC11to15"]
                
            # Apply risk premium to WACC if enabled
            if params.get("UseRiskPremium", default_params["UseRiskPremium"]):
                risk_premium = params.get("RiskPremium", default_params["RiskPremium"])
                # Risk premium decreases over time as technology matures
                adjusted_risk_premium = risk_premium * (1 - 0.05 * (y-1))
                adjusted_risk_premium = max(0, adjusted_risk_premium)  # Ensure non-negative
                wacc += adjusted_risk_premium

            return_on_cap = avg_rab * wacc
            cum_chargers = rollout_df.loc[rollout_df["Year"] == y, "CumulativeChargers"].values[0]
            
            # Apply efficiency factor with annual degradation
            current_efficiency_factor = params["EfficiencyFactor"] * (1 + params["EfficiencyDegradation"] * (y-1))
            
            # Basic OpEx calculation
            base_opex = cum_chargers * params["OpExPerCharger"] * current_efficiency_factor
            
            # Apply demand utilization adjustment to OpEx
            # Lower utilization can reduce some variable OpEx components
            utilization_factor = demand_utilization[y]["charger_utilization"]
            adjusted_opex = base_opex * (0.7 + 0.3 * utilization_factor)  # 70% fixed costs, 30% variable
            
            depr = rab_df.loc[rab_df["Year"] == y, "Depreciation"].values[0]
            obsolescence = rab_df.loc[rab_df["Year"] == y, "ObsolescenceWriteoff"].values[0]
            
            # Apply operational efficiency and demand utilization to third-party revenue
            tpr_base = cum_chargers * params["ThirdPartyRevenue"] * params["OperationalEfficiency"]
            tpr = tpr_base * demand_utilization[y]["effective_revenue_factor"]
            
            offset = cum_chargers * params["SharedAssetOffset"]
            
            # Include environmental benefits as an offset if enabled
            env_benefit = env_benefits[y]["total_annual_benefit"] if params.get("IncludeEnvironmentalBenefits", False) else 0
            
            # Calculate allowed revenue
            allowed = return_on_cap + adjusted_opex + depr + obsolescence - tpr - offset - env_benefit
            
            # Ensure customer base is positive
            customer_base = max(1, params["CustomerBase"])
            bill_impact = allowed / customer_base
            
            rev_data.append([
                y, avg_rab, return_on_cap, adjusted_opex, depr, obsolescence, 
                tpr, offset, env_benefit, allowed, bill_impact,
                current_efficiency_factor, params["OperationalEfficiency"], 
                demand_utilization[y]["charger_utilization"],
                wacc
            ])
        except Exception as e:
            print(f"Error in revenue calculation for year {y}: {str(e)}")
            # Use reasonable fallback values
            rev_data.append([
                y, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                params["EfficiencyFactor"], params["OperationalEfficiency"],
                params.get("DemandUtilization", default_params["DemandUtilization"]),
                params["WACC1to5"]
            ])
    
    revenue_df = pd.DataFrame(rev_data, columns=[
        "Year", "AvgRAB", "ReturnOnCapital", "Opex", "Depreciation", "ObsolescenceWriteoff",
        "ThirdPartyRevenue", "SharedAssetOffset", "EnvironmentalBenefit", 
        "AllowedRevenue", "BillImpactPerCustomer",
        "CurrentEfficiencyFactor", "OperationalEfficiency", "DemandUtilization",
        "RiskAdjustedWACC"
    ])
    
    # Handle NaN values that might have been created in error cases
    revenue_df = revenue_df.fillna(0)
    
    # Calculate running sums
    revenue_df["CumulativeBillImpact"] = revenue_df["BillImpactPerCustomer"].cumsum()
    revenue_df["TotalCostAllCustomers"] = revenue_df["AllowedRevenue"].sum()

    # E) Compute Summary Statistics with enhanced metrics
    try:
        avg_bill = revenue_df["BillImpactPerCustomer"].mean()
        peak_bill = revenue_df["BillImpactPerCustomer"].max()
        year_peak = revenue_df.loc[revenue_df["BillImpactPerCustomer"].idxmax(), "Year"]
        total_rev = revenue_df["AllowedRevenue"].sum()
        final_cum_bill = revenue_df["CumulativeBillImpact"].iloc[-1]
        final_total_cost = revenue_df["TotalCostAllCustomers"].iloc[-1]
        
        # Calculate environmental benefits if included
        if params.get("IncludeEnvironmentalBenefits", False):
            total_env_benefit = revenue_df["EnvironmentalBenefit"].sum()
            net_cost = total_rev - total_env_benefit
        else:
            total_env_benefit = 0
            net_cost = total_rev
    except Exception as e:
        print(f"Error calculating summary statistics: {str(e)}")
        avg_bill = 0
        peak_bill = 0
        year_peak = 0
        total_rev = 0
        final_cum_bill = 0
        final_total_cost = 0
        total_env_benefit = 0
        net_cost = 0
    
    # Initialize npv_bill_impact before try block
    npv_bill_impact = 0
    
    # Calculate NPV of bill impacts using risk-adjusted WACC as discount rate
    try:
        npv_bill_impact = 0
        for y in years:
            # Use risk-adjusted WACC for proper discounting
            discount_rate = revenue_df.loc[revenue_df["Year"] == y, "RiskAdjustedWACC"].values[0]
            bill_y = revenue_df.loc[revenue_df["Year"] == y, "BillImpactPerCustomer"].values[0]
            npv_bill_impact += bill_y / ((1 + discount_rate) ** (y-1))
    except Exception as e:
        print(f"Error calculating NPV: {str(e)}")
        npv_bill_impact = 0
    
    # Initialize final_efficiency_factor before try block
    final_efficiency_factor = params["EfficiencyFactor"]
    
    try:
        final_efficiency_factor = revenue_df["CurrentEfficiencyFactor"].iloc[-1]
    except:
        final_efficiency_factor = params["EfficiencyFactor"]
    
    summary_stats = {
        "Average Annual Bill Impact": avg_bill,
        "Peak Annual Bill Impact": peak_bill,
        "Year of Peak Impact": year_peak,
        "Total Revenue Requirement": total_rev,
        "Cumulative Bill Impact/Customer": final_cum_bill,
        "Total Cumulative Cost to All Customers": revenue_df["AllowedRevenue"].sum(),
        "NPV of Bill Impacts": npv_bill_impact,
        "Final Year Efficiency Factor": final_efficiency_factor
    }
    
    # F) Distributional Impact Analysis
    # Calculate impacts across income quintiles
    try:
        avg_annual_bill_impact = revenue_df["BillImpactPerCustomer"].mean()
        distributional_df = calculate_distributional_impacts(avg_annual_bill_impact, income_quintiles)
    except Exception as e:
        print(f"Error in distributional analysis: {str(e)}")
        # Create a default distributional dataframe
        quintiles = ["Q1", "Q2", "Q3", "Q4", "Q5"]
        distributional_df = pd.DataFrame({
            "quintile": quintiles,
            "annual_income": [income_quintiles[q]["income"] for q in quintiles],
            "electricity_spend": [income_quintiles[q]["electricity_spend"] for q in quintiles],
            "bill_impact": [avg_bill] * 5,
            "impact_pct_income": [avg_bill / income_quintiles[q]["income"] * 100 for q in quintiles],
            "impact_pct_bill": [avg_bill / income_quintiles[q]["electricity_spend"] * 100 for q in quintiles]
        })
    
    # G) Private Market and Competitiveness Analysis
    try:
        # Calculate what would happen in a competitive market
        competitive_market = calculate_competitive_market(
            years=15, 
            chargers_per_year=params["ChargersPerYear"],
            innovation_rate=params["InnovationRate"]
        )
        
        # Calculate displacement of private market
        private_displacement = calculate_private_market_displacement(
            rab_chargers=rollout_df["ChargersInstalled"].values,
            private_market_displacement_rate=params["PrivateMarketDisplacement"]
        )
        
        # Create competitiveness dataframe
        competitiveness_df = pd.DataFrame({
            "Year": list(range(1, 16)),
            "RAB_Chargers_Installed": rollout_df["ChargersInstalled"].values,
            "RAB_Cumulative_Chargers": rollout_df["CumulativeChargers"].values,
            "Private_Market_Baseline": private_displacement["baseline_private"],
            "Private_Market_With_RAB": private_displacement["actual_private"],
            "Private_Market_Displaced": private_displacement["displaced_chargers"],
            "Competitive_Market_Chargers": competitive_market["chargers"],
            "Competitive_Market_Cumulative": competitive_market["cumulative_chargers"],
            "Competitive_Market_CapEx": competitive_market["capex"],
            "Competitive_Market_OpEx": competitive_market["opex"],
            "RAB_CapEx": [params["CapExPerCharger"] * params["CostEscalation"]] * 15,
            "RAB_OpEx": [params["OpExPerCharger"] * params["EfficiencyFactor"]] * 15
        })
        
        # Calculate total chargers across both markets
        competitiveness_df["Total_Market_Chargers"] = (
            competitiveness_df["RAB_Cumulative_Chargers"] + 
            competitiveness_df["Private_Market_With_RAB"]
        )
        
        # Calculate innovation gap
        competitiveness_df["Innovation_Gap_CapEx"] = (
            competitiveness_df["RAB_CapEx"] - 
            competitiveness_df["Competitive_Market_CapEx"]
        )
        
        competitiveness_df["Innovation_Gap_OpEx"] = (
            competitiveness_df["RAB_OpEx"] - 
            competitiveness_df["Competitive_Market_OpEx"]
        )
    except Exception as e:
        print(f"Error in competitiveness analysis: {str(e)}")
        # Create a minimal competitiveness dataframe
        competitiveness_df = pd.DataFrame({
            "Year": list(range(1, 16)),
            "RAB_Chargers_Installed": rollout_df["ChargersInstalled"].values,
            "RAB_Cumulative_Chargers": rollout_df["CumulativeChargers"].values,
            "Private_Market_Baseline": [0] * 15,
            "Private_Market_With_RAB": [0] * 15,
            "Private_Market_Displaced": [0] * 15,
            "Competitive_Market_Chargers": [0] * 15,
            "Competitive_Market_Cumulative": [0] * 15,
            "Competitive_Market_CapEx": [0] * 15,
            "Competitive_Market_OpEx": [0] * 15,
            "RAB_CapEx": [params["CapExPerCharger"] * params["CostEscalation"]] * 15,
            "RAB_OpEx": [params["OpExPerCharger"] * params["EfficiencyFactor"]] * 15,
            "Total_Market_Chargers": rollout_df["CumulativeChargers"].values,
            "Innovation_Gap_CapEx": [0] * 15,
            "Innovation_Gap_OpEx": [0] * 15
        })
    
    return (
        rollout_df, 
        depreciation_df, 
        rab_df, 
        revenue_df, 
        summary_stats, 
        distributional_df, 
        competitiveness_df
    )


def run_monte_carlo_simulation(n_simulations=500):
    """
    Run Monte Carlo simulation on the model to understand uncertainty and risk.
    
    Parameters:
        n_simulations (int): Number of Monte Carlo simulations to run
        
    Returns:
        DataFrame: Results of all simulations
    """
    # Generate parameter sets
    param_sets = generate_monte_carlo_params(n_simulations)
    
    # Run model for each parameter set
    results = []
    
    for i, params in enumerate(param_sets):
        try:
            _, _, _, rev_df, stats, dist_df, _ = run_ev_charger_model(params)
            
            # Ensure quintiles exist before accessing them
            q1_impact = 0
            q5_impact = 0
            regressive_ratio = 1
            
            if not dist_df.empty and "quintile" in dist_df.columns and "impact_pct_income" in dist_df.columns:
                q1_rows = dist_df[dist_df["quintile"] == "Q1"]
                q5_rows = dist_df[dist_df["quintile"] == "Q5"]
                
                if not q1_rows.empty and not q5_rows.empty:
                    q1_impact = q1_rows["impact_pct_income"].values[0]
                    q5_impact = q5_rows["impact_pct_income"].values[0]
                    # Avoid division by zero
                    if q5_impact > 0:
                        regressive_ratio = q1_impact / q5_impact
            
            # Store key outputs
            results.append({
                "simulation": i,
                "avg_bill_impact": stats.get("Average Annual Bill Impact", 0),
                "peak_bill_impact": stats.get("Peak Annual Bill Impact", 0),
                "cumulative_bill": stats.get("Cumulative Bill Impact/Customer", 0),
                "npv_bill_impact": stats.get("NPV of Bill Impacts", 0),
                "total_cost": stats.get("Total Cumulative Cost to All Customers", 0),
                "q1_impact_pct_income": q1_impact,
                "q5_impact_pct_income": q5_impact,
                "regressive_ratio": regressive_ratio,
                # Store key input parameters
                "capex": params["CapExPerCharger"],
                "opex": params["OpExPerCharger"],
                "asset_life": params["AssetLife"],
                "wacc": params["WACC1to5"],
                "efficiency_factor": params["EfficiencyFactor"],
                "deployment_delay": params["DeploymentDelay"]
            })
        except Exception as e:
            print(f"Error in simulation {i}: {str(e)}")
            continue
    
    # Make sure we have at least one result
    if not results:
        # Return an empty DataFrame with the expected columns to avoid errors
        return pd.DataFrame(columns=[
            "simulation", "avg_bill_impact", "peak_bill_impact", "cumulative_bill", 
            "npv_bill_impact", "total_cost", "q1_impact_pct_income", "q5_impact_pct_income", 
            "regressive_ratio", "capex", "opex", "asset_life", "wacc", "efficiency_factor", 
            "deployment_delay"
        ])
    
    return pd.DataFrame(results)


def run_comparison_scenarios():
    """
    Runs multiple scenarios and returns their results for comparison.
    
    Returns:
        dict: Dictionary of scenario dataframes
    """
    scenarios = {
        "Base Case": default_params.copy(),
        "High Cost Case": {**default_params.copy(), **high_plus_params},
        "Low Cost Case": {
            **default_params.copy(),
            "CapExPerCharger": 4500,
            "OpExPerCharger": 400,
            "WACC1to5": 0.05,
            "EfficiencyFactor": 0.95,
            "EfficiencyDegradation": 0.0,
            "DeploymentDelay": 0.95
        },
        "More Chargers": {
            **default_params.copy(),
            "ChargersPerYear": 7500
        },
        "Tech Obsolescence": {
            **default_params.copy(),
            "AssetLife": 5,
            "CapExPerCharger": 6500
        },
        "Operational Inefficiency": {
            **default_params.copy(),
            "EfficiencyFactor": 1.25,
            "EfficiencyDegradation": 0.05,
            "OperationalEfficiency": 0.75
        },
        "Private Market Impact": {
            **default_params.copy(),
            "PrivateMarketDisplacement": 0.7
        }
    }
    
    # Run all scenarios
    scenario_results = {}
    scenario_dfs = {"revenue": {}, "distribution": {}, "competition": {}}
    
    for name, params in scenarios.items():
        try:
            rollout_df, depr_df, rab_df, rev_df, summary, dist_df, comp_df = run_ev_charger_model(params)
            
            rev_df["Scenario"] = name
            dist_df["Scenario"] = name
            comp_df["Scenario"] = name
            
            scenario_results[name] = summary
            scenario_dfs["revenue"][name] = rev_df
            scenario_dfs["distribution"][name] = dist_df
            scenario_dfs["competition"][name] = comp_df
        except Exception as e:
            print(f"Error running scenario '{name}': {str(e)}")
            # Create minimal placeholder dataframes with the scenario name
            years = range(1, 16)
            
            # Create minimal revenue df
            rev_df = pd.DataFrame({
                "Year": list(years),
                "BillImpactPerCustomer": [0] * 15,
                "CumulativeBillImpact": [0] * 15,
                "CurrentEfficiencyFactor": [1.0] * 15,
                "Scenario": [name] * 15
            })
            
            # Create minimal distribution df
            quintiles = ["Q1", "Q2", "Q3", "Q4", "Q5"]
            dist_df = pd.DataFrame({
                "quintile": quintiles,
                "impact_pct_income": [0] * 5,
                "impact_pct_bill": [0] * 5,
                "Scenario": [name] * 5
            })
            
            # Create minimal competition df
            comp_df = pd.DataFrame({
                "Year": list(years),
                "RAB_Chargers_Installed": [0] * 15,
                "RAB_Cumulative_Chargers": [0] * 15,
                "Private_Market_Baseline": [0] * 15,
                "Private_Market_With_RAB": [0] * 15,
                "Private_Market_Displaced": [0] * 15,
                "Competitive_Market_Chargers": [0] * 15,
                "Competitive_Market_Cumulative": [0] * 15,
                "Competitive_Market_CapEx": [0] * 15,
                "Competitive_Market_OpEx": [0] * 15,
                "RAB_CapEx": [0] * 15,
                "RAB_OpEx": [0] * 15,
                "Total_Market_Chargers": [0] * 15,
                "Innovation_Gap_CapEx": [0] * 15,
                "Innovation_Gap_OpEx": [0] * 15,
                "Scenario": [name] * 15
            })
            
            # Create minimal summary
            summary = {
                "Average Annual Bill Impact": 0,
                "Peak Annual Bill Impact": 0,
                "Year of Peak Impact": 0,
                "Total Revenue Requirement": 0,
                "Cumulative Bill Impact/Customer": 0,
                "Total Cumulative Cost to All Customers": 0,
                "NPV of Bill Impacts": 0,
                "Final Year Efficiency Factor": 0
            }
            
            scenario_results[name] = summary
            scenario_dfs["revenue"][name] = rev_df
            scenario_dfs["distribution"][name] = dist_df
            scenario_dfs["competition"][name] = comp_df
    
    # Make sure we have at least one scenario result
    if not scenario_results:
        # Create a default base case result
        name = "Base Case"
        try:
            rollout_df, depr_df, rab_df, rev_df, summary, dist_df, comp_df = run_ev_charger_model(default_params)
            
            rev_df["Scenario"] = name
            dist_df["Scenario"] = name
            comp_df["Scenario"] = name
            
            scenario_results[name] = summary
            scenario_dfs["revenue"][name] = rev_df
            scenario_dfs["distribution"][name] = dist_df
            scenario_dfs["competition"][name] = comp_df
        except Exception as e:
            print(f"Error creating default scenario: {str(e)}")
            # If even the default scenario fails, create empty DataFrames
            results_df = pd.DataFrame()
            all_revenue_df = pd.DataFrame()
            all_distribution_df = pd.DataFrame()  
            all_competition_df = pd.DataFrame()
            return results_df, all_revenue_df, all_distribution_df, all_competition_df
    
    # Convert results to DataFrames
    results_df = pd.DataFrame(scenario_results).T
    
    # Combine all revenue dataframes
    all_revenue_df = pd.concat(scenario_dfs["revenue"].values())
    all_distribution_df = pd.concat(scenario_dfs["distribution"].values())
    all_competition_df = pd.concat(scenario_dfs["competition"].values())
    
    return results_df, all_revenue_df, all_distribution_df, all_competition_df


def sensitivity_analysis(param_name, test_values, outcome_key):
    """
    Performs a sensitivity analysis on a given parameter.
    
    Parameters:
      param_name (str): Name of the parameter to test.
      test_values (list): List of values to test.
      outcome_key (str): Key from summary_stats to capture.
      
    Returns:
      DataFrame: Two columns with the test values and corresponding outcomes.
    """
    results = []
    for val in test_values:
        temp_params = default_params.copy()
        temp_params[param_name] = val
        _, _, _, _, stats, _, _ = run_ev_charger_model(temp_params)
        results.append([val, stats[outcome_key]])
    return pd.DataFrame(results, columns=[param_name, outcome_key])


# ========================
# 4. Streamlit Web Interface
# ========================
def main():
    """
    Streamlit web interface for the Enhanced EV Charger RAB Model.
    
    This dashboard extends the original model with:
    1. Operational inefficiency factors
    2. Technology obsolescence risk
    3. Distributional (regressive) impact analysis
    4. Anti-competitive effects analysis
    5. Monte Carlo simulation for risk assessment
    """
    st.set_page_config(page_title="EV Charger RAB Model", layout="wide")
    
    st.title("EV Charger RAB Model - Critical Analysis Dashboard")
    
    # Introduction text with explanation of enhancements
    st.markdown("""
    ### Critical Analysis of the RAB Model for EV Charger Rollout
    
    This dashboard evaluates the Regulatory Asset Base (RAB) Model for EV Charger rollout, considering important factors:
    
    1. **Operational Efficiency**: Distribution companies typically face efficiency challenges with new technologies
    2. **Regressive Bill Impacts**: How costs may disproportionately affect lower-income households
    3. **Market Effects**: How regulated monopoly provision relates to private investment and innovation
    4. **Risk Assessment**: Monte Carlo simulation to understand the range of possible outcomes
    
    Use the sidebar to adjust model parameters and explore different scenarios.
    """)
    
    # Create tabs for different analyses
    tabs = st.tabs([
        "Financial Overview", 
        "Income Distribution Impact", 
        "Market Competition Effects",
        "Technology & Environment",
        "Risk Assessment", 
        "Scenario Comparison"
    ])
    
    # Sidebar for user inputs - Organized into sections with expanders
    st.sidebar.header("Model Parameters")
    st.sidebar.markdown("""
    Adjust parameters to explore different scenarios. 
    Hover over any parameter for more information about its effect on the model.
    """)
    
    # Basic Parameters
    with st.sidebar.expander("Basic Parameters", expanded=True):
        chargers_per_year = st.number_input(
            "Chargers Installed per Year (Years 1-6)", 
            min_value=1000, 
            max_value=10000, 
            value=default_params["ChargersPerYear"], 
            step=500,
            help="Number of EV chargers installed each year during the deployment period"
        )
        
        capex_per_charger = st.number_input(
            "CapEx per Charger ($)", 
            min_value=1000, 
            max_value=10000, 
            value=default_params["CapExPerCharger"], 
            step=500
        )
        
        opex_per_charger = st.number_input(
            "OpEx per Charger ($ per year)", 
            min_value=100, 
            max_value=1000, 
            value=default_params["OpExPerCharger"],

            step=50
        )
        
        asset_life = st.number_input(
            "Asset Life (Years)", 
            min_value=3, 
            max_value=15, 
            value=default_params["AssetLife"]
        )
        
        customer_base = st.number_input(
            "Customer Base", 
            min_value=500000, 
            max_value=5000000, 
            value=default_params["CustomerBase"], 
            step=100000
        )
    
    # Financing Parameters
    with st.sidebar.expander("Financing Parameters"):
        wacc1to5 = st.slider(
            "WACC (Years 1-5)", 
            min_value=0.03, 
            max_value=0.1, 
            value=default_params["WACC1to5"], 
            step=0.005,
            format="%.3f"
        )
        
        wacc6to10 = st.slider(
            "WACC (Years 6-10)", 
            min_value=0.03, 
            max_value=0.1, 
            value=default_params["WACC6to10"], 
            step=0.005,
            format="%.3f"
        )
        
        wacc11to15 = st.slider(
            "WACC (Years 11-15)", 
            min_value=0.03, 
            max_value=0.1, 
            value=default_params["WACC11to15"], 
            step=0.005,
            format="%.3f"
        )
    
    # Efficiency and Implementation Parameters
    with st.sidebar.expander("Efficiency & Implementation"):
        efficiency_factor = st.slider(
            "Efficiency Factor (>1 means inefficiency)", 
            min_value=0.8, 
            max_value=1.5, 
            value=default_params["EfficiencyFactor"], 
            step=0.05,
            format="%.2f",
            help="Factor applied to OpEx. Values >1 represent inefficiency premium."
        )
        
        efficiency_degradation = st.slider(
            "Annual Efficiency Degradation", 
            min_value=0.0, 
            max_value=0.10, 
            value=default_params["EfficiencyDegradation"], 
            step=0.01,
            format="%.2f",
            help="Annual increase in inefficiency (e.g., 0.03 means 3% worse each year)"
        )
        
        deployment_delay = st.slider(
            "Deployment Delay Factor", 
            min_value=0.8, 
            max_value=2.0, 
            value=default_params["DeploymentDelay"], 
            step=0.1,
            format="%.1f",
            help="Multiplier for deployment schedule (>1 means delays)"
        )
        
        cost_escalation = st.slider(
            "Cost Escalation Factor", 
            min_value=0.9, 
            max_value=1.5, 
            value=default_params["CostEscalation"], 
            step=0.05,
            format="%.2f",
            help="Multiplier for capital costs (>1 means cost overruns)"
        )
        
        operational_efficiency = st.slider(
            "Operational Efficiency", 
            min_value=0.5, 
            max_value=1.0, 
            value=default_params["OperationalEfficiency"], 
            step=0.05,
            format="%.2f",
            help="How efficiently chargers are operated (<1 means underutilization)"
        )
    
    # Technology and Demand Parameters
    with st.sidebar.expander("Technology & Demand"):
        tech_obsolescence_rate = st.slider(
            "Technology Obsolescence Rate", 
            min_value=0.0, 
            max_value=0.15, 
            value=default_params["TechObsolescenceRate"], 
            step=0.01,
            format="%.2f",
            help="Annual rate of technology obsolescence (e.g., 0.05 means 5% of asset value becomes obsolete each year)"
        )
        
        demand_utilization = st.slider(
            "Initial Demand Utilization", 
            min_value=0.3, 
            max_value=1.0, 
            value=default_params["DemandUtilization"], 
            step=0.05,
            format="%.2f",
            help="Initial utilization rate of chargers (1.0 = full utilization)"
        )
        
        utilization_growth_rate = st.slider(
            "Utilization Growth Rate", 
            min_value=0.0, 
            max_value=0.15, 
            value=default_params["UtilizationGrowthRate"], 
            step=0.01,
            format="%.2f",
            help="Annual growth in utilization as EV adoption increases"
        )
        
        cost_decline_rate = st.slider(
            "Technology Cost Decline Rate", 
            min_value=0.0, 
            max_value=0.1, 
            value=default_params["CostDeclineRate"], 
            step=0.01,
            format="%.2f",
            help="Annual decline in CapEx costs due to technology improvements"
        )
        
        ev_adoption_rate = st.slider(
            "EV Adoption Growth Rate", 
            min_value=0.05, 
            max_value=0.3, 
            value=default_params["EVAdoptionRate"], 
            step=0.05,
            format="%.2f",
            help="Annual growth rate of EV adoption"
        )
    
    # Risk and Environmental Parameters
    with st.sidebar.expander("Risk & Environmental Benefits"):
        use_risk_premium = st.checkbox(
            "Apply Risk Premium to WACC", 
            value=default_params["UseRiskPremium"],
            help="Whether to apply risk premium to WACC for uncertain technology investments"
        )
        
        risk_premium = st.slider(
            "Risk Premium", 
            min_value=0.0, 
            max_value=0.03, 
            value=default_params["RiskPremium"], 
            step=0.005,
            format="%.3f",
            help="Additional risk premium for WACC for new technology investments",
            disabled=not use_risk_premium
        )
        
        include_environmental_benefits = st.checkbox(
            "Include Environmental Benefits", 
            value=default_params["IncludeEnvironmentalBenefits"],
            help="Whether to include environmental benefits in the analysis"
        )
        
        environmental_benefit_per_charger = st.number_input(
            "Environmental Benefit per Charger ($ per year)", 
            min_value=0, 
            max_value=1000, 
            value=default_params["EnvironmentalBenefitPerCharger"], 
            step=50,
            disabled=not include_environmental_benefits,
            help="Annual environmental benefit ($) per charger from reduced emissions"
        )
    
    # Market Impact Parameters
    with st.sidebar.expander("Market Impact"):
        private_market_displacement = st.slider(
            "Private Market Displacement Rate", 
            min_value=0.0, 
            max_value=1.0, 
            value=default_params["PrivateMarketDisplacement"], 
            step=0.1,
            format="%.1f",
            help="How much the RAB model crowds out private investment (0-1)"
        )
        
        innovation_rate = st.slider(
            "Competitive Market Innovation Rate", 
            min_value=0.0, 
            max_value=0.1, 
            value=default_params["InnovationRate"], 
            step=0.01,
            format="%.2f",
            help="Annual cost reduction in competitive market"
        )
        
        monopoly_innovation_rate = st.slider(
            "Monopoly Innovation Rate", 
            min_value=0.0, 
            max_value=0.05, 
            value=default_params["MonopolyInnovationRate"], 
            step=0.005,
            format="%.3f",
            help="Annual cost reduction in monopoly market (typically lower)"
        )
        
        public_private_ratio = st.slider(
            "Optimal Public/Private Ratio", 
            min_value=0.1, 
            max_value=2.0, 
            value=default_params["PublicPrivateRatio"], 
            step=0.1,
            format="%.1f",
            help="Optimal ratio of public to private chargers"
        )
    
    # Preset Scenarios
    with st.sidebar.expander("Preset Scenarios"):
        scenario_options = {
            "Custom (current settings)": None,
            "Base Case": default_params,
            "High Cost Case": {**default_params, **high_plus_params},
            "Low Cost Case": {
                **default_params,
                "CapExPerCharger": 4500,
                "OpExPerCharger": 400,
                "WACC1to5": 0.05,
                "EfficiencyFactor": 0.95,
                "EfficiencyDegradation": 0.0,
                "DeploymentDelay": 0.95
            },
            "Technology Obsolescence": {
                **default_params,
                "AssetLife": 5,
                "CapExPerCharger": 6500
            },
            "Operational Inefficiency": {
                **default_params,
                "EfficiencyFactor": 1.25,
                "EfficiencyDegradation": 0.05,
                "OperationalEfficiency": 0.75
            },
            "High Market Displacement": {
                **default_params,
                "PrivateMarketDisplacement": 0.7
            }
        }
        
        selected_scenario = st.selectbox(
            "Load Preset Scenario", 
            list(scenario_options.keys())
        )
        
        if selected_scenario != "Custom (current settings)" and st.button(f"Load {selected_scenario}"):
            try:
                # Update sidebar values when a scenario is selected
                # This requires a bit of session state management
                st.session_state.scenario_params = scenario_options[selected_scenario].copy()
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error loading scenario: {str(e)}")
    
    # Apply scenario parameters if loaded
    if hasattr(st.session_state, 'scenario_params') and st.session_state.scenario_params:
        try:
            params = st.session_state.scenario_params.copy()
            # Clear the scenario params after loading
            st.session_state.scenario_params = None
        except Exception as e:
            st.error(f"Error applying scenario parameters: {str(e)}")
            params = default_params.copy()
    else:
        # Use the current sidebar values
        params = default_params.copy()
        params.update({
            "ChargersPerYear": chargers_per_year,
            "CapExPerCharger": capex_per_charger,
            "OpExPerCharger": opex_per_charger,
            "AssetLife": asset_life,
            "WACC1to5": wacc1to5,
            "WACC6to10": wacc6to10,
            "WACC11to15": wacc11to15,
            "CustomerBase": customer_base,
            "EfficiencyFactor": efficiency_factor,
            "EfficiencyDegradation": efficiency_degradation,
            "DeploymentDelay": deployment_delay,
            "CostEscalation": cost_escalation,
            "OperationalEfficiency": operational_efficiency,
            "PrivateMarketDisplacement": private_market_displacement,
            "InnovationRate": innovation_rate,
            "MonopolyInnovationRate": monopoly_innovation_rate,
            "TechObsolescenceRate": tech_obsolescence_rate,
            "DemandUtilization": demand_utilization,
            "UtilizationGrowthRate": utilization_growth_rate,
            "UseRiskPremium": use_risk_premium,
            "RiskPremium": risk_premium,
            "CostDeclineRate": cost_decline_rate,
            "EVAdoptionRate": ev_adoption_rate,
            "EnvironmentalBenefitPerCharger": environmental_benefit_per_charger,
            "IncludeEnvironmentalBenefits": include_environmental_benefits,
            "PublicPrivateRatio": public_private_ratio
        })
    
    # Run the model with the current parameters
    with st.spinner("Calculating model results..."):
        rollout_df, depr_df, rab_df, rev_df, summary_stats, dist_df, comp_df = run_ev_charger_model(params)
        
        # Save results for use in all tabs
        revenue_df = rev_df
        competitiveness_df = comp_df
        depreciation_df = depr_df
        distributional_df = dist_df
    
    # ===============================
    # Tab 1: Financial Overview
    # ===============================
    with tabs[0]:
        # Display summary metrics
        st.subheader("Financial Overview")
        
        # Create 3 columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Average Annual Bill Impact", 
                f"${summary_stats['Average Annual Bill Impact']:.2f}",
                help="Average annual increase in household electricity bills"
            )
            st.metric(
                "Peak Annual Bill Impact", 
                f"${summary_stats['Peak Annual Bill Impact']:.2f}",
                help="Maximum annual increase in household bills (typically Year 6-7)"
            )
            st.metric(
                "NPV of Bill Impacts", 
                f"${summary_stats['NPV of Bill Impacts']:.2f}",
                help="Net present value of bill impacts over 15 years"
            )
        
        with col2:
            st.metric(
                "Cumulative Bill Impact", 
                f"${summary_stats['Cumulative Bill Impact/Customer']:.2f}",
                help="Total cumulative bill increase per household over 15 years"
            )
            st.metric(
                "Year of Peak Impact", 
                f"Year {int(summary_stats['Year of Peak Impact'])}",
                help="Year when bill impact reaches its maximum"
            )
            st.metric(
                "Final Year Efficiency Factor", 
                f"{summary_stats['Final Year Efficiency Factor']:.2f}x",
                help="How inefficient operations become by the end of the period"
            )
        
        with col3:
            st.metric(
                "Total Revenue Requirement", 
                f"${summary_stats['Total Revenue Requirement']/1e6:.1f}M",
                help="Total revenue required to fund the charger rollout"
            )
            st.metric(
                "Total Cost to All Customers", 
                f"${summary_stats['Total Cumulative Cost to All Customers']/1e6:.1f}M",
                help="Total cost spread across all customers over 15 years"
            )
        
        # Create tabs for different visualizations within the Base Model tab
        base_viz_tabs = st.tabs([
            "Bill Impacts", 
            "RAB Evolution", 
            "Efficiency Factors",
            "Detailed Metrics"
        ])
        
        # Bill Impacts Tab
        with base_viz_tabs[0]:
            # Annual and Cumulative Bill Impact Charts (side by side)
            col1, col2 = st.columns(2)
            
            with col1:
                # Annual Bill Impact
                fig = px.line(
                    rev_df, 
                    x="Year", 
                    y="BillImpactPerCustomer",
                    title="Annual Bill Impact per Customer",
                    labels={"BillImpactPerCustomer": "Bill Impact ($)", "Year": "Year"},
                    markers=True,
                    line_shape="spline"
                )
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Annual Bill Impact ($)"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Cumulative Bill Impact
                fig = px.line(
                    rev_df, 
                    x="Year", 
                    y="CumulativeBillImpact",
                    title="Cumulative Bill Impact per Customer",
                    labels={"CumulativeBillImpact": "Cumulative Bill Impact ($)", "Year": "Year"},
                    markers=True,
                    line_shape="spline"
                )
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Cumulative Bill Impact ($)"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # Breakdown of revenue components
            st.subheader("Breakdown of Revenue Components")
            
            # Extract the components
            components_df = rev_df[["Year", "ReturnOnCapital", "Opex", "Depreciation", "ThirdPartyRevenue", "SharedAssetOffset"]].copy()
            
            # Third party revenue and shared asset offset are negative (they reduce the revenue requirement)
            components_df["ThirdPartyRevenue"] = -components_df["ThirdPartyRevenue"]
            components_df["SharedAssetOffset"] = -components_df["SharedAssetOffset"]
            
            # Melt the dataframe for stacked bar chart
            melted_df = pd.melt(
                components_df, 
                id_vars=["Year"], 
                value_vars=["ReturnOnCapital", "Opex", "Depreciation", "ThirdPartyRevenue", "SharedAssetOffset"],
                var_name="Component", 
                value_name="Amount"
            )
            
            # Rename for readability
            component_names = {
                "ReturnOnCapital": "Return on Capital",
                "Opex": "Operating Expenses",
                "Depreciation": "Depreciation",
                "ThirdPartyRevenue": "Third Party Revenue (offset)",
                "SharedAssetOffset": "Shared Asset Offset"
            }
            melted_df["Component"] = melted_df["Component"].map(component_names)
            
            # Create stacked bar chart
            fig = px.bar(
                melted_df, 
                x="Year", 
                y="Amount",
                color="Component",
                title="Annual Revenue Requirement Components",
                labels={"Amount": "Amount ($)", "Year": "Year", "Component": "Revenue Component"}
            )
            
            # Customize hover template for simplified tooltips
            hovertemplate = (
                "Year: %{x}<br>" +
                "Component: %{customdata}<br>" +
                "Amount: $%{y:.2f}M<br>" +
                "<extra></extra>"
            )
            
            # Add custom data for hover template
            fig.update_traces(
                customdata=melted_df["Component"],
                hovertemplate=hovertemplate
            )
            
            fig.update_layout(
                height=500,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Amount ($)"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
        
        # RAB Evolution Tab
        with base_viz_tabs[1]:
            # RAB Evolution Chart
            fig = px.line(
                rab_df, 
                x="Year", 
                y="ClosingRAB",
                title="Regulatory Asset Base (RAB) Evolution",
                labels={"ClosingRAB": "Closing RAB ($)", "Year": "Year"},
                markers=True,
                line_shape="spline"
            )
            fig.update_layout(
                height=400,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Closing RAB ($)"),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # RAB Components Chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add Additions and Depreciation as bars
            fig.add_trace(
                go.Bar(
                    x=rab_df["Year"],
                    y=rab_df["Additions"],
                    name="Additions",
                    marker_color="green"
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Bar(
                    x=rab_df["Year"],
                    y=rab_df["Depreciation"],
                    name="Depreciation",
                    marker_color="red"
                ),
                secondary_y=False
            )
            
            # Add Opening and Closing RAB as lines
            fig.add_trace(
                go.Scatter(
                    x=rab_df["Year"],
                    y=rab_df["OpeningRAB"],
                    name="Opening RAB",
                    mode="lines+markers",
                    line=dict(color="blue")
                ),
                secondary_y=True
            )
            
            fig.add_trace(
                go.Scatter(
                    x=rab_df["Year"],
                    y=rab_df["ClosingRAB"],
                    name="Closing RAB",
                    mode="lines+markers",
                    line=dict(color="purple")
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title="RAB Components: Additions, Depreciation, and Asset Base",
                height=500,
                xaxis=dict(tickmode='linear', dtick=1, title="Year"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                barmode="group"
            )
            
            # Set y-axes titles
            fig.update_yaxes(title_text="Annual Additions/Depreciation ($)", secondary_y=False)
            fig.update_yaxes(title_text="RAB Value ($)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Chargers Rollout Chart
            fig = px.bar(
                rollout_df, 
                x="Year", 
                y="ChargersInstalled",
                title="Annual Charger Installation",
                labels={"ChargersInstalled": "Chargers Installed", "Year": "Year"}
            )
            
            # Add cumulative chargers as a line
            fig.add_trace(
                go.Scatter(
                    x=rollout_df["Year"],
                    y=rollout_df["CumulativeChargers"],
                    name="Cumulative Chargers",
                    mode="lines+markers",
                    yaxis="y2"
                )
            )
            
            fig.update_layout(
                height=400,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Annual Chargers Installed"),
                yaxis2=dict(
                    title="Cumulative Chargers",
                    overlaying="y",
                    side="right"
                ),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Efficiency Factors Tab
        with base_viz_tabs[2]:
            # Efficiency Factor Visualization
            st.subheader("Operational Inefficiency Growth")
            
            # Create a figure with 2 y-axes
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add efficiency factor line
            fig.add_trace(
                go.Scatter(
                    x=rev_df["Year"],
                    y=rev_df["CurrentEfficiencyFactor"],
                    name="Efficiency Factor",
                    mode="lines+markers",
                    line=dict(color="red")
                ),
                secondary_y=False
            )
            
            # Add OpEx to show impact of efficiency factor
            fig.add_trace(
                go.Bar(
                    x=rev_df["Year"],
                    y=rev_df["Opex"],
                    name="Annual OpEx",
                    marker_color="orange"
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title="Impact of Efficiency Factor on Operating Expenses",
                height=500,
                xaxis=dict(tickmode='linear', dtick=1, title="Year"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            # Set y-axes titles
            fig.update_yaxes(title_text="Efficiency Factor (multiplier)", secondary_y=False)
            fig.update_yaxes(title_text="Annual OpEx ($)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Explain the efficiency factors
            st.markdown("""
            **How Efficiency Factors Work:**
            
            - **Efficiency Factor** starts at the base value and increases by the annual degradation percentage each year
            - Higher values represent greater inefficiency (>1.0 means costs are higher than expected)
            - Common sources of inefficiency include:
                - Lack of specialized expertise in EV charger management
                - Poor asset utilization
                - Suboptimal maintenance practices
                - Organizational overhead and bureaucracy
            
            **Key Insight:** Distribution companies often lack the agility and expertise to operate new technologies efficiently, leading to significantly higher operational costs compared to specialized private providers.
            """)
        
        # Detailed Metrics Tab
        with base_viz_tabs[3]:
            # Show full dataframes for detailed analysis
            show_data_expander = st.expander("Show Detailed Data Tables")
            
            with show_data_expander:
                st.subheader("Annual Revenue and Bill Impacts")
                st.dataframe(rev_df)
                
                st.subheader("RAB Evolution")
                st.dataframe(rab_df)
                
                st.subheader("Charger Rollout")
                st.dataframe(rollout_df)
                
                st.subheader("Depreciation Schedule")
                st.dataframe(depr_df)
                
                csv_download = rev_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Revenue Data as CSV",
                    data=csv_download,
                    file_name="revenue_bill_impacts.csv",
                    mime="text/csv"
                )
    
    # ===============================
    # Tab 2: Income Distribution Impact
    # ===============================
    with tabs[1]:
        st.subheader("Distributional Impacts - Regressive Nature of Bill Increases")
        st.markdown("""
        This analysis examines how the bill impacts from the RAB model affect different household income groups. 
        Since electricity is an essential service, rate increases tend to be regressive, impacting lower-income 
        households more severely as a percentage of their income and total household budget.
        """)
        
        # Show the distributional impact analysis
        st.subheader("Bill Impact by Income Quintile")
        
        # Create a more readable version of the table
        dist_table = dist_df.copy()
        dist_table["annual_income"] = dist_table["annual_income"].apply(lambda x: f"${x:,.0f}")
        dist_table["electricity_spend"] = dist_table["electricity_spend"].apply(lambda x: f"${x:.2f}")
        dist_table["bill_impact"] = dist_table["bill_impact"].apply(lambda x: f"${x:.2f}")
        dist_table["impact_pct_income"] = dist_table["impact_pct_income"].apply(lambda x: f"{x:.4f}%")
        dist_table["impact_pct_bill"] = dist_table["impact_pct_bill"].apply(lambda x: f"{x:.2f}%")
        
        dist_table = dist_table.rename(columns={
            "quintile": "Income Group",
            "annual_income": "Annual Household Income",
            "electricity_spend": "Annual Electricity Bill",
            "bill_impact": "Average Annual Bill Increase",
            "impact_pct_income": "% of Annual Income",
            "impact_pct_bill": "% of Electricity Bill"
        })
        
        # Display the table
        st.table(dist_table)
        
        # Visualization of distributional impacts
        col1, col2 = st.columns(2)
        
        with col1:
            # Chart showing impact as % of income
            fig = px.bar(
                dist_df,
                x="quintile",
                y="impact_pct_income",
                title="Bill Impact as Percentage of Annual Income",
                labels={"impact_pct_income": "Impact (% of Income)", "quintile": "Income Group"},
                color="quintile",
                text_auto='.4f'
            )
            fig.update_layout(
                height=400,
                yaxis=dict(title="Impact (% of Annual Income)"),
                hovermode="x",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Chart showing impact as % of electricity bill
            fig = px.bar(
                dist_df,
                x="quintile",
                y="impact_pct_bill",
                title="Bill Impact as Percentage of Electricity Bill",
                labels={"impact_pct_bill": "Impact (% of Bill)", "quintile": "Income Group"},
                color="quintile", 
                text_auto='.2f'
            )
            fig.update_layout(
                height=400,
                yaxis=dict(title="Impact (% of Electricity Bill)"),
                hovermode="x",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Calculate regressivity metrics
        q1_pct_income = dist_df.loc[dist_df["quintile"] == "Q1", "impact_pct_income"].values[0]
        q5_pct_income = dist_df.loc[dist_df["quintile"] == "Q5", "impact_pct_income"].values[0]
        regressivity_ratio = q1_pct_income / q5_pct_income
        
        # Display regressivity metrics
        st.subheader("Regressivity Metrics")
        st.metric(
            "Regressivity Ratio", 
            f"{regressivity_ratio:.2f}x",
            help="How many times more impactful the bill increase is on lowest vs. highest income quintile (as % of income)"
        )
        
        # Explanation of the distributional analysis
        st.markdown(f"""
        ### Key Insights
        
        - **Lowest income quintile** spends **{q1_pct_income:.4f}%** of annual income on the RAB-related bill increase
        - **Highest income quintile** spends only **{q5_pct_income:.4f}%** of annual income
        - The bill increase is **{regressivity_ratio:.2f} times more burdensome** for the lowest income households
        
        This regressivity is particularly problematic because:
        
        1. Lower-income households are less likely to own EVs and benefit from the infrastructure
        2. Essential service prices should not disproportionately burden vulnerable populations
        3. The socialized costs create implicit subsidies from non-EV owners to EV owners
        
        **Alternative approaches** (e.g., user-pays models, targeted subsidies) could distribute costs more equitably.
        """)
    
    # ===============================
    # Tab 3: Market Competition Effects
    # ===============================
    with tabs[2]:
        st.subheader("Anti-Competitive Effects Analysis")
        st.markdown("""
        This analysis examines how a regulated monopoly approach to EV charging infrastructure impacts:
        
        1. **Market Development**: Displacement of private sector investment
        2. **Innovation**: Differences in cost reduction trajectories between competitive and monopoly provision
        3. **Total Market Growth**: Overall availability of charging infrastructure
        """)
        
        # Market displacement visualization
        st.subheader("Market Development Impact")
        
        # Create figure with market development
        fig = px.line(
            comp_df,
            x="Year",
            y=["RAB_Cumulative_Chargers", "Private_Market_With_RAB", "Private_Market_Baseline"],
            title="Impact on Market Development",
            labels={
                "value": "Cumulative Chargers", 
                "Year": "Year",
                "variable": "Market Segment"
            },
            color_discrete_map={
                "RAB_Cumulative_Chargers": "blue",
                "Private_Market_With_RAB": "green",
                "Private_Market_Baseline": "gray"
            }
        )
        
        # Rename the lines for display
        name_map = {
            "RAB_Cumulative_Chargers": "Public chargers (RAB model)",
            "Private_Market_With_RAB": "Private chargers (with RAB)",
            "Private_Market_Baseline": "Private chargers (no RAB)"
        }
        
        # Update traces with simplified tooltips
        for i, trace_name in enumerate(["RAB_Cumulative_Chargers", "Private_Market_With_RAB", "Private_Market_Baseline"]):
            fig.data[i].update(
                name=name_map[trace_name],
                hovertemplate="Year: %{x}<br>" +
                             f"{name_map[trace_name]}: " + "%{y:,.0f}<br>" +
                             "<extra></extra>"
            )
        
        # Add total market with RAB
        fig.add_trace(
            go.Scatter(
                x=comp_df["Year"],
                y=comp_df["Total_Market_Chargers"],
                name="Total chargers",
                mode="lines+markers",
                line=dict(color="purple", width=3, dash="dot"),
                hovertemplate="Year: %{x}<br>" +
                             "Total chargers: %{y:,.0f}<br>" +
                             "<extra></extra>"
            )
        )
        
        # Update layout
        fig.update_layout(
            height=500,
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Cumulative Chargers"),
            hovermode="x unified",
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="center", 
                x=0.5,
                title=""
            )
        )
        
        # Update legend names
        newnames = {
            "RAB_Cumulative_Chargers": "RAB Model Chargers",
            "Private_Market_With_RAB": "Private Market (with RAB)",
            "Private_Market_Baseline": "Private Market (without RAB)"
        }
        
        fig.for_each_trace(
            lambda t: t.update(name = newnames[t.name] if t.name in newnames else t.name)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Innovation gap visualization
        st.subheader("Innovation and Cost Efficiency Gap")
        
        # Create subplots for CapEx and OpEx innovation gaps
        fig = make_subplots(
            rows=1, 
            cols=2,
            subplot_titles=("Capital Cost Evolution", "Operating Cost Evolution")
        )
        
        # Add CapEx comparison
        fig.add_trace(
            go.Scatter(
                x=comp_df["Year"],
                y=comp_df["RAB_CapEx"],
                name="RAB CapEx",
                mode="lines+markers",
                line=dict(color="red")
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=comp_df["Year"],
                y=comp_df["Competitive_Market_CapEx"],
                name="Competitive CapEx",
                mode="lines+markers",
                line=dict(color="green")
            ),
            row=1, col=1
        )
        
        # Add OpEx comparison
        fig.add_trace(
            go.Scatter(
                x=comp_df["Year"],
                y=comp_df["RAB_OpEx"],
                name="RAB OpEx",
                mode="lines+markers",
                line=dict(color="orange")
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=comp_df["Year"],
                y=comp_df["Competitive_Market_OpEx"],
                name="Competitive OpEx",
                mode="lines+markers",
                line=dict(color="blue")
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=400,
            xaxis=dict(tickmode='linear', dtick=1, title="Year"),
            xaxis2=dict(tickmode='linear', dtick=1, title="Year"),
            yaxis=dict(title="CapEx per Charger ($)"),
            yaxis2=dict(title="OpEx per Charger ($)"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate key metrics
        final_year = comp_df["Year"].max()
        
        total_rab_chargers = comp_df.loc[comp_df["Year"] == final_year, "RAB_Cumulative_Chargers"].values[0]
        total_private_with_rab = comp_df.loc[comp_df["Year"] == final_year, "Private_Market_With_RAB"].values[0]
        total_private_baseline = comp_df.loc[comp_df["Year"] == final_year, "Private_Market_Baseline"].values[0]
        
        total_market_with_rab = total_rab_chargers + total_private_with_rab
        
        market_displacement_pct = (total_private_baseline - total_private_with_rab) / total_private_baseline * 100
        
        final_rab_capex = comp_df.loc[comp_df["Year"] == final_year, "RAB_CapEx"].values[0]
        final_competitive_capex = comp_df.loc[comp_df["Year"] == final_year, "Competitive_Market_CapEx"].values[0]
        
        innovation_gap_pct = (final_rab_capex - final_competitive_capex) / final_rab_capex * 100
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Private Market Displacement", 
                f"{market_displacement_pct:.1f}%",
                help="Percentage of private market investment displaced by the RAB model"
            )
        
        with col2:
            st.metric(
                "Final Year Innovation Gap", 
                f"{innovation_gap_pct:.1f}%",
                help="How much higher RAB costs are than competitive market in Year 15"
            )
        
        with col3:
            st.metric(
                "Total Chargers in Year 15", 
                f"{int(total_market_with_rab):,}",
                help="Total chargers deployed across both RAB and private market"
            )
        
        # Explanation of competitive effects
        st.markdown(f"""
        ### Key Insights on Anti-Competitive Effects
        
        - **Private Market Displacement**: The RAB model displaces approximately **{market_displacement_pct:.1f}%** of private investment that would otherwise occur
        
        - **Innovation Gap**: By Year 15, competitive market costs would be **{innovation_gap_pct:.1f}%** lower than monopoly provision due to innovation and competition
        
        - **Market Structure Impacts**:
          - RAB approach creates a protected monopoly with reduced incentives for efficiency
          - Competition drives both cost reduction and service quality improvements
          - Private providers are likely to strategically locate chargers based on demand, rather than political or regulated criteria
        
        **Alternative approaches** could leverage private market innovation while ensuring equitable access through targeted subsidies, performance requirements, or public-private partnerships.
        """)
    
    # ===============================
    # Tab 4: Technology & Environment
    # ===============================
    with tabs[3]:
        st.subheader("Technology Evolution and Environmental Impact Analysis")
        st.markdown("""
        This analysis explores how technology changes over time, including obsolescence, cost declines, 
        utilization patterns, and environmental benefits.
        """)
        
        # Create tabs for different visualizations
        tech_viz_tabs = st.tabs([
            "Technology Evolution", 
            "Utilization & Demand",
            "Environmental Benefits",
            "Public/Private Balance"
        ])
        
        # Technology Evolution Tab
        with tech_viz_tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                # Capital cost evolution
                fig = px.line(
                    rollout_df,
                    x="Year",
                    y="UnitCapEx",
                    title="Evolution of Capital Costs per Charger",
                    labels={"UnitCapEx": "Capital Cost per Charger ($)", "Year": "Year"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Capital Cost per Charger ($)"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Risk-adjusted WACC
                fig = px.line(
                    revenue_df,
                    x="Year",
                    y="RiskAdjustedWACC",
                    title="Risk-Adjusted WACC Over Time",
                    labels={"RiskAdjustedWACC": "Risk-Adjusted WACC", "Year": "Year"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="WACC", tickformat=".2%"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Technological obsolescence impacts
            if params["TechObsolescenceRate"] > 0:
                # Calculate technological obsolescence data
                tech_obsolescence = calculate_tech_obsolescence(
                    years=15, 
                    asset_life=params["AssetLife"],
                    tech_obsolescence_rate=params["TechObsolescenceRate"]
                )
                
                # Create DataFrame for visualization
                tech_obs_df = pd.DataFrame({
                    "Year": list(range(1, 16)),
                    "Cumulative Obsolescence (%)": [tech_obsolescence[y]["cumulative_obsolescence"] * 100 for y in range(1, 16)],
                    "Effective Asset Life (Years)": [tech_obsolescence[y]["effective_asset_life"] for y in range(1, 16)]
                })
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cumulative obsolescence
                    fig = px.line(
                        tech_obs_df,
                        x="Year",
                        y="Cumulative Obsolescence (%)",
                        title="Cumulative Technological Obsolescence",
                        labels={"Cumulative Obsolescence (%)": "Obsolescence (%)", "Year": "Year"},
                        markers=True
                    )
                    
                    fig.update_layout(
                        height=400,
                        xaxis=dict(tickmode='linear', dtick=1),
                        yaxis=dict(title="Obsolescence (%)"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Effective asset life
                    fig = px.line(
                        tech_obs_df,
                        x="Year",
                        y="Effective Asset Life (Years)",
                        title="Effective Asset Life Over Time",
                        labels={"Effective Asset Life (Years)": "Effective Asset Life (Years)", "Year": "Year"},
                        markers=True
                    )
                    
                    fig.update_layout(
                        height=400,
                        xaxis=dict(tickmode='linear', dtick=1),
                        yaxis=dict(title="Years"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Obsolescence write-offs
                fig = px.bar(
                    rab_df,
                    x="Year",
                    y="ObsolescenceWriteoff",
                    title="Annual Obsolescence Write-offs",
                    labels={"ObsolescenceWriteoff": "Write-off Amount ($)", "Year": "Year"}
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Write-off Amount ($)"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Technological obsolescence analysis is disabled. Enable it by setting a non-zero Technology Obsolescence Rate in the sidebar.")
        
        # Utilization & Demand Tab
        with tech_viz_tabs[1]:
            # Calculate demand utilization data
            demand_utilization = calculate_demand_utilization(
                years=15,
                initial_utilization=params["DemandUtilization"],
                utilization_growth_rate=params["UtilizationGrowthRate"],
                ev_adoption_rate=params["EVAdoptionRate"]
            )
            
            # Create DataFrame for visualization
            util_df = pd.DataFrame({
                "Year": list(range(1, 16)),
                "EV Adoption (%)": [demand_utilization[y]["ev_adoption"] * 100 for y in range(1, 16)],
                "Charger Utilization (%)": [demand_utilization[y]["charger_utilization"] * 100 for y in range(1, 16)],
                "Revenue Factor": [demand_utilization[y]["effective_revenue_factor"] for y in range(1, 16)]
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                # EV adoption
                fig = px.line(
                    util_df,
                    x="Year",
                    y="EV Adoption (%)",
                    title="EV Adoption Over Time",
                    labels={"EV Adoption (%)": "EV Adoption (%)", "Year": "Year"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="EV Adoption (%)"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Charger utilization
                fig = px.line(
                    util_df,
                    x="Year",
                    y="Charger Utilization (%)",
                    title="Charger Utilization Over Time",
                    labels={"Charger Utilization (%)": "Utilization (%)", "Year": "Year"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Utilization (%)"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Impact of utilization on revenue
            fig = px.line(
                util_df,
                x="Year",
                y="Revenue Factor",
                title="Effective Revenue Factor from Utilization",
                labels={"Revenue Factor": "Revenue Factor", "Year": "Year"},
                markers=True
            )
            
            fig.update_layout(
                height=400,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Revenue Factor (multiple)"),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights
            st.markdown("""
            ### Key Insights on Utilization and Demand
            
            - EV adoption follows an S-curve, with initial slow growth followed by acceleration and eventual saturation.
            - Charger utilization increases over time as EV adoption grows, but with some lag.
            - This affects both revenue (higher utilization = more revenue) and OpEx (variable costs increase with utilization).
            - **Policy Implication**: The timing of investment is critical; if deployed too early, chargers may be underutilized.
            """)
        
        # Environmental Benefits Tab
        with tech_viz_tabs[2]:
            if params["IncludeEnvironmentalBenefits"]:
                # Calculate environmental benefits
                env_benefits = calculate_environmental_benefits(
                    years=15,
                    chargers_per_year=adj_chargers_per_year,
                    benefit_per_charger=params["EnvironmentalBenefitPerCharger"],
                    deployment_years=deployment_years
                )
                
                # Create DataFrame for visualization
                env_df = pd.DataFrame({
                    "Year": list(range(1, 16)),
                    "Cumulative Chargers": [env_benefits[y]["cumulative_chargers"] for y in range(1, 16)],
                    "Annual Benefit per Charger ($)": [env_benefits[y]["annual_benefit_per_charger"] for y in range(1, 16)],
                    "Total Annual Benefit ($)": [env_benefits[y]["total_annual_benefit"] for y in range(1, 16)]
                })
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Environmental benefit per charger
                    fig = px.line(
                        env_df,
                        x="Year",
                        y="Annual Benefit per Charger ($)",
                        title="Environmental Benefit per Charger",
                        labels={"Annual Benefit per Charger ($)": "Benefit ($)", "Year": "Year"},
                        markers=True
                    )
                    
                    fig.update_layout(
                        height=400,
                        xaxis=dict(tickmode='linear', dtick=1),
                        yaxis=dict(title="Annual Benefit per Charger ($)"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Total environmental benefits
                    fig = px.line(
                        env_df,
                        x="Year",
                        y="Total Annual Benefit ($)",
                        title="Total Environmental Benefits",
                        labels={"Total Annual Benefit ($)": "Benefit ($)", "Year": "Year"},
                        markers=True
                    )
                    
                    fig.update_layout(
                        height=400,
                        xaxis=dict(tickmode='linear', dtick=1),
                        yaxis=dict(title="Total Annual Benefit ($)"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Compare costs with and without environmental benefits
                env_impact_df = pd.DataFrame({
                    "Year": revenue_df["Year"],
                    "Bill Impact (No Env. Benefits)": revenue_df["BillImpactPerCustomer"] + (revenue_df["EnvironmentalBenefit"] / params["CustomerBase"]),
                    "Bill Impact (With Env. Benefits)": revenue_df["BillImpactPerCustomer"],
                    "Environmental Benefit per Customer": revenue_df["EnvironmentalBenefit"] / params["CustomerBase"]
                })
                
                # Bill impact comparison
                fig = px.line(
                    env_impact_df,
                    x="Year",
                    y=["Bill Impact (No Env. Benefits)", "Bill Impact (With Env. Benefits)"],
                    title="Bill Impact With and Without Environmental Benefits",
                    labels={"value": "Bill Impact ($)", "Year": "Year", "variable": "Scenario"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Bill Impact ($)"),
                    hovermode="x unified",
                    legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total Environmental Benefits", 
                        f"${summary_stats['Total Environmental Benefits']/1e6:.1f}M",
                        help="Total environmental benefits over 15 years"
                    )
                
                with col2:
                    total_costs = summary_stats["Total Revenue Requirement"]
                    net_costs = summary_stats["Net Cost After Environmental Benefits"]
                    st.metric(
                        "Net Cost After Benefits", 
                        f"${net_costs/1e6:.1f}M",
                        f"-{(total_costs - net_costs)/total_costs*100:.1f}%",
                        help="Total costs after accounting for environmental benefits"
                    )
                
                with col3:
                    avg_bill_reduction = revenue_df["EnvironmentalBenefit"].sum() / params["CustomerBase"] / 15
                    st.metric(
                        "Average Annual Bill Reduction", 
                        f"${avg_bill_reduction:.2f}",
                        help="Average annual bill reduction per customer due to environmental benefits"
                    )
                
                # Key insights
                st.markdown("""
                ### Key Insights on Environmental Benefits
                
                - Environmental benefits increase over time as more chargers are deployed and EV adoption grows.
                - When these benefits are monetized and included in the RAB model, they can significantly reduce the bill impact.
                - **Policy Implication**: If the goal is to reduce emissions, the monetized environmental benefits should be explicitly included in the regulatory framework.
                """)
            else:
                st.info("Environmental benefits analysis is disabled. Enable it by checking 'Include Environmental Benefits' in the sidebar.")
        
        # Public/Private Balance Tab
        with tech_viz_tabs[3]:
            # Calculate optimal mix
            optimal_mix = calculate_optimal_charger_mix(
                years=15,
                public_chargers=rollout_df["CumulativeChargers"].values,
                private_market_chargers=competitiveness_df["Private_Market_With_RAB"].values,
                optimal_ratio=params["PublicPrivateRatio"]
            )
            
            # Create DataFrame for visualization
            mix_df = pd.DataFrame({
                "Year": list(range(1, 16)),
                "Public Chargers": [optimal_mix[y]["public_chargers"] for y in range(1, 16)],
                "Private Chargers": [optimal_mix[y]["private_chargers"] for y in range(1, 16)],
                "Actual Ratio": [optimal_mix[y]["actual_ratio"] for y in range(1, 16)],
                "Optimal Ratio": [optimal_mix[y]["optimal_ratio"] for y in range(1, 16)],
                "Optimality Score": [optimal_mix[y]["optimality_score"] for y in range(1, 16)],
                "Assessment": [optimal_mix[y]["imbalance"] for y in range(1, 16)]
            })
            
            # Charger mix stacked bar chart
            fig = px.bar(
                mix_df,
                x="Year",
                y=["Public Chargers", "Private Chargers"],
                title="Mix of Public and Private Chargers",
                labels={"value": "Number of Chargers", "Year": "Year", "variable": "Charger Type"},
                barmode="stack"
            )
            
            fig.update_layout(
                height=500,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Number of Chargers"),
                hovermode="x unified",
                legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Actual vs. optimal ratio
                fig = px.line(
                    mix_df,
                    x="Year",
                    y=["Actual Ratio", "Optimal Ratio"],
                    title="Actual vs. Optimal Public/Private Ratio",
                    labels={"value": "Ratio", "Year": "Year", "variable": ""},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Public/Private Ratio"),
                    hovermode="x unified",
                    legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Optimality score
                fig = px.line(
                    mix_df,
                    x="Year",
                    y="Optimality Score",
                    title="Market Balance Optimality Score",
                    labels={"Optimality Score": "Score (1.0 = Optimal)", "Year": "Year"},
                    markers=True
                )
                
                fig.update_layout(
                    height=400,
                    xaxis=dict(tickmode='linear', dtick=1),
                    yaxis=dict(title="Optimality Score (1.0 = Optimal)"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Market balance assessment
            st.subheader("Market Balance Assessment")
            
            # Display assessment as a table
            assessment_df = mix_df[["Year", "Assessment", "Actual Ratio", "Optimal Ratio", "Optimality Score"]]
            assessment_df.set_index("Year", inplace=True)
            st.dataframe(assessment_df, use_container_width=True)
            
            # Key insights
            st.markdown("""
            ### Key Insights on Public/Private Balance
            
            - The optimal mix of public and private chargers depends on various factors, including geographic coverage, equity of access, and market efficiency.
            - An imbalance can lead to inefficiencies: too many public chargers may crowd out private investment, while too few may leave gaps in coverage.
            - **Policy Implication**: The regulatory framework should aim for an optimal balance, perhaps through targeted subsidies or geographic planning rather than a blanket approach.
            """)
            
            # Display final year assessment prominently
            final_assessment = mix_df.iloc[-1]["Assessment"]
            final_score = mix_df.iloc[-1]["Optimality Score"]
            
            st.info(f"**Final Assessment (Year 15)**: {final_assessment} (Optimality Score: {final_score:.2f})")
        
        # Overall Technology and Environment Insights
        st.subheader("Overall Technology and Environment Insights")
        st.markdown("""
        The analysis of technology evolution, demand patterns, environmental benefits, and market balance reveals important considerations for the EV charger RAB model:
        
        1. **Technology Risk**: EV charging technology is evolving rapidly, creating risks of obsolescence and stranded assets.
        2. **Utilization Uncertainty**: Charger utilization depends heavily on EV adoption rates, which are uncertain.
        3. **Environmental Benefits**: When properly accounted for, these benefits can significantly improve the cost-benefit analysis.
        4. **Market Balance**: Finding the optimal balance between public and private provision is critical for efficiency.
        
        These factors suggest that a more flexible, targeted approach to EV charger deployment might be more effective than a large-scale RAB model.
        """)
    
    # ===============================
    # Tab 4: Risk Assessment
    # ===============================
    with tabs[4]:
        st.subheader("Monte Carlo Simulation - Risk Assessment")
        st.markdown("""
        The Monte Carlo simulation runs the model hundreds of times with different parameter combinations sampled from probability 
        distributions. This helps understand the range of possible outcomes and identify key risk factors.
        """)
        
        # Parameters for Monte Carlo simulation
        mc_col1, mc_col2 = st.columns(2)
        
        with mc_col1:
            n_simulations = st.slider(
                "Number of Simulations", 
                min_value=100, 
                max_value=1000, 
                value=500, 
                step=100,
                help="More simulations provide better estimates but take longer to run"
            )
        
        with mc_col2:
            run_simulation = st.button("Run Monte Carlo Simulation")
        
        # Run Monte Carlo simulation if button clicked
        if run_simulation:
            with st.spinner("Running Monte Carlo simulation..."):
                mc_results = run_monte_carlo_simulation(n_simulations)
                
                # Store results in session state for persistence
                st.session_state.mc_results = mc_results
        
        # Display Monte Carlo results if available
        if hasattr(st.session_state, 'mc_results') and st.session_state.mc_results is not None:
            mc_results = st.session_state.mc_results
            
            # Summary statistics of Monte Carlo results
            st.subheader("Simulation Results Summary")
            
            # Display key statistics
            mc_summary = pd.DataFrame({
                "Metric": [
                    "Average Bill Impact ($)",
                    "Peak Bill Impact ($)",
                    "Cumulative Bill Impact ($)",
                    "NPV of Bill Impacts ($)",
                    "Regressivity Ratio"
                ],
                "Min": [
                    mc_results["avg_bill_impact"].min(),
                    mc_results["peak_bill_impact"].min(),
                    mc_results["cumulative_bill"].min(),
                    mc_results["npv_bill_impact"].min(),
                    mc_results["regressive_ratio"].min()
                ],
                "Mean": [
                    mc_results["avg_bill_impact"].mean(),
                    mc_results["peak_bill_impact"].mean(),
                    mc_results["cumulative_bill"].mean(),
                    mc_results["npv_bill_impact"].mean(),
                    mc_results["regressive_ratio"].mean()
                ],
                "Median": [
                    mc_results["avg_bill_impact"].median(),
                    mc_results["peak_bill_impact"].median(),
                    mc_results["cumulative_bill"].median(),
                    mc_results["npv_bill_impact"].median(),
                    mc_results["regressive_ratio"].median()
                ],
                "90th Percentile": [
                    mc_results["avg_bill_impact"].quantile(0.9),
                    mc_results["peak_bill_impact"].quantile(0.9),
                    mc_results["cumulative_bill"].quantile(0.9),
                    mc_results["npv_bill_impact"].quantile(0.9),
                    mc_results["regressive_ratio"].quantile(0.9)
                ],
                "Max": [
                    mc_results["avg_bill_impact"].max(),
                    mc_results["peak_bill_impact"].max(),
                    mc_results["cumulative_bill"].max(),
                    mc_results["npv_bill_impact"].max(),
                    mc_results["regressive_ratio"].max()
                ]
            })
             
            # Format the summary table
            for col in mc_summary.columns[1:]:
                mc_summary[col] = mc_summary[col].apply(lambda x: f"{x:.2f}")
             
            st.table(mc_summary)
    
    # ===============================
    # Tab 5: Scenario Comparison
    # ===============================
    with tabs[5]:
        st.subheader("Scenario Comparison Analysis")
        st.markdown("""
        This analysis compares various scenarios to understand the range of potential outcomes under different assumptions.
        Scenarios include both optimistic and pessimistic cases to bound the analysis.
        """)
        
        # Run scenario comparisons
        scenario_results, all_revenue_df, all_distribution_df, all_competition_df = run_comparison_scenarios()
        
        # Display scenario results summary
        st.subheader("Scenario Summary Metrics")
        
        # Format the summary table for display
        display_cols = [
            "Average Annual Bill Impact", 
            "Peak Annual Bill Impact", 
            "Cumulative Bill Impact/Customer",
            "NPV of Bill Impacts",
            "Final Year Efficiency Factor"
        ]
        
        display_df = scenario_results[display_cols].copy()
        
        # Format numbers
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}" if "Bill" in col or "NPV" in col else f"{x:.2f}x")
        
        st.table(display_df)
        
        # Create tabs for different scenario comparisons
        scenario_tabs = st.tabs([
            "Bill Impact Comparison", 
            "Regressivity Comparison", 
            "Market Impact Comparison"
        ])
        
        # Bill Impact Comparison Tab
        with scenario_tabs[0]:
            st.subheader("Annual Bill Impact by Scenario")
            
            # Line chart of bill impacts by scenario
            fig = px.line(
                all_revenue_df,
                x="Year",
                y="BillImpactPerCustomer",
                color="Scenario",
                title="Annual Bill Impact per Customer by Scenario",
                labels={
                    "BillImpactPerCustomer": "Bill Impact ($)",
                    "Year": "Year"
                },
                markers=True
            )
            
            # Create a custom hovertemplate to simplify tooltips
            fig.update_traces(
                hovertemplate="Year: %{x}<br>" +
                              "Scenario: %{fullData.name}<br>" +
                              "Bill Impact: $%{y:.2f}<br>" +
                              "<extra></extra>"
            )
            
            fig.update_layout(
                height=500,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Annual Bill Impact ($)"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Cumulative bill impact chart
            fig = px.line(
                all_revenue_df,
                x="Year",
                y="CumulativeBillImpact",
                color="Scenario",
                title="Cumulative Bill Impact per Customer by Scenario",
                labels={
                    "CumulativeBillImpact": "Cumulative Bill Impact ($)",
                    "Year": "Year"
                },
                markers=True
            )
            
            fig.update_layout(
                height=500,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Cumulative Bill Impact ($)"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Efficiency factor comparison
            fig = px.line(
                all_revenue_df,
                x="Year",
                y="CurrentEfficiencyFactor",
                color="Scenario",
                title="Efficiency Factor Evolution by Scenario",
                labels={
                    "CurrentEfficiencyFactor": "Efficiency Factor",
                    "Year": "Year"
                },
                markers=True
            )
            
            fig.update_layout(
                height=400,
                xaxis=dict(tickmode='linear', dtick=1),
                yaxis=dict(title="Efficiency Factor (multiplier)"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Regressivity Comparison Tab
        with scenario_tabs[1]:
            st.subheader("Distributional Impact by Scenario")
            
            # Calculate regressivity by scenario
            scenario_reg = {}
            
            for scenario, group in all_distribution_df.groupby("Scenario"):
                q1_impact = group.loc[group["quintile"] == "Q1", "impact_pct_income"].values[0]
                q5_impact = group.loc[group["quintile"] == "Q5", "impact_pct_income"].values[0]
                ratio = q1_impact / q5_impact
                
                scenario_reg[scenario] = {
                    "Q1 Impact": q1_impact,
                    "Q5 Impact": q5_impact,
                    "Regressivity Ratio": ratio
                }
            
            reg_df = pd.DataFrame.from_dict(scenario_reg, orient="index")
            
            # Bar chart of regressivity ratios
            fig = px.bar(
                reg_df,
                y=reg_df.index,
                x="Regressivity Ratio",
                title="Regressivity Ratio by Scenario",
                labels={
                    "Regressivity Ratio": "Regressivity Ratio (Q1/Q5 Impact)",
                    "y": "Scenario"
                },
                text="Regressivity Ratio"
            )
            
            fig.update_traces(
                texttemplate="%{x:.2f}x",
                textposition="inside"
            )
            
            fig.update_layout(
                height=400,
                yaxis=dict(title="", categoryorder="total ascending"),
                xaxis=dict(title="Regressivity Ratio (higher is more regressive)")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Impact by income quintile for each scenario
            quintile_impact_df = []
            
            for scenario, group in all_distribution_df.groupby("Scenario"):
                for _, row in group.iterrows():
                    quintile_impact_df.append({
                        "Scenario": scenario,
                        "Income Quintile": row["quintile"],
                        "Impact (% of Income)": row["impact_pct_income"]
                    })
            
            quintile_impact_df = pd.DataFrame(quintile_impact_df)
            
            # Create grouped bar chart
            fig = px.bar(
                quintile_impact_df,
                x="Income Quintile",
                y="Impact (% of Income)",
                color="Scenario",
                barmode="group",
                title="Bill Impact as % of Income by Quintile and Scenario",
                text_auto='.4f'
            )
            
            fig.update_layout(
                height=500,
                yaxis=dict(title="Impact (% of Annual Income)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights on regressivity across scenarios
            st.markdown("""
            ### Key Insights on Regressivity Across Scenarios
            
            - **All scenarios are regressive**, with low-income households disproportionately impacted
            - Higher cost scenarios increase the absolute burden but maintain similar regressivity ratios
            - The regressivity is structural, stemming from the socialization of costs across all customers
            
            **Alternative approaches** that use targeted subsidies or user-pays models would reduce this inequitable impact.
            """)
        
        # Market Impact Comparison Tab
        with scenario_tabs[2]:
            st.subheader("Market Impact by Scenario")
            
            # Filter to relevant scenarios for market impact
            market_scenarios = ["Base Case", "High Cost Case", "Low Cost Case", "Private Market Impact"]
            filtered_comp_df = all_competition_df[all_competition_df["Scenario"].isin(market_scenarios)]
            
            # Final year market displacement by scenario
            final_year = filtered_comp_df["Year"].max()
            
            market_impact_df = []
            
            for scenario, group in filtered_comp_df.groupby("Scenario"):
                final_data = group[group["Year"] == final_year]
                
                baseline = final_data["Private_Market_Baseline"].values[0]
                with_rab = final_data["Private_Market_With_RAB"].values[0]
                rab_chargers = final_data["RAB_Cumulative_Chargers"].values[0]
                total_chargers = final_data["Total_Market_Chargers"].values[0]
                
                displacement = baseline - with_rab
                displacement_pct = displacement / baseline * 100
                
                market_impact_df.append({
                    "Scenario": scenario,
                    "Private Market Baseline": baseline,
                    "Private Market with RAB": with_rab,
                    "Private Market Displaced": displacement,
                    "Displacement (%)": displacement_pct,
                    "RAB Chargers": rab_chargers,
                    "Total Market Chargers": total_chargers
                })
            
            market_impact_df = pd.DataFrame(market_impact_df)
            
            # Bar chart of market displacement
            fig = px.bar(
                market_impact_df,
                x="Scenario",
                y=["Private Market with RAB", "Private Market Displaced", "RAB Chargers"],
                title="Market Composition in Year 15 by Scenario",
                labels={
                    "value": "Number of Chargers",
                    "Scenario": "Scenario",
                    "variable": "Market Segment"
                },
                barmode="stack"
            )
            
            fig.update_layout(
                height=500,
                yaxis=dict(title="Number of Chargers"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            
            # Update legend names
            newnames = {
                "Private Market with RAB": "Private Market (remaining)",
                "Private Market Displaced": "Private Market (displaced)",
                "RAB Chargers": "RAB Model Chargers"
            }
            
            fig.for_each_trace(
                lambda t: t.update(name = newnames[t.name] if t.name in newnames else t.name)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Displacement percentage chart
            fig = px.bar(
                market_impact_df,
                x="Scenario",
                y="Displacement (%)",
                title="Private Market Displacement by Scenario",
                labels={
                    "Displacement (%)": "Displacement (%)",
                    "Scenario": "Scenario"
                },
                text="Displacement (%)"
            )
            
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="inside"
            )
            
            fig.update_layout(
                height=400,
                yaxis=dict(title="Private Market Displacement (%)")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # CapEx innovation gap chart
            # Get year 15 data for all scenarios
            y15_data = filtered_comp_df[filtered_comp_df["Year"] == 15]
            
            # Calculate innovation gap
            y15_data["CapEx_Innovation_Gap_Pct"] = (
                (y15_data["RAB_CapEx"] - y15_data["Competitive_Market_CapEx"]) / 
                y15_data["RAB_CapEx"] * 100
            )
            
            # Bar chart of innovation gap
            fig = px.bar(
                y15_data,
                x="Scenario",
                y="CapEx_Innovation_Gap_Pct",
                title="Year 15 CapEx Innovation Gap by Scenario",
                labels={
                    "CapEx_Innovation_Gap_Pct": "Innovation Gap (%)",
                    "Scenario": "Scenario"
                },
                text="CapEx_Innovation_Gap_Pct"
            )
            
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="inside"
            )
            
            fig.update_layout(
                height=400,
                yaxis=dict(title="CapEx Innovation Gap (%)")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights on market impacts
            st.markdown("""
            ### Key Insights on Market Impacts Across Scenarios
            
            - Even in the most optimistic RAB scenarios, significant private market displacement occurs
            - Innovation gaps are consistent across scenarios, with RAB costs remaining higher than competitive market
            - The total number of chargers deployed may be comparable, but with higher overall socialized costs
            
            **Alternative approaches** that focus on enabling private investment while ensuring equitable access and 
            deployment in underserved areas would yield better market outcomes.
            """)
    
    # Footer with information about the enhanced model
    st.markdown("""
    ---
    ### About the EV Charger RAB Model
    
    This model evaluates the RAB approach through several critical factors:
    
    1. **Operational Efficiency**: Modelling how distribution companies operate new technologies
    2. **Regressive Bill Impacts**: Analysing how costs affect different income households
    3. **Market Effects**: Quantifying private investment and innovation impacts
    4. **Risk Assessment**: Using Monte Carlo simulation to understand the range of possible outcomes
    5. **Technology Evolution**: Accounting for technological obsolescence over time
    6. **Environmental Benefits**: Quantifying environmental benefits in the analysis
    
    For more information on methodology and assumptions, see the documentation.
    """)


# ========================
# 5. Run the App
# ========================
if __name__ == "__main__":
    main()
