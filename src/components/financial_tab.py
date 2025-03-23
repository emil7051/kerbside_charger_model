"""
Financial Overview tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_financial_tab(model_results):
    """
    Render the Financial Overview tab.
    
    Args:
        model_results: Dictionary of model results
    """
    st.header("Financial Overview")
    
    # Extract key results
    summary = model_results["summary"]
    revenue_df = model_results["revenue"]
    
    # Calculate regressivity factor based on income distribution
    # Income quintile data (% of median income)
    income_quintiles = {
        "Quintile 1 (Lowest)": 0.35,  # 35% of median income
        "Quintile 2": 0.7,
        "Quintile 3 (Median)": 1.0,
        "Quintile 4": 1.4,
        "Quintile 5 (Highest)": 2.5
    }
    
    # Calculate percentage impact on income for lowest and highest quintiles
    median_income = 65000
    avg_bill_impact = summary['avg_bill_impact']
    
    lowest_quintile_income = median_income * income_quintiles["Quintile 1 (Lowest)"]
    highest_quintile_income = median_income * income_quintiles["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate actual regressivity ratio
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average Annual Bill Impact", 
            f"${summary['avg_bill_impact']:.2f}",
            help="Average annual increase in household bills"
        )
        
        st.metric(
            "NPV of Bill Impacts", 
            f"${summary['npv_bill_impact']:.2f}",
            help="Net present value of bill impacts over 15 years"
        )
    
    with col2:
        st.metric(
            "Peak Bill Impact", 
            f"${summary['peak_bill_impact']:.2f}",
            help="Maximum annual bill impact"
        )
        
        st.metric(
            "Total Bill Impact", 
            f"${summary['total_bill_impact']:.2f}",
            help="Total cumulative bill impact over 15 years"
        )
    
    with col3:
        st.metric(
            "Total Revenue Requirement", 
            f"${summary['total_revenue']/1e6:.1f}M",
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
        # Annual bill impact
        fig = px.line(
            revenue_df,
            x=revenue_df.index,
            y="bill_impact",
            title="Annual Bill Impact",
            labels={"bill_impact": "Bill Impact ($)", "index": "Year"},
            markers=True
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Annual Bill Impact ($)"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cumulative bill impact
        fig = px.line(
            revenue_df,
            x=revenue_df.index,
            y="cumulative_bill_impact",
            title="Cumulative Bill Impact",
            labels={"cumulative_bill_impact": "Cumulative Impact ($)", "index": "Year"},
            markers=True
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Cumulative Bill Impact ($)"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Revenue breakdown
    st.subheader("Revenue Requirement Breakdown")
    
    # Create a stacked area chart
    rev_components = ["opex", "depreciation", "return_on_capital"]
    rev_labels = {"opex": "Operating Expenses", "depreciation": "Depreciation", "return_on_capital": "Return on Capital"}
    
    fig = go.Figure()
    
    for component in rev_components:
        fig.add_trace(
            go.Scatter(
                x=revenue_df.index,
                y=revenue_df[component],
                name=rev_labels.get(component, component),
                stackgroup="one"
            )
        )
    
    fig.update_layout(
        title="Revenue Requirement Components",
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title="Amount ($)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True) 