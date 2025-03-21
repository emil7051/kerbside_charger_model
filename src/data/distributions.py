"""Monte Carlo distribution definitions for the EV charger model."""

from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats

# Define parameter distributions for Monte Carlo simulations
PARAMETER_DISTRIBUTIONS = {
    # Base parameters
    "ChargersPerYear": {
        "distribution": "normal",
        "mean": 5000,
        "std": 500,
        "min": 3000,
        "max": 7000,
    },
    "CapExPerCharger": {
        "distribution": "triangular",
        "mode": 6000,
        "min": 4500,
        "max": 8000,
    },
    "OpExPerCharger": {
        "distribution": "triangular",
        "mode": 500,
        "min": 350,
        "max": 700,
    },
    "AssetLife": {
        "distribution": "discrete",
        "values": [6, 7, 8, 9, 10],
        "weights": [0.1, 0.2, 0.4, 0.2, 0.1],
    },
    "WACC1to5": {
        "distribution": "normal",
        "mean": 0.058,
        "std": 0.005,
        "min": 0.04,
        "max": 0.08,
    },
    
    # Efficiency parameters
    "EfficiencyFactor": {
        "distribution": "triangular",
        "mode": 1.0,
        "min": 0.9,
        "max": 1.3,
    },
    "EfficiencyDegradation": {
        "distribution": "triangular",
        "mode": 0.0,
        "min": 0.0,
        "max": 0.03,
    },
    "OperationalEfficiency": {
        "distribution": "triangular",
        "mode": 1.0,
        "min": 0.7,
        "max": 1.1,
    },
    
    # Market parameters
    "PrivateMarketDisplacement": {
        "distribution": "triangular",
        "mode": 0.3,
        "min": 0.0,
        "max": 0.7,
    },
    "InnovationRate": {
        "distribution": "triangular",
        "mode": 0.02,
        "min": 0.01,
        "max": 0.04,
    },
    "MonopolyInnovationRate": {
        "distribution": "triangular",
        "mode": 0.01,
        "min": 0.005,
        "max": 0.02,
    },
    
    # Technical parameters
    "DemandUtilisation": {
        "distribution": "triangular",
        "mode": 0.7,
        "min": 0.5,
        "max": 0.9,
    },
    "EVAdoptionRate": {
        "distribution": "triangular",
        "mode": 0.15,
        "min": 0.1,
        "max": 0.25,
    },
}

def generate_parameter_sample(
    param_name: str, 
    param_dist: Dict[str, Any],
    rng: Optional[np.random.Generator] = None
) -> float:
    """
    Generate a random sample for a parameter based on its distribution.
    
    Args:
        param_name: Name of the parameter
        param_dist: Dictionary describing the distribution
        rng: Random number generator (optional)
    
    Returns:
        A random sample from the distribution
    """
    if rng is None:
        rng = np.random.default_rng()
    
    dist_type = param_dist["distribution"]
    
    if dist_type == "normal":
        mean = param_dist["mean"]
        std = param_dist["std"]
        min_val = param_dist.get("min", float("-inf"))
        max_val = param_dist.get("max", float("inf"))
        
        # Keep sampling until we get a value within range
        while True:
            sample = rng.normal(mean, std)
            if min_val <= sample <= max_val:
                return sample
    
    elif dist_type == "triangular":
        mode = param_dist["mode"]
        min_val = param_dist["min"]
        max_val = param_dist["max"]
        
        # Convert to scipy parameters
        c = (mode - min_val) / (max_val - min_val)
        return rng.triangular(min_val, mode, max_val)
    
    elif dist_type == "uniform":
        min_val = param_dist["min"]
        max_val = param_dist["max"]
        return rng.uniform(min_val, max_val)
    
    elif dist_type == "discrete":
        values = param_dist["values"]
        weights = param_dist.get("weights", None)
        return rng.choice(values, p=weights)
    
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")

def generate_parameter_set(
    rng: Optional[np.random.Generator] = None
) -> Dict[str, Any]:
    """
    Generate a complete set of parameters for a Monte Carlo simulation.
    
    Args:
        rng: Random number generator (optional)
    
    Returns:
        Dictionary of parameter values
    """
    if rng is None:
        rng = np.random.default_rng()
    
    params = {}
    for param_name, param_dist in PARAMETER_DISTRIBUTIONS.items():
        params[param_name] = generate_parameter_sample(param_name, param_dist, rng)
    
    return params 