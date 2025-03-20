# Kerbside EV Charger Financial Model

A sophisticated financial modeling tool for analyzing Regulated Asset Base (RAB) approaches to electric vehicle charging infrastructure.

## Overview

This Streamlit application provides a comprehensive financial model for assessing the economic impact of implementing a Regulated Asset Base (RAB) approach to electric vehicle charging infrastructure deployment. The model evaluates various critical factors including:

- **Financial Overview**: Key financial metrics including revenue requirements, bill impacts, and returns on investment
- **Income Distribution Impact**: Analysis of how costs may disproportionately affect different income brackets
- **Market Competition Analysis**: Examination of potential market displacement and competitive effects
- **Technology Evolution**: Assessment of technological obsolescence and innovation gaps
- **Environmental Benefits**: Quantification of environmental benefits from EV charging infrastructure
- **Risk Assessment**: Monte Carlo simulation for robust risk analysis
- **Scenario Comparison**: Side-by-side comparison of multiple deployment scenarios

## Features

- **Interactive Dashboard**: Adjust parameters and immediately see impacts through an intuitive interface
- **Monte Carlo Simulation**: Robust risk assessment through probabilistic modeling
- **Scenario Analysis**: Compare different deployment strategies side-by-side
- **Distributional Impact Analysis**: Understand the regressive nature of bill impacts
- **Market Competition Modeling**: Assess potential displacement of private investment
- **Technology Obsolescence Modeling**: Account for technological change over the asset lifecycle
- **Environmental Benefit Calculation**: Quantify CO2 reduction and other environmental benefits

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kerbside_charger_model.git
cd kerbside_charger_model
```

2. Create a virtual environment and activate it:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run ev_charger_model.py
```

2. Adjust model parameters using the sidebar controls:
   - Number of chargers per year
   - Capital and operating expenditures
   - Weighted average cost of capital
   - Efficiency factors
   - Technology obsolescence rates
   - Environmental benefit factors

3. Navigate between tabs to explore different aspects of the analysis:
   - Financial Overview
   - Income Distribution Impact
   - Market Competition Analysis
   - Technology & Environment
   - Risk Assessment
   - Scenario Comparison

## Model Parameters

- **Basic Parameters**: Number of chargers, costs, WACC, customer base
- **Efficiency Factors**: Operational efficiency, cost escalation
- **Technological Factors**: Tech obsolescence rate, innovation rates
- **Market Effects**: Private market displacement
- **Environmental Factors**: CO2 reduction per charger

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This model builds upon financial modeling best practices and regulatory approaches to infrastructure investment. 