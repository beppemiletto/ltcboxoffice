"""
Cookie Consent Middleware
Ensures users provide cookie consent on login and throughout the session
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class CookieConsentMiddleware:
    """
    Middleware to enforce cookie consent for authenticated users
    """
    
    # URLs that don't require cookie consent
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/register/',
        '/accounts/cookie-consent/',
        '/accounts/cookie-policy/',
        '/static/',
        '/media/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if URL is exempt
        path = request.path
        is_exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)
        
        # If user is authenticated and hasn't given cookie consent
        if request.user.is_authenticated and not is_exempt:
            cookie_consent = request.session.get('cookie_consent_given')
            
            # If no consent, redirect to consent page
            if not cookie_consent:
                # Store the intended destination
                request.session['cookie_consent_next'] = path
                messages.warning(
                    request, 
                    'Per utilizzare il sito è necessario accettare la nostra policy sui cookies.'
                )
                return redirect('cookie_consent')
        
        response = self.get_response(request)
        return response
