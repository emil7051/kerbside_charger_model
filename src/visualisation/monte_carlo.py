"""Monte Carlo visualisation functions for the EV charger model."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import math

def create_monte_carlo_histogram(
    results_df: pd.DataFrame,
    metric: str,
    title: Optional[str] = None,
    x_axis_title: Optional[str] = None
) -> go.Figure:
    """
    Create a histogram of Monte Carlo simulation results.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        metric: Column name of the metric to visualize
        title: Optional title for the plot
        x_axis_title: Optional x-axis title
        
    Returns:
        Plotly figure
    """
    # Get metric values
    values = results_df[metric].values
    
    # Calculate statistics
    mean_val = np.mean(values)
    median_val = np.median(values)
    p10_val = np.percentile(values, 10)
    p90_val = np.percentile(values, 90)
    
    # Create figure
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=30,
            marker_color="#1f77b4",
            opacity=0.7
        )
    )
    
    # Add vertical lines for key statistics
    for val, name, color in [
        (mean_val, f"Mean: {mean_val:.2f}", "#ff7f0e"),
        (median_val, f"Median: {median_val:.2f}", "#2ca02c"),
        (p10_val, f"P10: {p10_val:.2f}", "#d62728"),
        (p90_val, f"P90: {p90_val:.2f}", "#d62728")
    ]:
        fig.add_vline(
            x=val,
            line=dict(color=color, width=2, dash="dash"),
            annotation_text=name,
            annotation_position="top right"
        )
    
    # Set plot title
    if title is None:
        title = f"Monte Carlo Distribution: {metric}"
    
    # Set x-axis title
    if x_axis_title is None:
        x_axis_title = metric
    
    fig.update_layout(
        title=title,
        xaxis_title=x_axis_title,
        yaxis_title="Frequency",
        template="plotly_white",
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_parameter_scatter(
    results_df: pd.DataFrame,
    param_name: str,
    outcome_name: str
) -> go.Figure:
    """
    Create a scatter plot of parameter vs outcome.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        param_name: Column name of the parameter
        outcome_name: Column name of the outcome
        
    Returns:
        Plotly figure
    """
    # Extract parameter and outcome values
    param_col = f"param_{param_name}"
    
    # Check if columns exist
    if param_col not in results_df.columns or outcome_name not in results_df.columns:
        return None
    
    param_values = results_df[param_col].values
    outcome_values = results_df[outcome_name].values
    
    # Calculate correlation
    correlation = np.corrcoef(param_values, outcome_values)[0, 1]
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(
        go.Scatter(
            x=param_values,
            y=outcome_values,
            mode="markers",
            marker=dict(
                color="#1f77b4",
                size=8,
                opacity=0.6
            )
        )
    )
    
    # Add trendline using least squares regression
    z = np.polyfit(param_values, outcome_values, 1)
    p = np.poly1d(z)
    
    fig.add_trace(
        go.Scatter(
            x=[min(param_values), max(param_values)],
            y=p([min(param_values), max(param_values)]),
            mode="lines",
            line=dict(color="#ff7f0e", width=2),
            name=f"Trend (r={correlation:.2f})"
        )
    )
    
    # Add correlation annotation
    fig.add_annotation(
        x=max(param_values),
        y=min(outcome_values),
        text=f"Correlation: {correlation:.2f}",
        showarrow=False,
        xshift=-5,
        yshift=10,
        xanchor="right"
    )
    
    fig.update_layout(
        title=f"Sensitivity: {outcome_name} vs {param_name}",
        xaxis_title=param_name,
        yaxis_title=outcome_name,
        template="plotly_white",
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_correlation_heatmap(
    results_df: pd.DataFrame,
    outcome_metrics: List[str],
    param_list: Optional[List[str]] = None
) -> go.Figure:
    """
    Create a correlation heatmap between parameters and outcomes.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        outcome_metrics: List of outcome metrics to analyse
        param_list: Optional list of parameters to include
        
    Returns:
        Plotly figure
    """
    # Identify parameter columns
    if param_list is None:
        param_cols = [col for col in results_df.columns if col.startswith("param_")]
    else:
        param_cols = [f"param_{param}" for param in param_list]
        param_cols = [col for col in param_cols if col in results_df.columns]
    
    # Calculate correlation matrix
    corr_data = []
    param_names = [col.replace("param_", "") for col in param_cols]
    
    for outcome in outcome_metrics:
        if outcome not in results_df.columns:
            continue
            
        outcome_corrs = []
        for param_col in param_cols:
            corr = np.corrcoef(results_df[param_col], results_df[outcome])[0, 1]
            outcome_corrs.append(corr)
        
        corr_data.append(outcome_corrs)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_data,
        x=param_names,
        y=outcome_metrics,
        colorscale="RdBu_r",  # Red for negative, blue for positive
        zmid=0,  # Center colorscale at 0
        colorbar=dict(title="Correlation")
    ))
    
    # Add text annotations with correlation values
    for i, outcome in enumerate(outcome_metrics):
        for j, param in enumerate(param_names):
            corr_value = corr_data[i][j]
            text_color = "white" if abs(corr_value) > 0.4 else "black"
            
            fig.add_annotation(
                x=param,
                y=outcome,
                text=f"{corr_value:.2f}",
                showarrow=False,
                font=dict(color=text_color)
            )
    
    fig.update_layout(
        title="Parameter-Outcome Correlation Heatmap",
        xaxis_title="Model Parameters",
        yaxis_title="Outcome Metrics",
        template="plotly_white",
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_tornado_chart(
    results_df: pd.DataFrame,
    outcome_metric: str,
    top_n: int = 10
) -> go.Figure:
    """
    Create a tornado chart showing parameter sensitivities.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        outcome_metric: Outcome metric to analyse
        top_n: Number of top parameters to include
        
    Returns:
        Plotly figure
    """
    # Get parameter columns
    param_cols = [col for col in results_df.columns if col.startswith("param_")]
    
    # Calculate correlations
    correlations = {}
    for param_col in param_cols:
        param_name = param_col.replace("param_", "")
        corr = np.corrcoef(results_df[param_col], results_df[outcome_metric])[0, 1]
        correlations[param_name] = corr
    
    # Sort by absolute correlation and take top N
    sorted_params = sorted(
        correlations.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:top_n]
    
    params = [item[0] for item in sorted_params]
    corrs = [item[1] for item in sorted_params]
    
    # Create tornado chart
    fig = go.Figure()
    
    # Add bars
    colors = ["#1f77b4" if corr >= 0 else "#d62728" for corr in corrs]
    
    fig.add_trace(
        go.Bar(
            x=corrs,
            y=params,
            orientation="h",
            marker_color=colors
        )
    )
    
    fig.update_layout(
        title=f"Sensitivity Analysis: {outcome_metric}",
        xaxis_title="Correlation Coefficient",
        yaxis_title="Parameter",
        template="plotly_white",
        xaxis=dict(range=[-1, 1]),
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_outcome_box_plots(
    results_df: pd.DataFrame,
    outcome_metrics: List[str]
) -> go.Figure:
    """
    Create box plots for multiple outcome metrics.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        outcome_metrics: List of outcome metrics to analyse
        
    Returns:
        Plotly figure
    """
    # Create figure
    fig = go.Figure()
    
    # Add box plots for each metric
    for metric in outcome_metrics:
        if metric not in results_df.columns:
            continue
            
        # Normalise the values for better comparison
        values = results_df[metric].values
        mean = np.mean(values)
        std = np.std(values)
        
        if std > 0:
            normalized_values = (values - mean) / std
        else:
            normalized_values = values - mean
        
        fig.add_trace(
            go.Box(
                y=normalized_values,
                name=metric,
                boxpoints="all",
                jitter=0.3,
                pointpos=-1.8,
                marker=dict(size=3)
            )
        )
    
    fig.update_layout(
        title="Outcome Variability Comparison (Normalized)",
        yaxis_title="Standard Deviations from Mean",
        template="plotly_white",
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_scenario_comparison(
    scenarios: Dict[str, Dict[str, Any]],
    metrics: List[str]
) -> go.Figure:
    """
    Create a comparison chart for multiple scenarios.
    
    Args:
        scenarios: Dictionary of scenario results
        metrics: List of metrics to compare
        
    Returns:
        Plotly figure
    """
    # Extract data for plotting
    scenario_names = list(scenarios.keys())
    
    # Create subplots - one for each metric
    fig = make_subplots(
        rows=len(metrics),
        cols=1,
        subplot_titles=[m.replace("_", " ").title() for m in metrics],
        vertical_spacing=0.1
    )
    
    # Add bars for each scenario and metric
    for i, metric in enumerate(metrics):
        metric_key = f"{metric}_mean"
        
        values = []
        p10_values = []
        p90_values = []
        
        for scenario in scenario_names:
            stats = scenarios[scenario]["summary_stats"]
            if metric_key in stats:
                values.append(stats[metric_key])
                p10_values.append(stats.get(f"{metric}_p10", stats[metric_key] * 0.9))
                p90_values.append(stats.get(f"{metric}_p90", stats[metric_key] * 1.1))
            else:
                values.append(0)
                p10_values.append(0)
                p90_values.append(0)
        
        # Add bar chart
        fig.add_trace(
            go.Bar(
                x=scenario_names,
                y=values,
                name=metric if i == 0 else None,
                showlegend=i == 0,
                marker_color=px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
            ),
            row=i+1, col=1
        )
        
        # Add error bars
        fig.add_trace(
            go.Scatter(
                x=scenario_names,
                y=values,
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[p90 - val for val, p90 in zip(values, p90_values)],
                    arrayminus=[val - p10 for val, p10 in zip(values, p10_values)]
                ),
                mode="markers",
                marker=dict(color="rgba(0,0,0,0)"),
                showlegend=False
            ),
            row=i+1, col=1
        )
    
    fig.update_layout(
        height=300 * len(metrics),
        title_text="Scenario Comparison",
        template="plotly_white",
        margin=dict(t=80, b=50)
    )
    
    return fig

def create_monte_carlo_dashboard(
    results_df: pd.DataFrame,
    summary_stats: Dict[str, Any]
) -> Dict[str, go.Figure]:
    """
    Create a dashboard with Monte Carlo simulation visualisations.
    
    Args:
        results_df: DataFrame with Monte Carlo results
        summary_stats: Summary statistics dictionary
        
    Returns:
        Dictionary of Plotly figures
    """
    figures = {}
    
    # Key metrics to visualize
    metrics = [
        "total_bill_impact",
        "avg_annual_bill",
        "npv_revenue",
        "peak_rab"
    ]
    
    # Create histograms for key metrics
    for metric in metrics:
        if metric in results_df.columns:
            figures[f"{metric}_histogram"] = create_monte_carlo_histogram(
                results_df, metric
            )
    
    # Create correlation heatmap
    figures["correlation_heatmap"] = create_correlation_heatmap(
        results_df, metrics
    )
    
    # Create tornado charts for key metrics
    for metric in metrics:
        if metric in results_df.columns:
            figures[f"{metric}_tornado"] = create_tornado_chart(
                results_df, metric
            )
    
    # Create box plots
    figures["outcome_box_plots"] = create_outcome_box_plots(
        results_df, metrics
    )
    
    # Create combined dashboard
    fig_combined = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Bill Impact Distribution",
            "Parameter Sensitivities",
            "NPV Distribution",
            "Parameter Correlations"
        ],
        vertical_spacing=0.12,  # Increased from default
        specs=[
            [{"type": "histogram"}, {"type": "bar"}],
            [{"type": "histogram"}, {"type": "heatmap"}]
        ]
    )
    
    # Bill impact histogram
    if "total_bill_impact" in results_df.columns:
        values = results_df["total_bill_impact"].values
        fig_combined.add_trace(
            go.Histogram(
                x=values,
                nbinsx=20,
                marker_color="#1f77b4"
            ),
            row=1, col=1
        )
        
        # Add mean line
        mean_val = np.mean(values)
        fig_combined.add_vline(
            x=mean_val,
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            row=1, col=1
        )
    
    # Parameter sensitivities (tornado)
    if "total_bill_impact" in results_df.columns:
        # Get parameter columns
        param_cols = [col for col in results_df.columns if col.startswith("param_")]
        
        # Calculate correlations
        correlations = {}
        for param_col in param_cols:
            param_name = param_col.replace("param_", "")
            corr = np.corrcoef(results_df[param_col], results_df["total_bill_impact"])[0, 1]
            correlations[param_name] = corr
        
        # Sort by absolute correlation and take top 5
        sorted_params = sorted(
            correlations.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        params = [item[0] for item in sorted_params]
        corrs = [item[1] for item in sorted_params]
        
        # Add bars
        colors = ["#1f77b4" if corr >= 0 else "#d62728" for corr in corrs]
        
        fig_combined.add_trace(
            go.Bar(
                x=corrs,
                y=params,
                orientation="h",
                marker_color=colors
            ),
            row=1, col=2
        )
    
    # NPV histogram
    if "npv_revenue" in results_df.columns:
        values = results_df["npv_revenue"].values
        fig_combined.add_trace(
            go.Histogram(
                x=values,
                nbinsx=20,
                marker_color="#2ca02c"
            ),
            row=2, col=1
        )
        
        # Add mean line
        mean_val = np.mean(values)
        fig_combined.add_vline(
            x=mean_val,
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            row=2, col=1
        )
    
    # Parameter correlations (heatmap)
    metrics = ["total_bill_impact", "npv_revenue"]
    metrics = [m for m in metrics if m in results_df.columns]
    
    if metrics:
        # Identify parameter columns and select top 5 by correlation magnitude
        param_cols = [col for col in results_df.columns if col.startswith("param_")]
        param_names = [col.replace("param_", "") for col in param_cols]
        
        corr_data = []
        for outcome in metrics:
            outcome_corrs = []
            for param_col in param_cols:
                corr = np.corrcoef(results_df[param_col], results_df[outcome])[0, 1]
                outcome_corrs.append(corr)
            
            corr_data.append(outcome_corrs)
        
        # Create heatmap
        fig_combined.add_trace(
            go.Heatmap(
                z=corr_data,
                x=param_names,
                y=metrics,
                colorscale="RdBu_r",
                zmid=0
            ),
            row=2, col=2
        )
    
    fig_combined.update_layout(
        height=800,
        title_text="Monte Carlo Simulation Results",
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