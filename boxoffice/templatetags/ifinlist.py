from django import template
register = template.Library()

@register.filter(name='ifinlist')
def ifinlist(value, list):
    return value in list
