"""
Asset Evolution tab component for the Kerbside Model app.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render_asset_tab(model_results):
    """
    Render the Asset Base Evolution tab.
    
    Args:
        model_results: Dictionary of model results
    """
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