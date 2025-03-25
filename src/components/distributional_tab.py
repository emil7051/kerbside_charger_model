"""
Distributional Impact tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils.parameters import DEFAULT_MEDIAN_INCOME, INCOME_QUINTILES, ENERGY_BURDEN, EV_LIKELIHOOD

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
    
    # Calculate actual income values from the quintile percentages
    income_quintiles_absolute = {
        quintile: DEFAULT_MEDIAN_INCOME * percentage
        for quintile, percentage in INCOME_QUINTILES.items()
    }
    
    # Calculate impacts by quintile
    quintile_impacts = []
    
    # Calculate the bill impact in dollars (same for all households)
    flat_bill_impact = avg_bill_impact
    
    for quintile, percentage in INCOME_QUINTILES.items():
        # Calculate income using the percentages from constants
        income = DEFAULT_MEDIAN_INCOME * percentage
        
        # Calculate impacts
        current_energy_cost = income * ENERGY_BURDEN[quintile]
        
        # Percentage impact on income
        pct_income_impact = (flat_bill_impact / income) * 100
        
        # EV benefit calculation
        benefit_factor = EV_LIKELIHOOD[quintile]
        
        quintile_impacts.append({
            "Quintile": quintile,
            "Annual Income": f"${income:,.0f}",
            "Energy Costs": f"${current_energy_cost:,.0f}",
            "Bill Impact": f"${flat_bill_impact:.2f}",
            "% of Income": f"{pct_income_impact:.3f}%",
            "EV Ownership Likelihood": f"{benefit_factor:.1f}x"
        })

    # Calculate regressivity metrics
    lowest_quintile_income = DEFAULT_MEDIAN_INCOME * INCOME_QUINTILES["Quintile 1 (Lowest)"]
    highest_quintile_income = DEFAULT_MEDIAN_INCOME * INCOME_QUINTILES["Quintile 5 (Highest)"]
    
    lowest_quintile_pct_impact = (avg_bill_impact / lowest_quintile_income) * 100
    highest_quintile_pct_impact = (avg_bill_impact / highest_quintile_income) * 100
    
    # Calculate actual regressivity ratio - exact same calculation as in Financial Overview tab
    regressivity_ratio = lowest_quintile_pct_impact / highest_quintile_pct_impact
    
    # Show regressivity metrics
    st.subheader("Regressivity Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Income Impact Ratio", 
            f"{regressivity_ratio:.2f}x",
            help="How many times greater the impact is on lowest vs. highest income quintile"
        )
    
    with col2:
        st.metric(
            "Benefit Ratio",
            f"{EV_LIKELIHOOD['Quintile 5 (Highest)'] / EV_LIKELIHOOD['Quintile 1 (Lowest)']:.1f}x",
            help="How many times more likely highest income quintile benefits from EV chargers"
        )
    
    with col3:
        st.metric(
            "NPV of Bill Impacts", 
            f"${summary['npv_bill_impact']:.2f}",
            help="Net present value of bill impacts over 15 years"
        )
        
    # Create dataframe and display table
    impact_df = pd.DataFrame(quintile_impacts)
    st.table(impact_df)

    # Visualisation of impact as % of income
    st.subheader("Bill Impact as Percentage of Income")
    
    pct_income_values = [float(qi["% of Income"].replace("%", "")) for qi in quintile_impacts]
    
    fig = px.bar(
        x=list(INCOME_QUINTILES.keys()),
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
            x=list(INCOME_QUINTILES.keys()),
            y=pct_income_values,
            name="Cost (% of Income)",
            marker_color="firebrick"
        )
    )
    
    # Add bar for EV ownership likelihood
    fig.add_trace(
        go.Bar(
            x=list(INCOME_QUINTILES.keys()),
            y=list(EV_LIKELIHOOD.values()),
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
    
    - **Same Dollar Amount, Different Impact**: The same dollar amount represents 
        a much larger percentage of income for lower-income households.
      
    - **Energy Burden**: Lower-income households already spend a higher percentage of their income on energy costs,
      making any additional costs more impactful.
      
    - **Benefits Accrue Unequally**: Higher-income households are more likely to own EVs and therefore
      directly benefit from the charger infrastructure, while lower-income households bear the costs with less benefit.
      
    - **Regressivity Ratio**: The bill impact is {regressivity_ratio:.2f} times more burdensome for the lowest income quintile 
      compared to the highest income quintile when measured as a percentage of income.
    """) 