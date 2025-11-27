"""
Middleware per permettere domini ngrok dinamici in development.
"""


class NgrokMiddleware:
    """
    Middleware che permette qualsiasi host ngrok in development.
    Aggiunge automaticamente domini ngrok a ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS.

    USARE SOLO IN DEVELOPMENT, MAI IN PRODUZIONE!
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings

        # Ottieni host direttamente dall'header HTTP_HOST (bypassa il check ALLOWED_HOSTS)
        host = request.META.get('HTTP_HOST', '').split(':')[0]

        # Controlla se è un dominio ngrok
        if host and (host.endswith('.ngrok-free.app') or host.endswith('.ngrok.io')):

            # Aggiungi ENTRAMBI http e https per sicurezza
            # ngrok usa HTTPS ma Django potrebbe non rilevarlo correttamente
            origins_to_add = [
                f"https://{host}",  # ngrok usa sempre HTTPS
                f"http://{host}",   # Fallback per sicurezza
            ]

            for origin in origins_to_add:
                if origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(origin)
                    print(f"[NgrokMiddleware] Aggiunto {origin} a CSRF_TRUSTED_ORIGINS")

        response = self.get_response(request)
        return response
