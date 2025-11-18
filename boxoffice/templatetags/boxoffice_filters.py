from django import template
from carts.models import ingressi_strings
from subscriptions.utils import is_subscription_price_code

register = template.Library()

@register.filter
def ingresso_display(price_code):
    """
    Restituisce la descrizione del tipo di ingresso dal codice
    """
    try:
        code = int(price_code)
        if 0 <= code < len(ingressi_strings):
            return ingressi_strings[code]
        return f"Codice {code}"
    except (ValueError, TypeError):
        return str(price_code)

@register.filter
def is_subscription(price_code):
    """
    Verifica se il codice è un abbonamento (3-6)
    """
    return is_subscription_price_code(price_code)

@register.filter
def price_or_subscription(item):
    """
    Restituisce il prezzo o 'Abbonamento' se è un codice abbonamento
    """
    if is_subscription_price_code(item.price):
        return ingresso_display(item.price)
    return f"€ {item.cost:.2f}"
