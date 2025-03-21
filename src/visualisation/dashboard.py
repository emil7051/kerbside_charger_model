"""Dashboard layout and configuration for the EV charger model."""

import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from ..data.defaults import DEFAULT_PARAMS, INCOME_QUINTILES
from ..data.scenarios import SCENARIOS
from ..model.base_model import run_ev_charger_model
from ..model.distributional import calculate_distributional_impact, calculate_lifetime_distributional_impact
from ..model.competitive import run_comparative_scenario
from ..model.monte_carlo import run_monte_carlo_simulation, run_scenario_comparison
from ..model.efficiency_model import calculate_efficiency_metrics, run_efficiency_sensitivity

from .base_charts import create_financial_summary, create_financial_metrics_table, create_sensitivity_plot
from .distributional import create_distributional_dashboard
from .competitive import create_competitive_dashboard
from .monte_carlo import create_monte_carlo_dashboard, create_scenario_comparison

def create_sidebar_controls() -> Dict[str, Any]:
    """Create sidebar controls and return parameter dictionary."""
    st.sidebar.title('Model Configuration')
    
    # Scenario selector
    scenario_name = st.sidebar.selectbox(
        'Select Scenario',
        list(SCENARIOS.keys()),
        index=0
    )
    
    # Get selected scenario parameters
    params = SCENARIOS[scenario_name].copy()
    
    # Allow modification of key parameters
    st.sidebar.subheader('Basic Parameters')
    
    params['ChargersPerYear'] = st.sidebar.number_input(
        'Chargers Per Year',
        min_value=1000,
        max_value=10000,
        value=params['ChargersPerYear']
    )
    
    params['CapExPerCharger'] = st.sidebar.number_input(
        'CapEx Per Charger ($)',
        min_value=3000,
        max_value=10000,
        value=params['CapExPerCharger']
    )
    
    params['OpExPerCharger'] = st.sidebar.number_input(
        'OpEx Per Charger ($)',
        min_value=100,
        max_value=1000,
        value=params['OpExPerCharger']
    )
    
    params['AssetLife'] = st.sidebar.number_input(
        'Asset Life (years)',
        min_value=5,
        max_value=15,
        value=params['AssetLife']
    )
    
    # Advanced parameter sections (collapsible)
    with st.sidebar.expander('Financing Parameters'):
        params['WACC1to5'] = st.slider(
            'WACC Years 1-5',
            min_value=0.03,
            max_value=0.09,
            value=params['WACC1to5'],
            format='%.3f'
        )
        
        params['WACC6to10'] = st.slider(
            'WACC Years 6-10',
            min_value=0.03,
            max_value=0.09,
            value=params['WACC6to10'],
            format='%.3f'
        )
        
        params['WACC11to15'] = st.slider(
            'WACC Years 11-15',
            min_value=0.03,
            max_value=0.09,
            value=params['WACC11to15'],
            format='%.3f'
        )
    
    with st.sidebar.expander('Efficiency Parameters'):
        params['EfficiencyFactor'] = st.slider(
            'Efficiency Factor',
            min_value=0.8,
            max_value=1.5,
            value=params['EfficiencyFactor'],
            format='%.2f'
        )
        
        params['EfficiencyDegradation'] = st.slider(
            'Efficiency Degradation',
            min_value=0.0,
            max_value=0.05,
            value=params['EfficiencyDegradation'],
            format='%.3f'
        )
        
        params['OperationalEfficiency'] = st.slider(
            'Operational Efficiency',
            min_value=0.7,
            max_value=1.3,
            value=params['OperationalEfficiency'],
            format='%.2f'
        )
        
        params['DeploymentDelay'] = st.slider(
            'Deployment Delay',
            min_value=1.0,
            max_value=2.0,
            value=params['DeploymentDelay'],
            format='%.2f'
        )
    
    with st.sidebar.expander('Market Parameters'):
        params['PrivateMarketDisplacement'] = st.slider(
            'Private Market Displacement',
            min_value=0.0,
            max_value=1.0,
            value=params['PrivateMarketDisplacement'],
            format='%.2f'
        )
        
        params['InnovationRate'] = st.slider(
            'Competitive Innovation Rate',
            min_value=0.01,
            max_value=0.05,
            value=params['InnovationRate'],
            format='%.3f'
        )
        
        params['MonopolyInnovationRate'] = st.slider(
            'Monopoly Innovation Rate',
            min_value=0.0,
            max_value=0.03,
            value=params['MonopolyInnovationRate'],
            format='%.3f'
        )
    
    with st.sidebar.expander('Environmental Parameters'):
        params['IncludeEnvironmentalBenefits'] = st.checkbox(
            'Include Environmental Benefits',
            value=params['IncludeEnvironmentalBenefits']
        )
        
        params['EnvironmentalBenefitPerCharger'] = st.number_input(
            'Environmental Benefit Per Charger ($)',
            min_value=0,
            max_value=500,
            value=params['EnvironmentalBenefitPerCharger']
        )
    
    return params

def display_financial_overview_tab(params: Dict[str, Any]):
    """Display the financial overview tab."""
    st.header('Financial Overview')
    
    # Run the model
    (rollout_df, depreciation_df, rab_df, revenue_df, summary_stats, _, _) = run_ev_charger_model(params)
    
    # Display key financial metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            'Total Chargers',
            f"{int(summary_stats['Total Chargers']):,}"
        )
    
    with col2:
        st.metric(
            'NPV of Revenue Requirement',
            f"${summary_stats['NPV of Revenue Requirement'] / 1e6:.2f}M"
        )
    
    with col3:
        st.metric(
            'Average Annual Bill Impact',
            f"${summary_stats['Average Annual Bill Impact']:.2f}"
        )
    
    # Create visualisation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Revenue Requirements", 
        "Bill Impact", 
        "Regulated Asset Base", 
        "Charger Deployment"
    ])
    
    # Create visualizations
    figures = create_financial_summary(revenue_df, rollout_df, rab_df, summary_stats)
    
    with tab1:
        st.plotly_chart(figures["revenue_requirements"], use_container_width=True)
    
    with tab2:
        st.plotly_chart(figures["bill_impact"], use_container_width=True)
    
    with tab3:
        st.plotly_chart(figures["rab_evolution"], use_container_width=True)
    
    with tab4:
        st.plotly_chart(figures["charger_deployment"], use_container_width=True)
    
    # Display metrics table
    with st.expander("Financial Metrics Details"):
        metrics_table = create_financial_metrics_table(summary_stats)
        st.plotly_chart(metrics_table, use_container_width=True)
        
        # Display RAB details
        st.subheader("Regulated Asset Base Details")
        st.dataframe(rab_df)
    
    # Sensitivity analysis
    st.subheader("Sensitivity Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        param_to_analyze = st.selectbox(
            "Select Parameter",
            ["CapExPerCharger", "OpExPerCharger", "AssetLife", "WACC1to5", "EfficiencyFactor"]
        )
    
    with col2:
        outcome_to_analyze = st.selectbox(
            "Select Outcome",
            ["Average Annual Bill Impact", "NPV of Revenue Requirement"]
        )
    
    # Run sensitivity analysis
    param_range = []
    original_value = params[param_to_analyze]
    
    # Create parameter range (±30%)
    if param_to_analyze in ["WACC1to5", "EfficiencyFactor"]:
        # For rates and factors, use smaller absolute changes
        min_val = max(original_value - 0.03, 0.01)
        max_val = original_value + 0.03
        param_range = np.linspace(min_val, max_val, 10)
    else:
        # For other parameters, use percentage changes
        min_val = original_value * 0.7
        max_val = original_value * 1.3
        param_range = np.linspace(min_val, max_val, 10)
    
    # Run model for each parameter value
    outcome_values = []
    
    for value in param_range:
        test_params = params.copy()
        test_params[param_to_analyze] = value
        test_params["skip_ext_calcs"] = True
        
        (_, _, _, _, test_summary, _, _) = run_ev_charger_model(test_params)
        outcome_values.append(test_summary[outcome_to_analyze])
    
    # Create sensitivity plot
    sensitivity_plot = create_sensitivity_plot(
        param_range,
        outcome_values,
        param_to_analyze,
        outcome_to_analyze
    )
    
    st.plotly_chart(sensitivity_plot, use_container_width=True)

def display_distributional_impact_tab(params: Dict[str, Any]):
    """Display the distributional impact tab."""
    st.header('Distributional Impact Analysis')
    
    # Run the model
    (_, _, _, revenue_df, summary_stats, _, _) = run_ev_charger_model(params)
    
    # Calculate distributional impact
    dist_df = calculate_distributional_impact(revenue_df)
    summary_df, df_by_year = calculate_lifetime_distributional_impact(revenue_df)
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        regressivity_ratio = dist_df.iloc[0]["regressivity_ratio_income"]
        st.metric(
            'Regressivity Ratio',
            f"{regressivity_ratio:.2f}x"
        )
    
    with col2:
        q1_impact = dist_df[dist_df["quintile"] == "Q1"].iloc[0]["impact_pct_income"]
        st.metric(
            'Lowest Quintile Impact',
            f"{q1_impact:.3f}% of income"
        )
    
    with col3:
        q5_impact = dist_df[dist_df["quintile"] == "Q5"].iloc[0]["impact_pct_income"]
        st.metric(
            'Highest Quintile Impact',
            f"{q5_impact:.3f}% of income"
        )
    
    # Create visualisation tabs
    tab1, tab2, tab3 = st.tabs([
        "Income Impact", 
        "Bill Impact", 
        "Lifetime Impact"
    ])
    
    # Create visualizations
    figures = create_distributional_dashboard(dist_df, df_by_year)
    
    with tab1:
        st.plotly_chart(figures["income_impact"], use_container_width=True)
    
    with tab2:
        st.plotly_chart(figures["bill_impact"], use_container_width=True)
    
    with tab3:
        st.plotly_chart(figures["lifetime_impact"], use_container_width=True)
    
    # Display full dashboard
    st.subheader("Distributional Impact Dashboard")
    st.plotly_chart(figures["dashboard"], use_container_width=True)
    
    # Display raw data
    with st.expander("View Raw Data"):
        st.subheader("Income Quintile Data")
        st.dataframe(dist_df)
        
        st.subheader("Lifetime Impact Data")
        st.dataframe(summary_df)

def display_competitive_market_tab(params: Dict[str, Any]):
    """Display the competitive market effects tab."""
    st.header('Competitive Market Effects')
    
    # Run the competitive market analysis
    results = run_comparative_scenario(params)
    
    # Extract results
    market_df = results["market_df"]
    innovation_df = results["innovation_df"]
    combined_df = results["combined_df"]
    metrics = results["metrics"]
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            'Market Growth',
            f"{metrics['market_growth_percentage']:.1f}%",
            delta=f"{int(metrics['total_chargers_with_rab'] - metrics['total_chargers_without_rab']):,} chargers"
        )
    
    with col2:
        st.metric(
            'Private Market Displacement',
            f"{metrics['private_displacement_percentage']:.1f}%",
            delta=f"{int(metrics['total_private_without_rab'] - metrics['total_private_with_rab']):,} chargers",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            'Innovation Gap',
            f"{metrics['final_innovation_gap_pct']:.1f}%",
            delta=f"${metrics['total_innovation_cost'] / 1e6:.2f}M cost",
            delta_color="inverse"
        )
    
    # Create visualisation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Market Development", 
        "Market Composition", 
        "Innovation Impact", 
        "Displacement Effect"
    ])
    
    # Create visualizations
    figures = create_competitive_dashboard(market_df, innovation_df, metrics)
    
    with tab1:
        st.plotly_chart(figures["market_development"], use_container_width=True)
    
    with tab2:
        st.plotly_chart(figures["market_composition"], use_container_width=True)
    
    with tab3:
        st.plotly_chart(figures["innovation_impact"], use_container_width=True)
    
    with tab4:
        st.plotly_chart(figures["displacement_effect"], use_container_width=True)
    
    # Display full dashboard
    st.subheader("Competitive Market Dashboard")
    st.plotly_chart(figures["dashboard"], use_container_width=True)
    
    # Display metrics table
    with st.expander("Competitive Market Metrics"):
        st.plotly_chart(figures["metrics_table"], use_container_width=True)
        
        # Display market data
        st.subheader("Market Development Data")
        st.dataframe(market_df)

def display_monte_carlo_tab(params: Dict[str, Any]):
    """Display the Monte Carlo simulation tab."""
    st.header('Monte Carlo Simulation')
    
    # Simulation parameters
    col1, col2 = st.columns(2)
    
    with col1:
        n_simulations = st.slider(
            "Number of Simulations",
            min_value=100,
            max_value=1000,
            value=200,
            step=100
        )
    
    with col2:
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=10000,
            value=42
        )
    
    # Run simulation
    with st.spinner("Running Monte Carlo simulation..."):
        results_df, summary_stats = run_monte_carlo_simulation(
            params,
            n_simulations=n_simulations,
            seed=seed
        )
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            'Average Bill Impact',
            f"${summary_stats['avg_annual_bill_mean']:.2f}",
            delta=f"±${summary_stats['avg_annual_bill_std']:.2f}"
        )
    
    with col2:
        st.metric(
            'NPV Range',
            f"${summary_stats['npv_revenue_mean'] / 1e6:.2f}M",
            delta=f"P10-P90: ${summary_stats['npv_revenue_p10'] / 1e6:.2f}M - ${summary_stats['npv_revenue_p90'] / 1e6:.2f}M"
        )
    
    with col3:
        if 'regressivity_ratio_mean' in summary_stats:
            st.metric(
                'Regressivity Ratio',
                f"{summary_stats['regressivity_ratio_mean']:.2f}x",
                delta=f"±{summary_stats['regressivity_ratio_std']:.2f}"
            )
    
    # Create visualisation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Bill Impact Distribution", 
        "Parameter Sensitivities", 
        "Outcome Distributions", 
        "Correlation Analysis"
    ])
    
    # Create visualizations
    figures = create_monte_carlo_dashboard(results_df, summary_stats)
    
    with tab1:
        st.plotly_chart(figures["total_bill_impact_histogram"], use_container_width=True)
    
    with tab2:
        if "total_bill_impact_tornado" in figures:
            st.plotly_chart(figures["total_bill_impact_tornado"], use_container_width=True)
    
    with tab3:
        st.plotly_chart(figures["outcome_box_plots"], use_container_width=True)
    
    with tab4:
        st.plotly_chart(figures["correlation_heatmap"], use_container_width=True)
    
    # Display full dashboard
    st.subheader("Monte Carlo Dashboard")
    st.plotly_chart(figures["dashboard"], use_container_width=True)
    
    # Display raw results
    with st.expander("View Simulation Results"):
        st.dataframe(results_df)

def display_scenario_comparison_tab():
    """Display the scenario comparison tab."""
    st.header('Scenario Comparison')
    
    # Select scenarios
    scenarios_to_compare = st.multiselect(
        "Select Scenarios to Compare",
        list(SCENARIOS.keys()),
        default=["Baseline", "High Efficiency", "Low Efficiency"]
    )
    
    if not scenarios_to_compare:
        st.warning("Please select at least one scenario to compare.")
        return
    
    # Select metrics
    metrics_to_compare = st.multiselect(
        "Select Metrics to Compare",
        [
            "avg_annual_bill", 
            "npv_revenue", 
            "total_chargers", 
            "regressivity_ratio", 
            "private_displacement_pct", 
            "final_innovation_gap_pct"
        ],
        default=["avg_annual_bill", "total_chargers", "regressivity_ratio"]
    )
    
    if not metrics_to_compare:
        st.warning("Please select at least one metric to compare.")
        return
    
    # Run simulations for selected scenarios
    with st.spinner("Running simulations for selected scenarios..."):
        scenario_params = {name: SCENARIOS[name] for name in scenarios_to_compare}
        
        # Keep simulation small for speed
        scenario_results = run_scenario_comparison(
            scenario_params,
            n_simulations=100,
            include_distributional=True,
            include_competitive=True,
            seed=42
        )
    
    # Create comparison chart
    comparison_chart = create_scenario_comparison(
        scenario_results,
        metrics_to_compare
    )
    
    st.plotly_chart(comparison_chart, use_container_width=True)
    
    # Display scenario details
    with st.expander("Scenario Details"):
        for scenario_name in scenarios_to_compare:
            st.subheader(scenario_name)
            
            # Display key parameters that differ from baseline
            baseline = SCENARIOS["Baseline"]
            current = SCENARIOS[scenario_name]
            
            differences = {}
            for key, value in current.items():
                if key in baseline and value != baseline[key]:
                    differences[key] = (baseline[key], value)
            
            if differences:
                diff_data = []
                for key, (baseline_val, current_val) in differences.items():
                    diff_data.append({
                        "Parameter": key,
                        "Baseline Value": baseline_val,
                        "Scenario Value": current_val
                    })
                
                st.dataframe(pd.DataFrame(diff_data))
            else:
                st.write("No differences from baseline")

def render_dashboard():
    """Render the main dashboard."""
    st.set_page_config(
        page_title="EV Charger RAB Model",
        page_icon="🔌",
        layout="wide"
    )
    
    # App title
    st.title('Enhanced EV Charger RAB Model')
    st.markdown("""
    This application models the economic and distributional impacts of regulated asset base (RAB) 
    approaches to EV charger deployment.
    """)
    
    # Create sidebar controls
    params = create_sidebar_controls()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Financial Overview",
        "Distributional Impacts",
        "Competitive Market Effects",
        "Monte Carlo Simulation",
        "Scenario Comparison"
    ])
    
    # Render each tab
    with tab1:
        display_financial_overview_tab(params)
    
    with tab2:
        display_distributional_impact_tab(params)
    
    with tab3:
        display_competitive_market_tab(params)
    
    with tab4:
        display_monte_carlo_tab(params)
    
    with tab5:
        display_scenario_comparison_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Enhanced EV Charger RAB Model • Built with Streamlit • "
        "[Model Documentation](https://github.com/yourusername/ev-charger-model)"
    ) 