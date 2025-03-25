"""
Sidebar component for parameter input in the Kerbside Model app.
"""

import streamlit as st
from src.utils.parameters import (
    DEFAULT_CHARGERS_PER_YEAR,
    DEFAULT_DEPLOYMENT_YEARS,
    DEFAULT_DEPLOYMENT_DELAY,
    DEFAULT_CAPEX_PER_CHARGER,
    DEFAULT_OPEX_PER_CHARGER,
    DEFAULT_ASSET_LIFE,
    DEFAULT_WACC,
    DEFAULT_EFFICIENCY,
    DEFAULT_EFFICIENCY_DEGRADATION,
    DEFAULT_TECH_OBSOLESCENCE_RATE,
    DEFAULT_MARKET_DISPLACEMENT
)
from src.utils.conversion_utils import percentage_to_decimal

def create_sidebar_parameters():
    """
    Create the sidebar with parameter input sections.
    
    Returns:
        dict: Dictionary of model parameters
    """
    with st.sidebar:
        st.header("Model Parameters")
        
        # Create tabs for Deployment and Financial parameters
        deployment_tab, financial_tab = st.tabs(["Deployment", "Financial"])
        
        # Deployment Parameters Tab
        with deployment_tab:
            chargers_per_year = st.number_input(
                "Chargers per Year (#/year)",
                min_value=1000,
                max_value=10000,
                value=DEFAULT_CHARGERS_PER_YEAR,
                step=200,
                help="Number of chargers deployed annually"
            )
            
            deployment_years = st.slider(
                "Deployment Period (years)",
                min_value=1,
                max_value=10,
                value=DEFAULT_DEPLOYMENT_YEARS,
                step=1,
                help="Total number of years over which chargers are deployed"
            )
            
            deployment_delay = st.slider(
                "Deployment Delay Factor",
                min_value=0.5,
                max_value=2.0,
                value=DEFAULT_DEPLOYMENT_DELAY,
                step=0.1,
                help="Value >1 means slower deployment, <1 means faster deployment"
            )
            
            tech_obsolescence_rate = st.slider(
                "Technology Obsolescence Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=DEFAULT_TECH_OBSOLESCENCE_RATE * 100,
                step=1.0,
                format="%.1f%%",
                help="Annual rate at which technology becomes obsolete"
            )
            
            market_displacement = st.slider(
                "Market Displacement Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=DEFAULT_MARKET_DISPLACEMENT * 100,
                step=5.0,
                format="%.1f%%",
                help="Rate at which RAB displaces private market"
            )
        
        # Financial Parameters Tab
        with financial_tab:
            capex_per_charger = st.number_input(
                "CapEx per Charger ($)",
                min_value=1000,
                max_value=10000,
                value=DEFAULT_CAPEX_PER_CHARGER,
                step=100,
                help="One-time capital expenditure per charger"
            )
            
            opex_per_charger = st.number_input(
                "OpEx per Charger ($/year)",
                min_value=100,
                max_value=2000,
                value=DEFAULT_OPEX_PER_CHARGER,
                step=50,
                help="Annual operating expenditure per charger"
            )
            
            asset_life = st.slider(
                "Asset Life (Years)",
                min_value=3,
                max_value=15,
                value=DEFAULT_ASSET_LIFE,
                step=1,
                help="Expected lifetime of charger assets"
            )
            
            wacc = st.slider(
                "WACC (%)",
                min_value=5.50,
                max_value=6.50,
                value=DEFAULT_WACC * 100,
                step=0.10,
                format="%.2f",
                help="Weighted Average Cost of Capital"
            )
            
            efficiency = st.slider(
                "Efficiency Factor",
                min_value=0.5,
                max_value=1.5,
                value=DEFAULT_EFFICIENCY,
                step=0.05,
                help="Operational efficiency multiplier (1.0 = fully efficient, >1.0 = inefficient)"
            )
            
            efficiency_degradation = st.slider(
                "Annual Efficiency Change (%)",
                min_value=-5.0,
                max_value=10.0,
                value=DEFAULT_EFFICIENCY_DEGRADATION * 100,
                step=1.0,
                format="%.1f%%",
                help="Annual rate at which efficiency changes (positive = worsens, negative = improves)"
            )
        
        # Add a small note about automatic updates
        st.info("Model updates automatically when parameters change")
    
    # Convert percentage values to decimal for model using the utility function
    wacc_decimal = percentage_to_decimal(wacc)
    efficiency_degradation_decimal = percentage_to_decimal(efficiency_degradation)
    tech_obsolescence_decimal = percentage_to_decimal(tech_obsolescence_rate)
    market_displacement_decimal = percentage_to_decimal(market_displacement)
    
    # Set up parameter dictionary
    model_params = {
        # Deployment parameters
        "chargers_per_year": chargers_per_year,
        "deployment_years": deployment_years,
        "deployment_delay": deployment_delay,
        
        # Financial parameters
        "capex_per_charger": capex_per_charger,
        "opex_per_charger": opex_per_charger,
        "asset_life": asset_life,
        "wacc": wacc_decimal,
        
        # Efficiency parameters
        "efficiency": efficiency,
        "efficiency_degradation": efficiency_degradation_decimal,
        "tech_obsolescence_rate": tech_obsolescence_decimal,
        "market_displacement": market_displacement_decimal
    }
    
    return model_params 