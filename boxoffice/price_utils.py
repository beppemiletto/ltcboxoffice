"""
Utility module for price code management.
Centralizes price code definitions and array handling to avoid hardcoded values.
"""

# Price code definitions
PRICE_CODES = {
    0: {'name': 'Gratuito', 'is_subscription': False},
    1: {'name': 'Ridotto', 'is_subscription': False},
    2: {'name': 'Intero', 'is_subscription': False},
    3: {'name': 'Abbonamento R4', 'short_name': 'R4', 'is_subscription': True},
    4: {'name': 'Abbonamento R8', 'short_name': 'R8', 'is_subscription': True},
    5: {'name': 'Abbonamento I4', 'short_name': 'I4', 'is_subscription': True},
    6: {'name': 'Abbonamento I8', 'short_name': 'I8', 'is_subscription': True},
}

# Number of price codes
NUM_PRICE_CODES = len(PRICE_CODES)

# Legacy arrays for backward compatibility
INGRESSI_NAMES = [PRICE_CODES[i]['name'] for i in range(NUM_PRICE_CODES)]
INGRESSI_SHORT_NAMES = [
    PRICE_CODES[i].get('short_name', PRICE_CODES[i]['name']) 
    for i in range(NUM_PRICE_CODES)
]


def get_price_name(price_code):
    """Get the full name for a price code."""
    return PRICE_CODES.get(price_code, {}).get('name', 'Unknown')


def get_price_short_name(price_code):
    """Get the short name for a price code."""
    return PRICE_CODES.get(price_code, {}).get('short_name', 
                                                PRICE_CODES.get(price_code, {}).get('name', 'Unknown'))


def is_subscription(price_code):
    """Check if a price code is a subscription."""
    return PRICE_CODES.get(price_code, {}).get('is_subscription', False)


def extend_price_array(base_array, default_value=0.0):
    """
    Extend a price array to support all price codes.
    
    Args:
        base_array: List with 3 elements [gratuito, ridotto, intero]
        default_value: Value to use for subscription codes (default: 0.0)
    
    Returns:
        Extended list with NUM_PRICE_CODES elements
    """
    if len(base_array) >= NUM_PRICE_CODES:
        return base_array
    
    extension = [default_value] * (NUM_PRICE_CODES - len(base_array))
    return base_array + extension


def safe_price_access(price_array, price_code, default_value=0.0):
    """
    Safely access a price array with bounds checking.
    
    Args:
        price_array: The array to access
        price_code: The index to access
        default_value: Value to return if index is out of bounds
    
    Returns:
        The value at price_code index or default_value
    """
    if 0 <= price_code < len(price_array):
        return price_array[price_code]
    return default_value


def get_price_choices():
    """
    Get price choices for Django model field.
    
    Returns:
        List of tuples [(code, name), ...] suitable for Django choices
    """
    return [(code, info['name']) for code, info in PRICE_CODES.items()]
