"""
Utility functions for subscription management
"""
from .models import Subscription, SubscriptionType


# Mapping subscription type code_prefix to price code
SUBSCRIPTION_PRICE_CODES = {
    'R4': 3,  # Abbonamento 4 ridotti
    'R8': 4,  # Abbonamento 8 ridotti
    'I4': 5,  # Abbonamento 4 interi
    'I8': 6,  # Abbonamento 8 interi
}

# Reverse mapping
PRICE_CODE_TO_SUBSCRIPTION = {v: k for k, v in SUBSCRIPTION_PRICE_CODES.items()}


def get_user_active_subscriptions(user):
    """
    Restituisce gli abbonamenti attivi e validi dell'utente
    
    Returns:
        QuerySet di Subscription filtrati per:
        - user
        - status = ACTIVE
        - valid_to >= today
        - events_used < events_included
    """
    if not user or not user.is_authenticated:
        return Subscription.objects.none()
    
    return Subscription.objects.filter(
        user=user,
        status='ACTIVE'
    ).select_related('subscription_type').order_by('-created_at')


def get_subscription_price_options(user):
    """
    Restituisce le opzioni di prezzo abbonamento disponibili per l'utente
    
    Returns:
        List di dict con struttura:
        [
            {
                'code': 3,  # Codice prezzo
                'name': 'Abbonamento R4',
                'subscription': <Subscription object>,
                'remaining': 2,  # Eventi rimanenti
            },
            ...
        ]
    """
    active_subs = get_user_active_subscriptions(user)
    options = []
    
    for sub in active_subs:
        if sub.is_valid():
            price_code = SUBSCRIPTION_PRICE_CODES.get(sub.subscription_type.code_prefix)
            if price_code:
                options.append({
                    'code': price_code,
                    'name': f'Abbonamento {sub.subscription_type.code_prefix}',
                    'subscription': sub,
                    'subscription_number': sub.subscription_number,
                    'remaining': sub.remaining_events(),
                    'type_name': sub.subscription_type.name,
                })
    
    return options


def is_subscription_price_code(price_code):
    """
    Verifica se il codice prezzo è un abbonamento
    
    Args:
        price_code: int o str del codice prezzo
    
    Returns:
        bool: True se è un codice abbonamento (3-6)
    """
    try:
        code = int(price_code)
        return code in PRICE_CODE_TO_SUBSCRIPTION
    except (ValueError, TypeError):
        return False


def get_subscription_by_price_code(user, price_code):
    """
    Restituisce l'abbonamento corrispondente al codice prezzo
    
    Args:
        user: Account object
        price_code: int (3, 4, 5, 6)
    
    Returns:
        Subscription object o None
    """
    if not is_subscription_price_code(price_code):
        return None
    
    code_prefix = PRICE_CODE_TO_SUBSCRIPTION.get(int(price_code))
    if not code_prefix:
        return None
    
    # Trova abbonamento attivo di quel tipo
    try:
        return Subscription.objects.filter(
            user=user,
            subscription_type__code_prefix=code_prefix,
            status='ACTIVE'
        ).select_related('subscription_type').first()
    except Subscription.DoesNotExist:
        return None


def can_use_subscription(user, price_code):
    """
    Verifica se l'utente può usare l'abbonamento per questo codice prezzo
    
    Returns:
        tuple (bool, str): (può_usare, messaggio_errore)
    """
    if not is_subscription_price_code(price_code):
        return False, "Codice prezzo non è un abbonamento"
    
    subscription = get_subscription_by_price_code(user, price_code)
    
    if not subscription:
        return False, "Abbonamento non trovato"
    
    if not subscription.is_valid():
        if subscription.status == 'EXPIRED':
            return False, "Abbonamento scaduto"
        elif subscription.status == 'EXHAUSTED':
            return False, "Abbonamento esaurito (nessun evento rimanente)"
        else:
            return False, f"Abbonamento non valido (stato: {subscription.get_status_display()})"
    
    return True, ""
