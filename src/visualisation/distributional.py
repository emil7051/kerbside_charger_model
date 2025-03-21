"""Regressive impact visualizations for the EV charger model."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def create_income_impact_chart(dist_df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing bill impact as percentage of income by quintile.
    
    Args:
        dist_df: Distributional impact DataFrame
        
    Returns:
        Plotly figure
    """
    # Sort by quintile to ensure Q1 to Q5 order
    df = dist_df.sort_values("quintile")
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(
        go.Bar(
            x=df["quintile"],
            y=df["impact_pct_income"],
            marker_color="#1f77b4",
            text=[f"{x:.2f}%" for x in df["impact_pct_income"]],
            textposition="auto"
        )
    )
    
    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=df["quintile"],
            y=df["impact_pct_income"],
            mode="lines",
            line=dict(color="#ff7f0e", width=3, dash="dash"),
            name="Trend"
        )
    )
    
    # Add regressivity annotation
    regressivity_ratio = df.iloc[0]["regressivity_ratio_income"]
    
    fig.add_annotation(
        x=df["quintile"].iloc[-1],
        y=df["impact_pct_income"].min(),
        text=f"Regressivity Ratio: {regressivity_ratio:.2f}x",
        showarrow=False,
        yshift=-30
    )
    
    fig.update_layout(
        title="Distributional Impact by Income Quintile",
        xaxis_title="Income Quintile",
        yaxis_title="Percentage of Income/Bill (%)",
        template="plotly_white",
        margin=dict(t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_bill_impact_chart(dist_df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing bill impact as percentage of electricity bill by quintile.
    
    Args:
        dist_df: Distributional impact DataFrame
        
    Returns:
        Plotly figure
    """
    # Sort by quintile to ensure Q1 to Q5 order
    df = dist_df.sort_values("quintile")
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(
        go.Bar(
            x=df["quintile"],
            y=df["impact_pct_bill"],
            marker_color="#2ca02c",
            text=[f"{x:.2f}%" for x in df["impact_pct_bill"]],
            textposition="auto"
        )
    )
    
    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=df["quintile"],
            y=df["impact_pct_bill"],
            mode="lines",
            line=dict(color="#d62728", width=3, dash="dash"),
            name="Trend"
        )
    )
    
    # Add regressivity annotation
    regressivity_ratio = df.iloc[0]["regressivity_ratio_bill"]
    
    fig.add_annotation(
        x=df["quintile"].iloc[-1],
        y=df["impact_pct_bill"].min(),
        text=f"Regressivity Ratio: {regressivity_ratio:.2f}x",
        showarrow=False,
        yshift=-30
    )
    
    fig.update_layout(
        title="Distributional Impact: Impact per Customer",
        xaxis_title="Income Quintile",
        yaxis_title="Annual Impact ($)",
        template="plotly_white",
        margin=dict(t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_regressivity_gauge(dist_df: pd.DataFrame) -> go.Figure:
    """
    Create a gauge chart showing regressivity ratio.
    
    Args:
        dist_df: Distributional impact DataFrame
        
    Returns:
        Plotly figure
    """
    # Get regressivity ratio
    regressivity_ratio = dist_df.iloc[0]["regressivity_ratio_income"]
    
    # Define thresholds for color coding
    thresholds = [1, 2, 3, 5, 10]
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#7f7f7f"]
    
    # Find color based on value
    color_idx = 0
    for i, threshold in enumerate(thresholds):
        if regressivity_ratio >= threshold:
            color_idx = i
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=regressivity_ratio,
        title={"text": "Regressivity Ratio"},
        gauge={
            "axis": {"range": [0, 10]},
            "bar": {"color": colors[color_idx]},
            "steps": [
                {"range": [0, 1], "color": "#e5f5e0"},
                {"range": [1, 2], "color": "#c7e9c0"},
                {"range": [2, 3], "color": "#a1d99b"},
                {"range": [3, 5], "color": "#74c476"},
                {"range": [5, 10], "color": "#31a354"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": regressivity_ratio
            }
        }
    ))
    
    # Add interpretation annotation
    if regressivity_ratio < 1:
        interpretation = "Progressive"
    elif regressivity_ratio < 2:
        interpretation = "Slightly Regressive"
    elif regressivity_ratio < 5:
        interpretation = "Moderately Regressive"
    else:
        interpretation = "Highly Regressive"
    
    fig.add_annotation(
        x=0.5,
        y=0.25,
        text=interpretation,
        font=dict(size=20),
        showarrow=False,
        xref="paper",
        yref="paper"
    )
    
    fig.update_layout(
        height=300,
        title="Regressivity Metric",
        template="plotly_white"
    )
    
    return fig

def create_lifetime_impact_chart(df_by_year: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap showing impact over time for each quintile.
    
    Args:
        df_by_year: Distributional impact by year DataFrame
        
    Returns:
        Plotly figure
    """
    # Pivot data to create heatmap
    pivot_df = df_by_year.pivot(
        index="quintile",
        columns="year",
        values="impact_pct_income"
    )
    
    # Ensure quintiles are in the right order
    quintile_order = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    pivot_df = pivot_df.reindex(quintile_order)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale="Blues",
        colorbar=dict(title="% of Income")
    ))
    
    fig.update_layout(
        title="Lifetime Distributional Impact",
        xaxis_title="Year",
        yaxis_title="Percentage of Income (%)",
        template="plotly_white",
        margin=dict(t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_distributional_dashboard(
    dist_df: pd.DataFrame,
    df_by_year: Optional[pd.DataFrame] = None
) -> Dict[str, go.Figure]:
    """
    Create a dashboard with distributional impact visualizations.
    
    Args:
        dist_df: Distributional impact DataFrame
        df_by_year: Optional DataFrame with impact by year
        
    Returns:
        Dictionary of Plotly figures
    """
    figures = {}
    
    # Income impact chart
    figures["income_impact"] = create_income_impact_chart(dist_df)
    
    # Bill impact chart
    figures["bill_impact"] = create_bill_impact_chart(dist_df)
    
    # Regressivity gauge
    figures["regressivity_gauge"] = create_regressivity_gauge(dist_df)
    
    # Combined dashboard
    fig_combined = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Impact as % of Income", 
            "Impact as % of Electricity Bill",
            "Regressivity Metric",
            "Impact Comparison"
        ],
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "indicator"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12  # Increased from default
    )
    
    # Income impact
    fig_combined.add_trace(
        go.Bar(
            x=dist_df["quintile"],
            y=dist_df["impact_pct_income"],
            marker_color="#1f77b4",
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Bill impact
    fig_combined.add_trace(
        go.Bar(
            x=dist_df["quintile"],
            y=dist_df["impact_pct_bill"],
            marker_color="#2ca02c",
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Regressivity gauge
    regressivity_ratio = dist_df.iloc[0]["regressivity_ratio_income"]
    fig_combined.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=regressivity_ratio,
            gauge={
                "axis": {"range": [0, 10]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 2], "color": "#c7e9c0"},
                    {"range": [2, 5], "color": "#a1d99b"},
                    {"range": [5, 10], "color": "#31a354"},
                ],
            },
            domain={"row": 1, "column": 0}
        ),
        row=2, col=1
    )
    
    # Comparison chart (absolute bill amount)
    fig_combined.add_trace(
        go.Bar(
            x=dist_df["quintile"],
            y=dist_df["bill_impact"],
            marker_color="#ff7f0e",
            name="Bill Impact ($)",
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig_combined.update_layout(
        height=800,
        title_text="Distributional Impact Dashboard",
        template="plotly_white",
        margin=dict(t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    figures["dashboard"] = fig_combined
    
    # Add lifetime impact chart if data available
    if df_by_year is not None:
        figures["lifetime_impact"] = create_lifetime_impact_chart(df_by_year)
    
    return figures 