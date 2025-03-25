"""
Financial Overview tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.parameters import DEFAULT_MEDIAN_INCOME, INCOME_QUINTILES
from src.utils.plot_utils import create_line_chart, create_stacked_area_chart
from src.utils.conversion_utils import format_currency

def render_financial_tab(model_results):
 
    st.header("Financial Overview")
    
    # Extract key results
    summary = model_results["summary"]
    revenue_df = model_results["revenue"]
    
    # Calculate actual income values from the quintile percentages
    income_quintiles_absolute = {
        quintile: DEFAULT_MEDIAN_INCOME * percentage
        for quintile, percentage in INCOME_QUINTILES.items()
    }
    
    # Calculate percentage impact on income for lowest and highest quintiles
    avg_bill_impact = summary['avg_bill_impact']
    
    lowest_quintile_income = income_quintiles_absolute["Quintile 1 (Lowest)"]
    highest_quintile_income = income_quintiles_absolute["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate regressivity ratio
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average Annual Bill Impact", 
            format_currency(summary['avg_bill_impact']),
            help="Average annual increase in household bills"
        )
        
        st.metric(
            "NPV of Bill Impacts", 
            format_currency(summary['npv_bill_impact']),
            help="Net present value of bill impacts over 15 years"
        )
    
    with col2:
        st.metric(
            "Peak Bill Impact", 
            format_currency(summary['peak_bill_impact']),
            help="Maximum annual bill impact"
        )
        
        st.metric(
            "Total Bill Impact", 
            format_currency(summary['total_bill_impact']),
            help="Total cumulative bill impact over 15 years"
        )
    
    with col3:
        st.metric(
            "Total Revenue Requirement", 
            format_currency(summary['total_revenue'], millions=True),
            help="Total revenue required for the program"
        )
        
        # Use the properly calculated regressivity ratio
        st.metric(
            "Regressivity Factor", 
            f"{regressivity_ratio:.2f}x",
            help="How many times greater the impact is on lowest vs. highest income quintile"
        )
    
    # Bill impact charts
    st.subheader("Bill Impact Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Annual bill impact - using utility function
        fig = create_line_chart(
            revenue_df,
            revenue_df.index,
            "bill_impact",
            "Annual Bill Impact",
            y_label="Bill Impact ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cumulative bill impact - using utility function
        fig = create_line_chart(
            revenue_df,
            revenue_df.index,
            "cumulative_bill_impact",
            "Cumulative Bill Impact",
            y_label="Cumulative Impact ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Revenue breakdown
    st.subheader("Revenue Requirement Breakdown")
    
    # Create a stacked area chart using utility function
    rev_components = ["opex", "depreciation", "return_on_capital"]
    rev_labels = {"opex": "Operating Expenses", "depreciation": "Depreciation", "return_on_capital": "Return on Capital"}
    
    fig = create_stacked_area_chart(
        revenue_df,
        "index",
        rev_components,
        "Revenue Requirement Components",
        labels=rev_labels,
        y_label="Amount ($)"
    )
    
    st.plotly_chart(fig, use_container_width=True) 