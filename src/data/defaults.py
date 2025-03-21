"""Default parameter sets for the EV charger model."""

from dataclasses import dataclass
from typing import Dict, Any

# Base parameters that apply to all models
BASE_PARAMS = {
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
}

# Efficiency model parameters
EFFICIENCY_PARAMS = {
    "EfficiencyFactor": 1.0,  # Default is no inefficiency premium
    "EfficiencyDegradation": 0.0,  # Annual degradation in efficiency
    "DeploymentDelay": 1.0,  # Deployment time multiplier (1.0 = no delay)
    "CostEscalation": 1.0,  # Cost escalation factor (1.0 = no escalation)
    "OperationalEfficiency": 1.0,  # How efficiently chargers are operated (1.0 = fully efficient)
}

# Competitive market parameters
COMPETITIVE_PARAMS = {
    "PrivateMarketDisplacement": 0.0,  # Percentage of private market displaced
    "InnovationRate": 0.02,  # Annual innovation rate in competitive market
    "MonopolyInnovationRate": 0.01,  # Annual innovation rate in monopoly market
    "BaselinePrivateGrowth": 0.1,  # Annual growth rate of private charger deployment
    "InitialPrivateChargers": 1000,  # Initial number of private chargers
}

# Technical parameters
TECHNICAL_PARAMS = {
    "TechObsolescenceRate": 0.05,  # Technology obsolescence rate
    "DemandUtilisation": 0.7,  # Average utilisation of chargers
    "UtilisationGrowthRate": 0.05,  # Annual growth in utilisation
    "EVAdoptionRate": 0.15,  # Annual growth rate of EV adoption
}

# Environmental parameters
ENVIRONMENTAL_PARAMS = {
    "EnvironmentalBenefitPerCharger": 250,  # Annual environmental benefit ($) per charger
    "IncludeEnvironmentalBenefits": False,  # Whether to include environmental benefits
    "CO2PerKWh": 0.2,  # kg of CO2 per kWh
    "KWhPerChargerYear": 5000,  # kWh delivered per charger per year
}

# Income distribution data for distributional analysis
INCOME_QUINTILES = {
    "Q1": {"income": 25000, "electricity_spend": 1200, "percent_of_population": 0.2},
    "Q2": {"income": 45000, "electricity_spend": 1400, "percent_of_population": 0.2},
    "Q3": {"income": 65000, "electricity_spend": 1600, "percent_of_population": 0.2},
    "Q4": {"income": 95000, "electricity_spend": 1900, "percent_of_population": 0.2},
    "Q5": {"income": 165000, "electricity_spend": 2500, "percent_of_population": 0.2},
}

# Combine all parameter sets
DEFAULT_PARAMS = {
    **BASE_PARAMS,
    **EFFICIENCY_PARAMS,
    **COMPETITIVE_PARAMS,
    **TECHNICAL_PARAMS,
    **ENVIRONMENTAL_PARAMS,
} 