# Kerbside EV Charger Economic Model

A streamlined economic model for analyzing the deployment of electric vehicle chargers through a Regulated Asset Base (RAB) approach.

## Overview

The Kerbside Model is a simplified implementation of an EV charger economic model that analyzes:

- Financial impacts on customer bills
- Asset base evolution over time
- Market competition effects
- Parameter sensitivity through Monte Carlo simulations

This model consolidates multiple parameters and calculations into a single, unified approach that is more maintainable and easier to understand while maintaining the accuracy of the underlying economic analysis.

## Key Features

- **Simplified parameter structure**: Reduced parameter count focused on the most impactful ones
- **Integrated calculations**: Consolidated calculation methods with vectorized operations
- **Powerful visualizations**: Interactive charts showing key metrics and trends
- **Monte Carlo simulation**: Parameter sensitivity analysis to understand uncertainty
- **Market competition effects**: Analysis of private market displacement and innovation gaps

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/emil7051/kerbside_charger_model.git
   cd kerbside_charger_model
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:

```
streamlit run app.py
```

This will launch a web browser with the interactive model interface. Use the sidebar parameters to adjust model inputs and see the results update in real-time.

## Model Structure

The model is organized in a simple, modular structure:

- `src/model/kerbside_model.py`: The main model class encapsulating all calculations
- `app.py`: Streamlit web interface for interacting with the model

## Parameter Descriptions

- **Deployment Parameters**:
  - `chargers_per_year`: Number of chargers deployed annually
  - `deployment_years`: Number of years for the deployment phase
  - `deployment_delay`: Factor affecting deployment time (>1 means slower)

- **Financial Parameters**:
  - `capex_per_charger`: Capital cost per charger ($)
  - `opex_per_charger`: Annual operating cost per charger ($)
  - `asset_life`: Expected lifetime of charger assets (years)
  - `wacc`: Weighted Average Cost of Capital (%)
  - `cost_decline_rate`: Annual technology cost reduction (%)

- **Efficiency Parameters**:
  - `efficiency`: Operational efficiency factor (1.0 = fully efficient)
  - `efficiency_degradation`: Annual worsening of efficiency
  - `tech_obsolescence_rate`: Rate at which technology becomes obsolete

- **Market Parameters**:
  - `market_displacement`: Rate at which RAB displaces private market

## License

This project is licensed under the MIT License - see the LICENSE file for details. 