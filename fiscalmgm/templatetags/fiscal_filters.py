"""
Custom template filters for fiscalmgm app
"""
from django import template

register = template.Library()


@register.filter(name='fix_extension')
def fix_extension(value):
    """
    Sostituisce .xls con .xlsx per compatibilità con i nuovi file Excel
    """
    if value:
        return value.replace('.xls', '.xlsx')
    return value
