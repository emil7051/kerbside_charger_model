"""
Parameters for the Kerbside Model app.
"""

# =============================================
# App Configuration
# =============================================

# Page configuration
PAGE_TITLE = "Kerbside EV Charger Model"
PAGE_ICON = "🔌"
PAGE_LAYOUT = "wide"

# Tab names
TABS = [
    "Financial Overview", 
    "Asset Evolution",
    "Distributional Impact",
    "Market Effects",
    "Monte Carlo Analysis"
]

# =============================================
# Core Model Parameters
# =============================================

# Time period
DEFAULT_YEARS = 15  # Standard 15-year analysis period

# Deployment parameters
DEFAULT_CHARGERS_PER_YEAR = 6000  # Default annual charger deployment
DEFAULT_DEPLOYMENT_YEARS = 5  # Default deployment period
DEFAULT_DEPLOYMENT_DELAY = 1.0  # Default deployment delay factor (>1 means slower)

# Financial parameters
DEFAULT_CAPEX_PER_CHARGER = 6000  # Default capital cost per charger
DEFAULT_OPEX_PER_CHARGER = 500   # Default operating cost per charger
DEFAULT_ASSET_LIFE = 8    # Default asset lifetime in years
DEFAULT_WACC = 0.0595     # Default Weighted Average Cost of Capital (5.95%)

# Third-party revenue parameters
DEFAULT_REVENUE_PER_CHARGER = 100  # Default third-party revenue per charger (NOTE: Used in KerbsideModel but not in UI inputs)

# Customer parameters
DEFAULT_CUSTOMER_BASE = 1800000  # Default utility customer base

# Efficiency parameters
DEFAULT_EFFICIENCY = 1.0  # Default efficiency factor (1.0 = fully efficient)
DEFAULT_EFFICIENCY_DEGRADATION = 0.0  # Default annual efficiency degradation
DEFAULT_TECH_OBSOLESCENCE_RATE = 0.0  # Default technology obsolescence rate

# Private market parameters
DEFAULT_INITIAL_PRIVATE_CHARGERS = 1000  # Initial private market chargers
DEFAULT_PRIVATE_GROWTH_RATE = 0.2  # Annual growth rate of private market
DEFAULT_MARKET_DISPLACEMENT = 0.0  # Default market displacement rate
DEFAULT_SATURATION_TIME_CONSTANT = 5.0  # Time constant for market saturation effect

# RAB obsolescence calculation
DEFAULT_OBSOLESCENCE_FACTOR = 0.1  # Factor for obsolescence writeoff calculation

# Income data parameters
DEFAULT_MEDIAN_INCOME = 92856  # Median household income

# Income quintiles as a fraction of median income
INCOME_QUINTILES = {
    "Quintile 1 (Lowest)": 0.27, 
    "Quintile 2": 0.6,
    "Quintile 3 (Median)": 1.0,
    "Quintile 4": 1.54,
    "Quintile 5 (Highest)": 3.1
}

# Energy burden by income quintile (% of income spent on energy)
ENERGY_BURDEN = {
    "Quintile 1 (Lowest)": 0.085,  # 8.5% of income
    "Quintile 2": 0.065,
    "Quintile 3 (Median)": 0.045,
    "Quintile 4": 0.025,
    "Quintile 5 (Highest)": 0.015
}

# EV ownership likelihood multiplier
EV_LIKELIHOOD = {
    "Quintile 1 (Lowest)": 0.01,
    "Quintile 2": 0.4,
    "Quintile 3 (Median)": 0.8,
    "Quintile 4": 1.2,
    "Quintile 5 (Highest)": 1.6
}

# =============================================
# Monte Carlo Simulation Parameters
# =============================================

# Default random seed for reproducibility
DEFAULT_RANDOM_SEED = 42

# Default parameter ranges for Monte Carlo simulation
DEFAULT_PARAMETER_RANGES = {
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