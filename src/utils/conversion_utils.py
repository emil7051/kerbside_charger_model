"""
Utility functions for parameter conversions and transformations.
"""

def percentage_to_decimal(percentage_value):
    """
    Convert a percentage value to its decimal equivalent.
    
    Args:
        percentage_value (float): The percentage value (e.g., 5.95 for 5.95%)
        
    Returns:
        float: The decimal equivalent (e.g., 0.0595)
    """
    return percentage_value / 100.0

def format_currency(value, millions=False):
    """
    Format a numeric value as currency.
    
    Args:
        value (float): The value to format
        millions (bool): Whether to display in millions
        
    Returns:
        str: Formatted currency string
    """
    if millions:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:.2f}"

def format_percentage(value):
    """
    Format a decimal value as percentage.
    
    Args:
        value (float): The decimal value (e.g., 0.0595)
        
    Returns:
        str: Formatted percentage string (e.g., "5.95%")
    """
    return f"{value * 100:.2f}%" 