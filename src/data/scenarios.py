"""Predefined scenario configurations for the EV charger model."""

from .defaults import DEFAULT_PARAMS

# Baseline scenario uses default parameters
BASELINE_SCENARIO = DEFAULT_PARAMS.copy()

# High Efficiency scenario
HIGH_EFFICIENCY_SCENARIO = DEFAULT_PARAMS.copy()
HIGH_EFFICIENCY_SCENARIO.update({
    "EfficiencyFactor": 0.9,  # 10% more efficient than baseline
    "EfficiencyDegradation": 0.0,
    "OperationalEfficiency": 1.1,  # 10% better operational efficiency
    "InnovationRate": 0.03,
    "MonopolyInnovationRate": 0.02,
})

# Low Efficiency scenario
LOW_EFFICIENCY_SCENARIO = DEFAULT_PARAMS.copy()
LOW_EFFICIENCY_SCENARIO.update({
    "EfficiencyFactor": 1.2,  # 20% less efficient than baseline
    "EfficiencyDegradation": 0.02,  # 2% annual degradation
    "OperationalEfficiency": 0.8,  # 20% worse operational efficiency
    "DeploymentDelay": 1.2,  # 20% delay in deployment
    "CostEscalation": 1.1,  # 10% cost escalation
})

# Competitive Market scenario
COMPETITIVE_MARKET_SCENARIO = DEFAULT_PARAMS.copy()
COMPETITIVE_MARKET_SCENARIO.update({
    "PrivateMarketDisplacement": 0.0,  # No displacement of private market
    "InnovationRate": 0.04,  # Higher innovation rate
    "MonopolyInnovationRate": 0.02,  # Lower monopoly innovation
    "BaselinePrivateGrowth": 0.15,  # Higher private market growth
})

# Monopoly Market scenario
MONOPOLY_MARKET_SCENARIO = DEFAULT_PARAMS.copy()
MONOPOLY_MARKET_SCENARIO.update({
    "PrivateMarketDisplacement": 0.5,  # 50% displacement of private market
    "InnovationRate": 0.02,
    "MonopolyInnovationRate": 0.01,
    "BaselinePrivateGrowth": 0.05,  # Lower private market growth
})

# Accelerated Deployment scenario
ACCELERATED_DEPLOYMENT_SCENARIO = DEFAULT_PARAMS.copy()
ACCELERATED_DEPLOYMENT_SCENARIO.update({
    "ChargersPerYear": 8000,  # More chargers per year
    "DeploymentDelay": 0.9,  # 10% faster deployment
    "EVAdoptionRate": 0.2,  # Higher EV adoption rate
    "DemandUtilisation": 0.8,  # Higher initial utilisation
})

# Environmental Benefits scenario
ENVIRONMENTAL_BENEFITS_SCENARIO = DEFAULT_PARAMS.copy()
ENVIRONMENTAL_BENEFITS_SCENARIO.update({
    "IncludeEnvironmentalBenefits": True,
    "EnvironmentalBenefitPerCharger": 350,  # Higher environmental benefit
    "CO2PerKWh": 0.15,  # Lower CO2 per kWh (greener grid)
    "KWhPerChargerYear": 6000,  # More kWh delivered per charger
})

# Dictionary of all scenarios
SCENARIOS = {
    "Baseline": BASELINE_SCENARIO,
    "High Efficiency": HIGH_EFFICIENCY_SCENARIO,
    "Low Efficiency": LOW_EFFICIENCY_SCENARIO,
    "Competitive Market": COMPETITIVE_MARKET_SCENARIO,
    "Monopoly Market": MONOPOLY_MARKET_SCENARIO,
    "Accelerated Deployment": ACCELERATED_DEPLOYMENT_SCENARIO,
    "Environmental Benefits": ENVIRONMENTAL_BENEFITS_SCENARIO,
} 