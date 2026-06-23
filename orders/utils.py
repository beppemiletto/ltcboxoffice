from .models import OrderEventLog


def log_orderevent(orderevent, operation, operator=None, notes='', request=None):
    """
    Registra un'operazione nella black box delle prenotazioni.

    operation: OrderEventLog.OP_CREATA | OP_EVASA | OP_CANCELLATA | OP_MODIFICATA | OP_ALTRO
    operator:  istanza Account (chi ha eseguito) — None per azioni automatiche di sistema
    notes:     testo libero opzionale
    request:   HttpRequest — se passato estrae l'IP automaticamente
    """
    ip = ''
    if request is not None:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
             or request.META.get('REMOTE_ADDR', '')

    OrderEventLog.objects.create(
        orderevent=orderevent,
        operation=operation,
        operator=operator,
        notes=notes,
        ip_address=ip,
    )
