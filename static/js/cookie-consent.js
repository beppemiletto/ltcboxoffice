// Cookie Consent Banner JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Check if user has already given consent
    const cookieConsent = getCookie('cookie_consent_accepted');
    
    if (!cookieConsent) {
        showCookieBanner();
    }
    
    // Accept all cookies
    document.getElementById('acceptCookies')?.addEventListener('click', function() {
        setCookie('cookie_consent_accepted', 'all', 365);
        setCookie('cookie_consent_date', new Date().toISOString(), 365);
        hideCookieBanner();
    });
    
    // Decline cookies
    document.getElementById('declineCookies')?.addEventListener('click', function() {
        setCookie('cookie_consent_accepted', 'essential', 365);
        setCookie('cookie_consent_date', new Date().toISOString(), 365);
        hideCookieBanner();
    });
    
    // Show settings modal
    document.getElementById('cookieSettings')?.addEventListener('click', function() {
        document.getElementById('cookieSettingsModal').style.display = 'block';
    });
    
    // Close settings modal
    document.querySelector('.cookie-settings-close')?.addEventListener('click', function() {
        document.getElementById('cookieSettingsModal').style.display = 'none';
    });
    
    // Save cookie preferences
    document.getElementById('saveCookieSettings')?.addEventListener('click', function() {
        const essential = document.getElementById('essentialCookies').checked;
        const functional = document.getElementById('functionalCookies').checked;
        
        let consent = 'essential';
        if (functional) consent = 'functional';
        
        setCookie('cookie_consent_accepted', consent, 365);
        setCookie('cookie_consent_date', new Date().toISOString(), 365);
        setCookie('cookie_functional', functional, 365);
        
        document.getElementById('cookieSettingsModal').style.display = 'none';
        hideCookieBanner();
    });
});

function showCookieBanner() {
    const banner = document.getElementById('cookieConsentBanner');
    if (banner) {
        banner.style.display = 'block';
    }
}

function hideCookieBanner() {
    const banner = document.getElementById('cookieConsentBanner');
    if (banner) {
        banner.style.display = 'none';
    }
}

function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    const secure = window.location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = name + '=' + value + '; expires=' + expires.toUTCString() + '; path=/' + secure + '; SameSite=Lax';
}

function getCookie(name) {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('cookieSettingsModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}
