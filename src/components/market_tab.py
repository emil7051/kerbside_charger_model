"""
Market Effects tab component for the Kerbside Model app.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_market_tab(model_results):
    """
    Render the Market Competition Effects tab.
    
    Args:
        model_results: Dictionary of model results
    """
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