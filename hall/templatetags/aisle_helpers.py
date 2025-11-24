"""
Template tags and filters for rendering venue aisles (corridors)
"""
from django import template

register = template.Library()


@register.filter
def has_horizontal_aisle_after(aisles, args):
    """
    Check if there's a horizontal aisle after a specific seat in a row.
    Usage: {% if aisles|has_horizontal_aisle_after:"H,10" %}

    Args:
        aisles: dict with 'horizontal' and 'vertical' keys
        args: string "row_name,seat_number"

    Returns:
        dict with aisle info or None
    """
    if not aisles or 'horizontal' not in aisles:
        return None

    try:
        row_name, seat_num = args.split(',')
        seat_num = int(seat_num)
    except (ValueError, AttributeError):
        return None

    horizontal_aisles = aisles.get('horizontal', [])

    for aisle in horizontal_aisles:
        # Check if this aisle applies to this row
        applies_to_rows = aisle.get('applies_to_rows', [])
        if applies_to_rows != '*' and row_name not in applies_to_rows:
            continue

        # Check if aisle is after this seat number
        if aisle.get('position') == 'after_seat' and aisle.get('seat_number') == seat_num:
            return aisle

    return None


@register.filter
def has_vertical_aisle_after(aisles, row_name):
    """
    Check if there's a vertical aisle after a specific row.
    Usage: {% if aisles|has_vertical_aisle_after:"H" %}

    Args:
        aisles: dict with 'horizontal' and 'vertical' keys
        row_name: string row name

    Returns:
        dict with aisle info or None
    """
    if not aisles or 'vertical' not in aisles:
        return None

    vertical_aisles = aisles.get('vertical', [])

    for aisle in vertical_aisles:
        if aisle.get('position') == 'after_row' and aisle.get('row_name') == row_name:
            return aisle

    return None


@register.filter
def get_aisle_width(aisle, default=2):
    """
    Get width of a horizontal aisle in seat-units.
    Usage: {{ aisle|get_aisle_width }}
    """
    if not aisle:
        return default
    return aisle.get('width', default)


@register.filter
def get_aisle_height(aisle, default=1):
    """
    Get height of a vertical aisle in row-units.
    Usage: {{ aisle|get_aisle_height }}
    """
    if not aisle:
        return default
    return aisle.get('height', default)


@register.filter
def get_aisle_description(aisle):
    """
    Get description of an aisle.
    Usage: {{ aisle|get_aisle_description }}
    """
    if not aisle:
        return ""
    return aisle.get('description', '')
