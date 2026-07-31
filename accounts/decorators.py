from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def socio_required(view_func):
    """Richiede login e is_socio=True (o is_staff/is_admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_admin or request.user.is_staff or request.user.is_socio:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Questa sezione è riservata ai soci del Laboratorio Teatrale di Cambiano.')
        return redirect('store')
    return wrapper
