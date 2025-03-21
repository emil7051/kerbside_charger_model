"""Market comparison charts for the EV charger model."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def create_market_development_chart(market_df: pd.DataFrame) -> go.Figure:
    """
    Create a line chart showing market development with and without RAB.
    
    Args:
        market_df: Market development DataFrame
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add total market with RAB
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["total_with_rab"],
            mode="lines",
            name="Total Market with RAB",
            line=dict(color="#1f77b4", width=3)
        )
    )
    
    # Add baseline market without RAB
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["total_without_rab"],
            mode="lines",
            name="Total Market without RAB",
            line=dict(color="#ff7f0e", width=3, dash="dash")
        )
    )
    
    # Add RAB chargers
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["rab_chargers"],
            mode="lines",
            name="RAB Chargers",
            line=dict(color="#2ca02c", width=2)
        )
    )
    
    # Add private market with RAB
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["actual_private"],
            mode="lines",
            name="Private Market with RAB",
            line=dict(color="#d62728", width=2)
        )
    )
    
    fig.update_layout(
        title="Market Development: Charger Deployment",
        xaxis_title="Year",
        yaxis_title="Number of Chargers",
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

def create_market_composition_chart(market_df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing market composition in final year.
    
    Args:
        market_df: Market development DataFrame
        
    Returns:
        Plotly figure
    """
    # Get final year data
    final_year = market_df.index.max()
    
    # Create figure
    fig = go.Figure()
    
    # Scenario with RAB
    fig.add_trace(
        go.Bar(
            x=["With RAB"],
            y=[market_df.loc[final_year, "rab_chargers"]],
            name="RAB Chargers",
            marker_color="#2ca02c"
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=["With RAB"],
            y=[market_df.loc[final_year, "actual_private"]],
            name="Private Chargers",
            marker_color="#d62728"
        )
    )
    
    # Scenario without RAB
    fig.add_trace(
        go.Bar(
            x=["Without RAB"],
            y=[market_df.loc[final_year, "baseline_private"]],
            name="Private Chargers",
            marker_color="#ff7f0e"
        )
    )
    
    # Add text annotations for total
    total_with_rab = market_df.loc[final_year, "total_with_rab"]
    total_without_rab = market_df.loc[final_year, "total_without_rab"]
    
    for x, y, text in [
        ("With RAB", total_with_rab, f"Total: {int(total_with_rab):,}"),
        ("Without RAB", total_without_rab, f"Total: {int(total_without_rab):,}")
    ]:
        fig.add_annotation(
            x=x,
            y=y,
            text=text,
            showarrow=False,
            yshift=10
        )
    
    # Calculate and show net effect
    net_effect = total_with_rab - total_without_rab
    net_effect_pct = (net_effect / total_without_rab) * 100
    
    effect_text = (
        f"Net Effect: {'+' if net_effect >= 0 else ''}{int(net_effect):,} chargers "
        f"({'+' if net_effect_pct >= 0 else ''}{net_effect_pct:.1f}%)"
    )
    
    fig.add_annotation(
        x=0.5,
        y=1.1,
        xref="paper",
        yref="paper",
        text=effect_text,
        showarrow=False,
        font=dict(size=16)
    )
    
    fig.update_layout(
        xaxis_title="Scenario",
        yaxis_title="Number of Chargers",
        title="Final Year Market Composition",
        template="plotly_white",
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_innovation_chart(innovation_df: pd.DataFrame) -> go.Figure:
    """
    Create a line chart comparing cost trajectories.
    
    Args:
        innovation_df: Innovation impact DataFrame
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add competitive market cost trajectory
    fig.add_trace(
        go.Scatter(
            x=innovation_df.index,
            y=innovation_df["competitive_capex"],
            mode="lines",
            name="Competitive Market CapEx",
            line=dict(color="#1f77b4", width=3)
        )
    )
    
    # Add monopoly market cost trajectory
    fig.add_trace(
        go.Scatter(
            x=innovation_df.index,
            y=innovation_df["monopoly_capex"],
            mode="lines",
            name="Monopoly Market CapEx",
            line=dict(color="#ff7f0e", width=3)
        )
    )
    
    # Add innovation gap
    fig.add_trace(
        go.Scatter(
            x=innovation_df.index,
            y=innovation_df["innovation_gap"],
            mode="lines",
            name="Innovation Gap",
            line=dict(color="#d62728", width=2, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(214, 39, 40, 0.1)"
        )
    )
    
    fig.update_layout(
        title="Market Development: Cost Evolution",
        xaxis_title="Year",
        yaxis_title="Cost per Charger ($)",
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

def create_displacement_chart(market_df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing private market displacement over time.
    
    Args:
        market_df: Market development DataFrame
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add displacement percentage
    fig.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["displacement_percentage"],
            mode="lines+markers",
            name="Private Market Displacement",
            line=dict(color="#d62728", width=3),
            marker=dict(size=8)
        )
    )
    
    # Add visual reference for 50% displacement
    fig.add_shape(
        type="line",
        x0=market_df.index.min(),
        x1=market_df.index.max(),
        y0=50,
        y1=50,
        line=dict(color="#ff7f0e", width=2, dash="dash")
    )
    
    fig.add_annotation(
        x=market_df.index.max(),
        y=50,
        text="50% Displacement",
        showarrow=False,
        yshift=10
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Displacement (%)",
        title="Private Market Displacement Effect",
        template="plotly_white"
    )
    
    return fig

def create_competitive_dashboard(
    market_df: pd.DataFrame,
    innovation_df: pd.DataFrame,
    metrics: Dict[str, float]
) -> Dict[str, go.Figure]:
    """
    Create a dashboard with competitive market visualizations.
    
    Args:
        market_df: Market development DataFrame
        innovation_df: Innovation impact DataFrame
        metrics: Competitive metrics dictionary
        
    Returns:
        Dictionary of Plotly figures
    """
    figures = {}
    
    # Market development chart
    figures["market_development"] = create_market_development_chart(market_df)
    
    # Market composition chart
    figures["market_composition"] = create_market_composition_chart(market_df)
    
    # Innovation chart
    figures["innovation_impact"] = create_innovation_chart(innovation_df)
    
    # Displacement chart
    figures["displacement_effect"] = create_displacement_chart(market_df)
    
    # Create summary metrics table
    summary_metrics = [
        ("Total RAB Chargers", f"{int(metrics['total_rab_chargers']):,}"),
        ("Total Private Chargers with RAB", f"{int(metrics['total_private_with_rab']):,}"),
        ("Total Private Chargers without RAB", f"{int(metrics['total_private_without_rab']):,}"),
        ("Market Growth with RAB", f"{metrics['market_growth_percentage']:.1f}%"),
        ("Private Market Displacement", f"{metrics['private_displacement_percentage']:.1f}%"),
        ("Final Innovation Gap", f"{metrics['final_innovation_gap_pct']:.1f}%"),
        ("Total Innovation Cost", f"${metrics['total_innovation_cost'] / 1e6:.2f}M")
    ]
    
    fig_metrics = go.Figure(data=[go.Table(
        header=dict(
            values=["Metric", "Value"],
            fill_color="#1f77b4",
            align="left",
            font=dict(color="white", size=14)
        ),
        cells=dict(
            values=list(zip(*summary_metrics)),
            fill_color="#f5f5f5",
            align="left",
            font=dict(size=14)
        )
    )])
    
    fig_metrics.update_layout(
        title="Market Structure Comparison",
        template="plotly_white",
        margin=dict(t=80, b=50),
        height=400
    )
    
    figures["metrics_table"] = fig_metrics
    
    # Combined dashboard
    fig_combined = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Market Development",
            "Innovation Impact",
            "Market Composition (Final Year)",
            "Private Market Displacement"
        ],
        vertical_spacing=0.12  # Increased from default
    )
    
    # Market development
    fig_combined.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["total_with_rab"],
            mode="lines",
            name="With RAB",
            line=dict(color="#1f77b4")
        ),
        row=1, col=1
    )
    
    fig_combined.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["total_without_rab"],
            mode="lines",
            name="Without RAB",
            line=dict(color="#ff7f0e", dash="dash")
        ),
        row=1, col=1
    )
    
    # Innovation impact
    fig_combined.add_trace(
        go.Scatter(
            x=innovation_df.index,
            y=innovation_df["competitive_capex"],
            mode="lines",
            name="Competitive",
            line=dict(color="#1f77b4")
        ),
        row=1, col=2
    )
    
    fig_combined.add_trace(
        go.Scatter(
            x=innovation_df.index,
            y=innovation_df["monopoly_capex"],
            mode="lines",
            name="Monopoly",
            line=dict(color="#ff7f0e")
        ),
        row=1, col=2
    )
    
    # Final year composition
    final_year = market_df.index.max()
    
    fig_combined.add_trace(
        go.Bar(
            x=["With RAB"],
            y=[market_df.loc[final_year, "rab_chargers"]],
            name="RAB",
            marker_color="#2ca02c"
        ),
        row=2, col=1
    )
    
    fig_combined.add_trace(
        go.Bar(
            x=["With RAB"],
            y=[market_df.loc[final_year, "actual_private"]],
            name="Private",
            marker_color="#d62728"
        ),
        row=2, col=1
    )
    
    fig_combined.add_trace(
        go.Bar(
            x=["Without RAB"],
            y=[market_df.loc[final_year, "baseline_private"]],
            name="Private",
            marker_color="#ff7f0e"
        ),
        row=2, col=1
    )
    
    # Displacement effect
    fig_combined.add_trace(
        go.Scatter(
            x=market_df.index,
            y=market_df["displacement_percentage"],
            mode="lines",
            name="Displacement",
            line=dict(color="#d62728")
        ),
        row=2, col=2
    )
    
    fig_combined.update_layout(
        height=1200,
        title_text="Market Competition Analysis Dashboard",
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
    
    return figures 