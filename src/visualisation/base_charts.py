"""Core financial visualizations for the EV charger model."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def create_financial_summary(
    revenue_df: pd.DataFrame,
    rollout_df: pd.DataFrame,
    rab_df: pd.DataFrame,
    summary_stats: Dict[str, Any]
) -> Dict[str, go.Figure]:
    """
    Create core financial summary visualizations.
    
    Args:
        revenue_df: Revenue requirements DataFrame
        rollout_df: Charger deployment DataFrame
        rab_df: Regulated Asset Base DataFrame
        summary_stats: Summary statistics dictionary
        
    Returns:
        Dictionary of Plotly figures
    """
    figures = {}
    
    # 1. Revenue requirements
    fig_revenue = make_subplots(
        rows=1, cols=1,
        subplot_titles=["Annual Revenue Requirements"],
        vertical_spacing=0.12
    )
    
    # Create a stacked bar chart for revenue components
    fig_revenue.add_trace(
        go.Bar(
            x=revenue_df.index,
            y=revenue_df["return_on_capital"],
            name="Return on Capital",
            marker_color="#1f77b4"
        )
    )
    
    fig_revenue.add_trace(
        go.Bar(
            x=revenue_df.index,
            y=revenue_df["depreciation"],
            name="Depreciation",
            marker_color="#ff7f0e"
        )
    )
    
    fig_revenue.add_trace(
        go.Bar(
            x=revenue_df.index,
            y=revenue_df["opex"],
            name="Operating Expenditure",
            marker_color="#2ca02c"
        )
    )
    
    fig_revenue.add_trace(
        go.Scatter(
            x=revenue_df.index,
            y=revenue_df["net_revenue_requirement"],
            name="Net Revenue Requirement",
            line=dict(color="#d62728", width=3)
        )
    )
    
    fig_revenue.update_layout(
        barmode="stack",
        xaxis_title="Year",
        yaxis_title="Revenue Requirement ($)",
        title="Annual Revenue Requirements",
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
    
    figures["revenue_requirements"] = fig_revenue
    
    # 2. Bill impact
    fig_bill = go.Figure()
    
    fig_bill.add_trace(
        go.Bar(
            x=revenue_df.index,
            y=revenue_df["per_customer_impact"],
            marker_color="#1f77b4",
            name="Bill Impact per Customer"
        )
    )
    
    # Add trend line
    fig_bill.add_trace(
        go.Scatter(
            x=revenue_df.index,
            y=revenue_df["per_customer_impact"],
            mode="lines",
            line=dict(color="#ff7f0e", width=3),
            name="Trend"
        )
    )
    
    # Add horizontal line for average
    avg_bill = summary_stats["Average Annual Bill Impact"]
    
    fig_bill.add_shape(
        type="line",
        x0=revenue_df.index.min(),
        x1=revenue_df.index.max(),
        y0=avg_bill,
        y1=avg_bill,
        line=dict(
            color="#d62728",
            width=2,
            dash="dash"
        )
    )
    
    # Add annotation for average
    fig_bill.add_annotation(
        x=revenue_df.index.max(),
        y=avg_bill,
        text=f"Average: ${avg_bill:.2f}",
        showarrow=False,
        yshift=10
    )
    
    fig_bill.update_layout(
        xaxis_title="Year",
        yaxis_title="Annual Bill Impact per Customer ($)",
        title="Annual Bill Impact per Customer",
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
    
    figures["bill_impact"] = fig_bill
    
    # 3. RAB evolution
    fig_rab = go.Figure()
    
    fig_rab.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["average_rab"],
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
            name="Regulated Asset Base"
        )
    )
    
    # Add capex as bars
    fig_rab.add_trace(
        go.Bar(
            x=rab_df.index,
            y=rab_df["capex"],
            marker_color="#ff7f0e",
            name="Annual Capital Expenditure",
            yaxis="y2"
        )
    )
    
    fig_rab.update_layout(
        xaxis_title="Year",
        yaxis_title="Regulated Asset Base ($)",
        yaxis2=dict(
            title="Annual Capital Expenditure ($)",
            overlaying="y",
            side="right"
        ),
        title="Regulated Asset Base Evolution",
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
    
    figures["rab_evolution"] = fig_rab
    
    # 4. Charger deployment
    fig_chargers = go.Figure()
    
    fig_chargers.add_trace(
        go.Bar(
            x=rollout_df.index,
            y=rollout_df["annual_chargers"],
            marker_color="#1f77b4",
            name="Annual Chargers Deployed"
        )
    )
    
    fig_chargers.add_trace(
        go.Scatter(
            x=rollout_df.index,
            y=rollout_df["cumulative_chargers"],
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
            name="Cumulative Chargers",
            yaxis="y2"
        )
    )
    
    fig_chargers.update_layout(
        xaxis_title="Year",
        yaxis_title="Annual Chargers Deployed",
        yaxis2=dict(
            title="Cumulative Chargers",
            overlaying="y",
            side="right"
        ),
        title="Charger Deployment",
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
    
    figures["charger_deployment"] = fig_chargers
    
    # 5. Dashboard summary
    fig_summary = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Regulated Asset Base", 
            "Annual Bill Impact",
            "Cumulative Chargers",
            "Revenue Requirement"
        ],
        vertical_spacing=0.15
    )
    
    # RAB
    fig_summary.add_trace(
        go.Scatter(
            x=rab_df.index,
            y=rab_df["average_rab"],
            mode="lines",
            line=dict(color="#1f77b4"),
            name="RAB"
        ),
        row=1, col=1
    )
    
    # Bill impact
    fig_summary.add_trace(
        go.Bar(
            x=revenue_df.index,
            y=revenue_df["per_customer_impact"],
            marker_color="#ff7f0e",
            name="Bill Impact"
        ),
        row=1, col=2
    )
    
    # Cumulative chargers
    fig_summary.add_trace(
        go.Scatter(
            x=rollout_df.index,
            y=rollout_df["cumulative_chargers"],
            mode="lines",
            line=dict(color="#2ca02c"),
            name="Chargers"
        ),
        row=2, col=1
    )
    
    # Revenue requirement
    fig_summary.add_trace(
        go.Scatter(
            x=revenue_df.index,
            y=revenue_df["net_revenue_requirement"],
            mode="lines",
            line=dict(color="#d62728"),
            name="Revenue"
        ),
        row=2, col=2
    )
    
    fig_summary.update_layout(
        height=600,
        showlegend=True,
        template="plotly_white",
        margin=dict(t=80, b=50),
        title_text="Financial Summary Dashboard",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    figures["summary_dashboard"] = fig_summary
    
    return figures

def create_financial_metrics_table(summary_stats: Dict[str, Any]) -> go.Figure:
    """
    Create a table visualisation of financial metrics.
    
    Args:
        summary_stats: Summary statistics dictionary
        
    Returns:
        Plotly figure with table
    """
    # Extract key metrics
    metrics = [
        ("Total Chargers", f"{int(summary_stats['Total Chargers']):,}"),
        ("NPV of Revenue Requirement", f"${summary_stats['NPV of Revenue Requirement'] / 1e6:.2f}M"),
        ("Cumulative Bill Impact/Customer", f"${summary_stats['Cumulative Bill Impact/Customer']:.2f}"),
        ("Average Annual Bill Impact", f"${summary_stats['Average Annual Bill Impact']:.2f}"),
        ("Peak RAB", f"${summary_stats['Peak RAB'] / 1e6:.2f}M"),
        ("Peak Annual Bill Impact", f"${summary_stats['Peak Annual Bill Impact']:.2f}"),
        ("Cost per Charger", f"${summary_stats['Cost per Charger']:.2f}"),
    ]
    
    # Create figure
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Metric", "Value"],
            fill_color="#1f77b4",
            align="left",
            font=dict(color="white", size=14)
        ),
        cells=dict(
            values=list(zip(*metrics)),
            fill_color="#f5f5f5",
            align="left",
            font=dict(size=14)
        )
    )])
    
    fig.update_layout(
        title="Financial Metrics Summary",
        margin=dict(t=80, b=50),
        height=300
    )
    
    return fig

def create_sensitivity_plot(
    param_values: List[float],
    outcome_values: List[float],
    param_name: str,
    outcome_name: str
) -> go.Figure:
    """
    Create sensitivity analysis plot.
    
    Args:
        param_values: List of parameter values
        outcome_values: List of outcome values
        param_name: Parameter name
        outcome_name: Outcome name
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=param_values,
            y=outcome_values,
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=10)
        )
    )
    
    # Calculate simple linear regression for trendline
    z = np.polyfit(param_values, outcome_values, 1)
    p = np.poly1d(z)
    
    # Add trendline
    fig.add_trace(
        go.Scatter(
            x=param_values,
            y=p(param_values),
            mode="lines",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            name="Trend"
        )
    )
    
    # Calculate elasticity at the mean
    mid_idx = len(param_values) // 2
    mid_param = param_values[mid_idx]
    mid_outcome = outcome_values[mid_idx]
    
    if mid_param != 0 and mid_outcome != 0:
        # Calculate percentage change in outcome for each percentage change in parameter
        param_pct_change = [(p - mid_param) / mid_param for p in param_values]
        outcome_pct_change = [(o - mid_outcome) / mid_outcome for o in outcome_values]
        
        # Calculate elasticities
        elasticities = []
        for i in range(len(param_values)):
            if param_pct_change[i] != 0:
                elasticity = outcome_pct_change[i] / param_pct_change[i]
                elasticities.append(elasticity)
        
        if elasticities:
            avg_elasticity = sum(elasticities) / len(elasticities)
            
            # Add annotation for elasticity
            fig.add_annotation(
                x=param_values[-1],
                y=outcome_values[-1],
                text=f"Elasticity: {avg_elasticity:.2f}",
                showarrow=False,
                yshift=20
            )
    
    fig.update_layout(
        xaxis_title=param_name,
        yaxis_title=outcome_name,
        title=f"Sensitivity Analysis: {outcome_name} vs {param_name}",
        margin=dict(t=80, b=50),
        template="plotly_white"
    )
    
    return fig 