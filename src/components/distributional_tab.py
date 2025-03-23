"""
Distributional Impact tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_distributional_tab(model_results):
    """
    Render the Distributional Impact tab.
    
    Args:
        model_results: Dictionary of model results
    """
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
        
    # Create dataframe and display table
    impact_df = pd.DataFrame(quintile_impacts)
    st.table(impact_df)

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
    st.markdown(f"""
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