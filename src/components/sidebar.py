"""
Sidebar component for parameter input in the Kerbside Model app.
"""

import streamlit as st


def create_sidebar_parameters():
    """
    Create the sidebar with parameter input sections.
    
    Returns:
        dict: Dictionary of parameters
    """
    with st.sidebar:
        st.header("Model Parameters")
        
        # Create tabs for parameter categories
        param_tabs = st.tabs([
            "Deployment", 
            "Financial",
            "Efficiency", 
            "Market"
        ])
        
        # Deployment parameters
        with param_tabs[0]:
            chargers_per_year = st.number_input(
                "Chargers per Year (#/year)",
                min_value=1000,
                max_value=10000,
                value=6000,
                step=200,
                help="Number of chargers deployed annually"
            )
            
            deployment_years = st.slider(
                "Deployment Period (years)",
                min_value=1,
                max_value=10,
                value=5,
                step=1,
                help="Total number of years over which chargers are deployed"
            )
            
            deployment_delay = st.slider(
                "Deployment Delay Factor (multiplier)",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Multiplier affecting deployment speed (>1 means slower deployment)"
            )
        
        # Financial parameters
        with param_tabs[1]:
            capex_per_charger = st.number_input(
                "CapEx per Charger ($)",
                min_value=1000,
                max_value=10000,
                value=6000,
                step=100,
                help="One-time capital expenditure per charger"
            )
            
            opex_per_charger = st.number_input(
                "OpEx per Charger ($/year)",
                min_value=100,
                max_value=2000,
                value=500,
                step=50,
                help="Annual operating expenditure per charger"
            )
            
            asset_life = st.slider(
                "Asset Life (Years)",
                min_value=3,
                max_value=15,
                value=8,
                step=1,
                help="Expected lifetime of charger assets"
            )
            
            wacc = st.slider(
                "WACC (%)",
                min_value=5.50,
                max_value=6.50,
                value=5.95,
                step=0.10,
                format="%.1f",
                help="Weighted Average Cost of Capital"
            )
            
            cost_decline_rate = st.slider(
                "Annual Cost Decline (%)",
                min_value=0.0,
                max_value=8.0,
                value=0.0,
                step=0.5,
                format="%.1f",
                help="Annual percentage reduction in capital costs due to technology improvements"
            )
        
        # Efficiency parameters
        with param_tabs[2]:
            efficiency = st.slider(
                "Efficiency Factor (Multiplier)",
                min_value=0.5,
                max_value=1.5,
                value=1.0,
                step=0.05,
                help="Operational efficiency multiplier (1.0 = fully efficient, >1.0 = inefficient)"
            )
            
            efficiency_degradation = st.slider(
                "Annual Efficiency Degradation (%/year)",
                min_value=0.0,
                max_value=10.0,
                value=0.0,
                step=1.0,
                format="%.1f",
                help="Annual rate at which efficiency worsens"
            )
            
            tech_obsolescence_rate = st.slider(
                "Technology Obsolescence Rate (%/year)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=1.0,
                format="%.1f",
                help="Annual rate at which technology becomes obsolete"
            )
        
        # Market parameters
        with param_tabs[3]:
            market_displacement = st.slider(
                "Market Displacement Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                format="%.1f",
                help="Rate at which RAB displaces private market (0-100%)"
            )
        
        # Run model button
        run_button = st.button("Run Model", type="primary", use_container_width=True)
    
    # Convert percentage values to decimal for model
    wacc_decimal = wacc / 100.0
    cost_decline_decimal = cost_decline_rate / 100.0
    efficiency_degradation_decimal = efficiency_degradation / 100.0
    tech_obsolescence_decimal = tech_obsolescence_rate / 100.0
    market_displacement_decimal = market_displacement / 100.0
    
    # Set up parameter dictionary
    model_params = {
        "chargers_per_year": chargers_per_year,
        "deployment_years": deployment_years,
        "deployment_delay": deployment_delay,
        "capex_per_charger": capex_per_charger,
        "opex_per_charger": opex_per_charger,
        "asset_life": asset_life,
        "wacc": wacc_decimal,
        "cost_decline_rate": cost_decline_decimal,
        "efficiency": efficiency,
        "efficiency_degradation": efficiency_degradation_decimal,
        "tech_obsolescence_rate": tech_obsolescence_decimal,
        "market_displacement": market_displacement_decimal
    }
    
    return model_params, run_button 