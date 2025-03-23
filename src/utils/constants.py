"""
Constants for the Kerbside Model app.
"""

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

# Income data constants
MEDIAN_INCOME = 65000
INCOME_QUINTILES = {
    "Quintile 1 (Lowest)": 0.35,  # 35% of median income
    "Quintile 2": 0.7,
    "Quintile 3 (Median)": 1.0,
    "Quintile 4": 1.4,
    "Quintile 5 (Highest)": 2.5
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