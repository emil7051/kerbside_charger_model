"""
Streamlit app for the Kerbside EV Charger Model.

This app provides an interactive interface for the simplified EV charger model.
"""

import streamlit as st

from src.model.kerbside_model import KerbsideModel
from src.utils.constants import (
    PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT, TABS
)
from src.components.sidebar import create_sidebar_parameters
from src.components.financial_tab import render_financial_tab
from src.components.asset_tab import render_asset_tab
from src.components.distributional_tab import render_distributional_tab
from src.components.market_tab import render_market_tab
from src.components.monte_carlo_tab import render_monte_carlo_tab

# Set page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=PAGE_LAYOUT
)

# App title and description
st.title("Kerbside EV Charger Economic Model")
st.markdown("""
This app analyzes the economic implications of deploying electric vehicle (EV) chargers 
through a Regulated Asset Base (RAB) approach. Adjust the parameters to see how they
affect the economic outcomes.
""")

# Create sidebar for parameters
model_params, run_button = create_sidebar_parameters()

# Initialize and run the model
if 'model_results' not in st.session_state or run_button:
    with st.spinner("Running model calculations..."):
        model = KerbsideModel(model_params)
        model_results = model.run()
        st.session_state.model_results = model_results
        st.session_state.model = model
else:
    model_results = st.session_state.model_results
    model = st.session_state.model

# Create tabs for different result categories
tabs = st.tabs(TABS)

# Financial Overview Tab
with tabs[0]:
    render_financial_tab(model_results)

# Asset Evolution Tab
with tabs[1]:
    render_asset_tab(model_results)

# Distributional Impact Tab
with tabs[2]:
    render_distributional_tab(model_results)

# Market Effects Tab
with tabs[3]:
    render_market_tab(model_results)

# Monte Carlo Analysis Tab
with tabs[4]:
    render_monte_carlo_tab(model_results, model)

# Footer with additional information
st.markdown("---")
st.markdown("""
**About this model**: This models the implementation of the EV charger RAB economic model.
It calculates the impact of deploying EV chargers on houshehold energy bills, as well as the impact on private investment 
and market competition.
""") 