"""
Monte Carlo tab component for the Kerbside Model app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.model.monte_carlo import run_monte_carlo
from src.utils.config import (
    MAX_MONTE_CARLO_SIMULATIONS,
    DEFAULT_CHART_HEIGHT,
    DEFAULT_COLOR_SCHEME,
    CURRENCY_FORMAT
)
from src.utils.conversion_utils import format_currency


def render_monte_carlo_tab(model_results, model):
    """
    Render the Monte Carlo tab.
    
    Args:
        model_results: Dictionary of model results
        model: KerbsideModel instance for simulation
    """
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
            max_value=MAX_MONTE_CARLO_SIMULATIONS,
            value=200,
            step=100,
            help="More simulations provide better results but take longer"
        )
        
        run_mc_button = st.button("Run Simulation", use_container_width=True)
    
    # Run Monte Carlo simulation if requested
    if run_mc_button:
        with st.spinner(f"Running {n_simulations} simulations..."):
            # Use the new monte_carlo module instead of the model method
            mc_results = run_monte_carlo(model, n_simulations=n_simulations)
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
                labels={"avg_bill_impact": "Average Annual Bill Impact ($)"},
                color_discrete_sequence=[px.colors.sequential.Blues[5]]
            )
            
            # Format the mean value correctly
            mean_value = summary_stats["avg_bill_impact_mean"]
            mean_label = format_currency(mean_value)
            
            fig.add_vline(
                x=mean_value, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: {mean_label}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Average Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False,
                height=DEFAULT_CHART_HEIGHT
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                results_df,
                x="peak_bill_impact",
                nbins=20,
                title="Peak Annual Bill Impact",
                labels={"peak_bill_impact": "Peak Annual Bill Impact ($)"},
                color_discrete_sequence=[px.colors.sequential.Blues[5]]
            )
            
            # Format the mean value correctly
            mean_value = summary_stats["peak_bill_impact_mean"]
            mean_label = format_currency(mean_value)
            
            fig.add_vline(
                x=mean_value, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Mean: {mean_label}"
            )
            
            fig.update_layout(
                xaxis=dict(title="Peak Annual Bill Impact ($)"),
                yaxis=dict(title="Frequency"),
                showlegend=False,
                height=DEFAULT_CHART_HEIGHT
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        
        # Create a table of statistics for key metrics
        metrics = ["avg_bill_impact", "peak_bill_impact", "npv_bill_impact", "total_bill_impact"]
        metric_labels = {
            "avg_bill_impact": "Average Annual Bill Impact",
            "peak_bill_impact": "Peak Annual Bill Impact",
            "npv_bill_impact": "NPV of Bill Impacts",
            "total_bill_impact": "Total Bill Impact"
        }
        
        stats_data = []
        
        for metric in metrics:
            stats_data.append({
                "Metric": metric_labels.get(metric, metric),
                "Mean": format_currency(summary_stats[f"{metric}_mean"]),
                "Median": format_currency(summary_stats[f"{metric}_median"]),
                "Std Dev": format_currency(summary_stats[f"{metric}_std"]),
                "10th %ile": format_currency(summary_stats[f"{metric}_p10"]),
                "90th %ile": format_currency(summary_stats[f"{metric}_p90"])
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
                    coloraxis_showscale=False,
                    height=DEFAULT_CHART_HEIGHT
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