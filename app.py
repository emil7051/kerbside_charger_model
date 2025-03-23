"""
Streamlit app for the Kerbside EV Charger Model.

This app provides an interactive interface for the simplified EV charger model.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.model.kerbside_model import KerbsideModel

# Set page configuration
st.set_page_config(
    page_title="Kerbside EV Charger Model",
    page_icon="🔌",
    layout="wide"
)

# App title and description
st.title("Kerbside EV Charger Economic Model")
st.markdown("""
This app analyzes the economic implications of deploying electric vehicle (EV) chargers 
through a Regulated Asset Base (RAB) approach. Adjust the parameters to see how they
affect the economic outcomes.
""")

# Create sidebar for parameters
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

# Initialize and run the model
if 'model_results' not in st.session_state or run_button:
    with st.spinner("Running model calculations..."):
        model = KerbsideModel(model_params)
        model_results = model.run()
        st.session_state.model_results = model_results
else:
    model_results = st.session_state.model_results

# Create tabs for different result categories
tabs = st.tabs([
    "Financial Overview", 
    "Asset Evolution", 
    "Market Effects",
    "Distributional Impact",
    "Monte Carlo Analysis"
])

# Financial Overview Tab
with tabs[0]:
    st.header("Financial Overview")
    
    # Extract key results
    summary = model_results["summary"]
    revenue_df = model_results["revenue"]
    
    # Calculate regressivity factor based on income distribution
    # Income quintile data (% of median income)
    income_quintiles = {
        "Quintile 1 (Lowest)": 0.4,  # 40% of median income
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

# Asset Evolution Tab
with tabs[1]:
    st.header("Asset Base Evolution")
    
    # Extract key results
    rollout_df = model_results["rollout"]
    rab_df = model_results["rab"]
    
    # Charger deployment chart
    st.subheader("Charger Deployment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Annual deployment
        fig = px.bar(
            rollout_df,
            x=rollout_df.index,
            y="annual_chargers",
            title="Annual Charger Deployment",
            labels={"annual_chargers": "Chargers Deployed", "index": "Year"}
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Number of Chargers"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cumulative deployment
        fig = px.line(
            rollout_df,
            x=rollout_df.index,
            y="cumulative_chargers",
            title="Cumulative Chargers",
            labels={"cumulative_chargers": "Cumulative Chargers", "index": "Year"},
            markers=True
        )
        
        fig.update_layout(
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title="Number of Chargers"),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # CapEx evolution
    st.subheader("Capital Cost Evolution")
    
    fig = px.line(
        rollout_df,
        x=rollout_df.index,
        y="unit_capex",
        title="Capital Cost per Charger",
        labels={"unit_capex": "CapEx per Charger ($)", "index": "Year"},
        markers=True
    )
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title="CapEx per Charger ($)"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # RAB evolution
    st.subheader("Regulated Asset Base Evolution")
    
    # Create a combined chart with opening RAB, additions, and closing RAB
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["opening_rab"],
            name="Opening RAB",
            mode="lines+markers",
            line=dict(width=2)
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["closing_rab"],
            name="Closing RAB",
            mode="lines+markers",
            line=dict(width=2)
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=rab_df.index,
            y=rab_df["additions"],
            name="Additions",
            marker_color="lightgreen"
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=rab_df.index,
            y=-rab_df["depreciation"],
            name="Depreciation",
            marker_color="salmon"
        )
    )
    
    if "obsolescence_writeoff" in rab_df.columns:
        fig.add_trace(
            go.Bar(
                x=rab_df.index,
                y=-rab_df["obsolescence_writeoff"],
                name="Obsolescence",
                marker_color="orange"
            )
        )
    
    fig.update_layout(
        title="Regulated Asset Base Evolution",
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title="Amount ($)"),
        barmode="relative",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Market Effects Tab
with tabs[2]:
    st.header("Market Competition Effects")
    
    # Extract market data
    market_df = model_results["market"]
    
    # Market development chart
    st.subheader("Market Development")
    
    # Create a stacked area chart for charger deployment
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["rab_chargers"],
            name="RAB Chargers",
            stackgroup="one",
            line=dict(width=0),
            fillcolor="rgb(26, 118, 255)"
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["actual_private"],
            name="Private Market Chargers",
            stackgroup="one",
            line=dict(width=0),
            fillcolor="rgb(0, 200, 0)"
        )
    )
    
    # Add baseline private market line
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["baseline_private"],
            name="Baseline Private (No RAB)",
            mode="lines",
            line=dict(color="green", width=2, dash="dash")
        )
    )
    
    fig.update_layout(
        title="Charger Deployment by Market Segment",
        xaxis=dict(tickmode='linear', dtick=1, title="Year"),
        yaxis=dict(title="Number of Chargers"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Market displacement analysis
    st.subheader("Market Displacement Analysis")
    
    # Create a line chart showing displaced private market
    fig = px.area(
        market_df,
        x=market_df.index,
        y="displaced_private",
        title="Private Market Displacement",
        labels={
            "displaced_private": "Displaced Chargers",
            "index": "Year"
        }
    )
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(title="Number of Chargers"),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics
    col1, col2 = st.columns(2)
    
    with col1:
        final_year = market_df.index[-1]
        
        displaced_pct = (
            (market_df.loc[final_year, "baseline_private"] - market_df.loc[final_year, "actual_private"]) / 
            market_df.loc[final_year, "baseline_private"] * 100
        )
        
        st.metric(
            "Final Private Market Displacement", 
            f"{displaced_pct:.1f}%",
            help="Percentage of private market displaced by RAB in final year"
        )
    
    with col2:
        market_growth = (
            market_df.loc[final_year, "total_with_rab"] - market_df.loc[final_year, "total_without_rab"]
        )
        
        market_growth_pct = (
            market_growth / market_df.loc[final_year, "total_without_rab"] * 100
        )
        
        st.metric(
            "Net Market Effect", 
            f"{market_growth_pct:.1f}%",
            help="Percentage change in total market size compared to baseline"
        )

# Distributional Impact Tab
with tabs[3]:
    st.header("Distributional Impact Analysis")
    
    # Extract key results
    summary = model_results["summary"]
    avg_bill_impact = summary['avg_bill_impact']
    
    st.markdown("""
    This analysis shows how the same dollar bill impact affects households differently based on income level.
    While all households pay the same amount on their utility bills, this represents a different proportion
    of each household's income and energy spending.
    """)
    
    # Income quintile data (% of median income)
    income_quintiles = {
        "Quintile 1 (Lowest)": 0.4,  # 40% of median income
        "Quintile 2": 0.7,
        "Quintile 3 (Median)": 1.0,
        "Quintile 4": 1.4,
        "Quintile 5 (Highest)": 2.5
    }
    
    # Energy burden by income quintile (% of income spent on energy)
    # Lower income households spend higher percentage of income on energy
    energy_burden = {
        "Quintile 1 (Lowest)": 0.085,  # 8.5% of income
        "Quintile 2": 0.065,
        "Quintile 3 (Median)": 0.045,
        "Quintile 4": 0.025,
        "Quintile 5 (Highest)": 0.015
    }
    
    # EV ownership likelihood multiplier (higher income = higher likelihood of owning an EV)
    ev_likelihood = {
        "Quintile 1 (Lowest)": 0.01,
        "Quintile 2": 0.4,
        "Quintile 3 (Median)": 0.8,
        "Quintile 4": 1.2,
        "Quintile 5 (Highest)": 1.6
    }
    
    # Calculate impacts by quintile
    quintile_impacts = []
    
    # Median income assumed at $65,000
    median_income = 65000
    
    # Calculate the bill impact in dollars (same for all households)
    flat_bill_impact = avg_bill_impact
    
    for quintile, income_factor in income_quintiles.items():
        income = median_income * income_factor
        
        # Calculate current energy costs based on energy burden
        current_energy_cost = income * energy_burden[quintile]
        
        # Percentage impact on energy costs
        pct_energy_impact = (flat_bill_impact / current_energy_cost) * 100
        
        # Percentage impact on income
        pct_income_impact = (flat_bill_impact / income) * 100
        
        # Calculate potential benefit from EV chargers
        benefit_factor = ev_likelihood[quintile]
        
        quintile_impacts.append({
            "Quintile": quintile,
            "Annual Income": f"${income:,.0f}",
            "Energy Costs": f"${current_energy_cost:,.0f}",
            "Bill Impact": f"${flat_bill_impact:.2f}",
            "% of Income": f"{pct_income_impact:.3f}%",
            "% of Energy Costs": f"{pct_energy_impact:.2f}%",
            "EV Ownership Likelihood": f"{benefit_factor:.1f}x"
        })
    
    # Create dataframe and display table
    impact_df = pd.DataFrame(quintile_impacts)
    st.table(impact_df)
    
    # Calculate regressivity metrics
    lowest_quintile_income = median_income * income_quintiles["Quintile 1 (Lowest)"]
    highest_quintile_income = median_income * income_quintiles["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate actual regressivity ratio - exact same calculation as in Financial Overview tab
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show regressivity metrics
    st.subheader("Regressivity Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Income Impact Ratio", 
            f"{regressivity_ratio:.2f}x",
            help="How many times greater the impact is on lowest vs. highest income quintile"
        )
    
    with col2:
        st.metric(
            "Benefit Ratio",
            f"{ev_likelihood['Quintile 5 (Highest)'] / ev_likelihood['Quintile 1 (Lowest)']:.1f}x",
            help="How many times more likely highest income quintile benefits from EV chargers"
        )
    
    # Visualization of impact as % of income
    st.subheader("Bill Impact as Percentage of Income")
    
    pct_income_values = [float(qi["% of Income"].replace("%", "")) for qi in quintile_impacts]
    
    fig = px.bar(
        x=list(income_quintiles.keys()),
        y=pct_income_values,
        labels={"x": "Income Quintile", "y": "Percentage of Annual Income (%)"},
        title="Bill Impact as Percentage of Income by Quintile"
    )
    
    fig.update_layout(yaxis_ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)
    
    # Combined chart showing benefits vs. costs
    st.subheader("Benefits vs. Costs by Income Quintile")
    
    fig = go.Figure()
    
    # Add bar for income impact
    fig.add_trace(
        go.Bar(
            x=list(income_quintiles.keys()),
            y=pct_income_values,
            name="Cost (% of Income)",
            marker_color="firebrick"
        )
    )
    
    # Add bar for EV ownership likelihood
    fig.add_trace(
        go.Bar(
            x=list(income_quintiles.keys()),
            y=list(ev_likelihood.values()),
            name="Benefit (EV Ownership Likelihood)",
            marker_color="forestgreen"
        )
    )
    
    fig.update_layout(
        barmode='group',
        title="Costs vs. Benefits Distribution",
        xaxis_title="Income Quintile",
        yaxis_title="Relative Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation of distributional impacts
    st.markdown("""
    ### Understanding Regressivity in Utility Programs
    
    The charts above illustrate the regressivity of the EV charger program:
    
    - **Same Dollar Amount, Different Impact**: All households pay the same dollar amount on their utility bills, 
      but this represents a much larger percentage of income for lower-income households.
      
    - **Energy Burden**: Lower-income households already spend a higher percentage of their income on energy costs,
      making any additional costs more impactful.
      
    - **Benefits Accrue Unequally**: Higher-income households are more likely to own EVs and therefore
      directly benefit from the charger infrastructure, while lower-income households bear the costs with less benefit.
      
    - **Regressivity Ratio**: The bill impact is {regressivity_ratio:.2f} times more burdensome for the lowest income quintile 
      compared to the highest income quintile when measured as a percentage of income.
    """)

# Monte Carlo Analysis Tab
with tabs[4]:
    st.header("Monte Carlo Simulation")
    
    st.markdown("""
    Run a Monte Carlo simulation to explore the effect of parameter uncertainty on model outcomes.
    The simulation will vary key parameters within a reasonable range to understand the sensitivity
    of results to different inputs.
    """)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        n_simulations = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=1000,
            value=200,
            step=100,
            help="More simulations provide better results but take longer"
        )
        
        run_mc_button = st.button("Run Simulation", use_container_width=True)
    
    # Run Monte Carlo simulation if requested
    if run_mc_button:
        with st.spinner(f"Running {n_simulations} simulations..."):
            model = KerbsideModel(model_params)
            mc_results = model.run_monte_carlo(n_simulations=n_simulations)
            st.session_state.mc_results = mc_results
    
    # Display Monte Carlo results if available
    if 'mc_results' in st.session_state:
        mc_results = st.session_state.mc_results
        results_df = mc_results["results_df"]
        summary_stats = mc_results["summary_stats"]
        
        # Display histogram of bill impacts
        st.subheader("Distribution of Bill Impacts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                results_df,
                x="avg_bill_impact",
                nbins=20,
                title="Average Annual Bill Impact",
                labels={"avg_bill_impact": "Average Annual Bill Impact ($)"}
            )
            
            fig.add_vline(
                x=summary_stats["avg_bill_impact_mean"], 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: ${summary_stats['avg_bill_impact_mean']:.2f}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Average Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                results_df,
                x="peak_bill_impact",
                nbins=20,
                title="Peak Annual Bill Impact",
                labels={"peak_bill_impact": "Peak Annual Bill Impact ($)"}
            )
            
            fig.add_vline(
                x=summary_stats["peak_bill_impact_mean"], 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: ${summary_stats['peak_bill_impact_mean']:.2f}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Peak Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        
        # Create a table of statistics for key metrics
        metrics = ["avg_bill_impact", "peak_bill_impact", "npv_bill_impact", "total_bill_impact"]
        metric_labels = {
            "avg_bill_impact": "Average Annual Bill Impact ($)",
            "peak_bill_impact": "Peak Annual Bill Impact ($)",
            "npv_bill_impact": "NPV of Bill Impacts ($)",
            "total_bill_impact": "Total Bill Impact ($)"
        }
        
        stats_data = []
        
        for metric in metrics:
            stats_data.append({
                "Metric": metric_labels.get(metric, metric),
                "Mean": f"${summary_stats[f'{metric}_mean']:.2f}",
                "Median": f"${summary_stats[f'{metric}_median']:.2f}",
                "Std Dev": f"${summary_stats[f'{metric}_std']:.2f}",
                "10th %ile": f"${summary_stats[f'{metric}_p10']:.2f}",
                "90th %ile": f"${summary_stats[f'{metric}_p90']:.2f}"
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.table(stats_df)
        
        # Display parameter sensitivities
        st.subheader("Parameter Sensitivities")
        
        if "correlations" in summary_stats:
            # Get correlations for average bill impact
            bill_impact_corr = summary_stats["correlations"].get("avg_bill_impact", {})
            
            if bill_impact_corr:
                # Create a horizontal bar chart
                corr_df = pd.DataFrame({
                    "Parameter": list(bill_impact_corr.keys()),
                    "Correlation": list(bill_impact_corr.values())
                })
                
                # Sort by absolute correlation
                corr_df["AbsCorr"] = corr_df["Correlation"].abs()
                corr_df = corr_df.sort_values("AbsCorr", ascending=False).head(10)
                
                fig = px.bar(
                    corr_df,
                    y="Parameter",
                    x="Correlation",
                    title="Parameter Sensitivity to Average Bill Impact",
                    orientation="h",
                    color="Correlation",
                    color_continuous_scale=px.colors.diverging.RdBu_r
                )
                
                fig.update_layout(
                    xaxis=dict(title="Correlation Coefficient"),
                    yaxis=dict(title=""),
                    coloraxis_showscale=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                The chart above shows the correlation between each parameter and the average bill impact.
                A positive correlation means that increasing the parameter increases the bill impact,
                while a negative correlation means that increasing the parameter decreases the bill impact.
                The absolute value indicates the strength of the relationship.
                """)
            else:
                st.info("No correlation data available.")
        else:
            st.info("No sensitivity analysis data available.")

# Footer with additional information
st.markdown("---")
st.markdown("""
**About this model**: This is a simplified implementation of the EV charger RAB economic model.
The model calculates the impact of deploying EV chargers on customer bills, regulated asset base,
and market competition.
""") 