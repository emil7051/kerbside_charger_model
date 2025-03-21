"""Configuration parameters for the EV charger model."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelParameters:
    """Core parameters for the EV charger model."""
    chargers_per_year: int = 5000
    capex_per_charger: float = 6000
    opex_per_charger: float = 500
    asset_life: int = 8
    wacc_1_to_5: float = 0.058
    wacc_6_to_10: float = 0.06
    wacc_11_to_15: float = 0.055
    customer_base: int = 1800000
    third_party_revenue: float = 100
    shared_asset_offset: float = 0

@dataclass
class EnhancedParameters(ModelParameters):
    """Additional parameters for the enhanced model."""
    efficiency_factor: float = 1.0
    efficiency_degradation: float = 0.0
    deployment_delay: float = 1.0
    cost_escalation: float = 1.0
    operational_efficiency: float = 1.0
    private_market_displacement: float = 0.0
    innovation_rate: float = 0.02
    monopoly_innovation_rate: float = 0.01
    tech_obsolescence_rate: float = 0.05
    demand_utilization: float = 0.7
    utilization_growth_rate: float = 0.05
    use_risk_premium: bool = True
    risk_premium: float = 0.01
    cost_decline_rate: float = 0.03
    ev_adoption_rate: float = 0.15
    environmental_benefit_per_charger: float = 250
    include_environmental_benefits: bool = False

def create_params_from_dict(param_dict: Dict[str, Any], enhanced: bool = False) -> ModelParameters:
    """Create a parameters object from a dictionary."""
    param_class = EnhancedParameters if enhanced else ModelParameters
    return param_class(**{k.lower(): v for k, v in param_dict.items()}) 