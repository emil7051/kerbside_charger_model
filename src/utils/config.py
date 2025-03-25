"""
Configuration file for the Kerbside EV Charger Economic Model.

This module contains environment-specific configuration settings that can be
modified without changing the application code.
"""

# =============================================
# Application Configuration
# =============================================

# Data file paths (can be absolute or relative to application root)
DATA_PATH = "data"

# Default file paths for data imports/exports
DEFAULT_EXPORT_PATH = "exports"

# Environment-specific settings
DEBUG_MODE = False
SHOW_DETAILED_ERRORS = True

# =============================================
# User Interface Configuration
# =============================================

# Charts and visualization settings
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 800
DEFAULT_COLOR_SCHEME = "Blues"
CHART_DECIMALS = 2

# Theme-related settings
PRIMARY_COLOR = "#1E88E5"
SECONDARY_COLOR = "#ff9e00"
BACKGROUND_COLOR = "#f0f2f6"

# =============================================
# Model Configuration
# =============================================

# Computation settings
MAX_MONTE_CARLO_SIMULATIONS = 1000
USE_PARALLEL_COMPUTATION = False  # Set to True to enable parallel computation for Monte Carlo
N_PARALLEL_JOBS = 4  # Number of parallel jobs for Monte Carlo simulation

# =============================================
# Data Export Configuration
# =============================================

# Export settings
DEFAULT_EXPORT_FORMAT = "csv"
AVAILABLE_EXPORT_FORMATS = ["csv", "excel", "json"]

# Number formatting for exports
DECIMAL_PLACES = 2
CURRENCY_FORMAT = "${:.2f}"
PERCENTAGE_FORMAT = "{:.2f}%" 