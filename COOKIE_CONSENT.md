# Cookie Consent System - LTC Box Office

## Panoramica

Il sistema di gestione cookie conforme al GDPR implementato per LTC Box Office richiede il consenso esplicito degli utenti per l'utilizzo dei cookies, con particolare attenzione agli utenti autenticati.

## Caratteristiche Principali

### 1. **Consenso Obbligatorio al Login**
- Quando un utente si autentica, viene automaticamente reindirizzato alla pagina di consenso cookies
- Il consenso viene cancellato ad ogni nuovo login per garantire conformità
- L'utente deve accettare i cookies per procedere all'utilizzo del sistema

### 2. **Banner Cookie per Utenti Non Autenticati**
- Banner informativo nella parte inferiore della pagina
- Tre opzioni disponibili:
  - **Accetta Tutti**: accetta cookies essenziali e funzionali
  - **Preferenze**: apre modal per selezione granulare
  - **Solo Essenziali**: accetta solo cookies tecnici necessari

### 3. **Middleware di Controllo**
- `CookieConsentMiddleware` controlla ogni richiesta
- Verifica se l'utente autenticato ha dato il consenso
- Reindirizza alla pagina di consenso se necessario
- URL esclusi dal controllo: login, logout, register, static files, admin

### 4. **Gestione Granulare**
- **Cookies Essenziali** (obbligatori):
  - `sessionid`: gestione sessione utente (60 minuti)
  - `csrftoken`: protezione CSRF (1 anno)
  - `cart_id`: carrello prenotazioni (sessione)
  - `messages`: messaggi sistema (sessione)

- **Cookies Funzionali** (opzionali):
  - `cookie_consent`: preferenze consenso (1 anno)
  - `user_preferences`: preferenze interfaccia (6 mesi)

## File Implementati

### Backend
```
accounts/
├── cookie_middleware.py          # Middleware controllo consenso
└── views.py                      # View cookie_consent() e cookie_policy()
```

### Templates
```
templates/accounts/
├── cookie_consent.html           # Pagina consenso per utenti autenticati
└── cookie_policy.html            # Informativa completa cookie policy
```

### Frontend
```
static/
├── css/cookie-consent.css        # Stili banner e modal
└── js/cookie-consent.js          # Logica banner per non autenticati
```

### Configurazione
```
ltcboxoffice/settings/base.py
├── MIDDLEWARE: aggiunto CookieConsentMiddleware
└── SESSION_COOKIE_AGE: 3600 (60 minuti)

accounts/urls.py
├── /accounts/cookie-consent/     # Pagina consenso
└── /accounts/cookie-policy/      # Cookie policy completa
```

## Flusso Utente

### Utente Autenticato
1. Login → `auth.login()` in `views.py`
2. Sessione `cookie_consent_given` viene cancellata
3. Middleware intercetta richiesta successiva
4. Redirect a `/accounts/cookie-consent/`
5. Utente legge informativa e accetta
6. Consenso salvato in sessione:
   - `cookie_consent_given`: True
   - `cookie_consent_date`: timestamp ISO
   - `cookie_functional`: True/False
7. Redirect alla destinazione originale

### Utente Non Autenticato
1. Visita il sito
2. Banner cookie appare in basso
3. JavaScript verifica cookie `cookie_consent_accepted`
4. Se non presente, mostra banner
5. Utente sceglie opzione:
   - Accetta → cookie salvato, banner nascosto
   - Preferenze → modal per scelta granulare
   - Solo Essenziali → cookie minimal, banner nascosto

## Implementazione Tecnica

### Middleware
```python
class CookieConsentMiddleware:
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
    
    def __call__(self, request):
        if request.user.is_authenticated and not is_exempt:
            if not request.session.get('cookie_consent_given'):
                request.session['cookie_consent_next'] = path
                return redirect('cookie_consent')
```

### View Consenso
```python
def cookie_consent(request):
    if request.method == 'POST':
        if request.POST.get('confirm_consent'):
            request.session['cookie_consent_given'] = True
            request.session['cookie_consent_date'] = timezone.now().isoformat()
            request.session['cookie_functional'] = bool(request.POST.get('accept_functional'))
            next_url = request.session.pop('cookie_consent_next', 'dashboard')
            return redirect(next_url)
```

### Modifica Login
```python
def login(request):
    # ... autenticazione ...
    auth.login(request, user)
    # Cancella consenso precedente per forzare nuovo consenso
    if 'cookie_consent_given' in request.session:
        del request.session['cookie_consent_given']
```

## Conformità GDPR

✅ **Consenso Esplicito**: checkbox obbligatoria conferma lettura informativa  
✅ **Informativa Chiara**: descrizione dettagliata ogni categoria cookie  
✅ **Granularità**: scelta separata cookies essenziali vs funzionali  
✅ **Revoca**: utente può uscire e non dare consenso  
✅ **Tracciabilità**: timestamp consenso salvato in sessione  
✅ **Durata**: cookies con scadenza definita  
✅ **Sicurezza**: HttpOnly, Secure (prod), SameSite=Lax  

## Testing

### Test Manuale

1. **Test Login con Consenso**:
   ```bash
   # Accedi al sito
   # Login con credenziali
   # Verifica redirect a /accounts/cookie-consent/
   # Accetta consenso
   # Verifica redirect a dashboard
   ```

2. **Test Banner Non Autenticati**:
   ```bash
   # Cancella cookies browser
   # Visita homepage
   # Verifica apparizione banner
   # Clicca "Preferenze"
   # Verifica modal settings
   # Salva preferenze
   # Verifica banner nascosto
   ```

3. **Test Middleware**:
   ```bash
   # Login utente
   # Accetta cookies
   # Naviga diverse pagine
   # Verifica no redirect ripetuti
   ```

### Django Check
```bash
python manage.py check
# System check identified no issues (0 silenced).
```

## Sicurezza

- **CSRF Protection**: token validato su POST consenso
- **Session Security**: 
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SECURE = True` (produzione)
  - `SESSION_COOKIE_AGE = 3600` (60 minuti)
- **XSS Prevention**: escape HTML nei template
- **SameSite**: cookie con attributo `SameSite=Lax`

## Manutenzione

### Aggiungere Nuova Categoria Cookie
1. Aggiorna `cookie_consent.html` con nuovo checkbox
2. Modifica `cookie_consent()` view per salvare preferenza
3. Aggiorna `cookie_policy.html` con descrizione
4. Aggiorna tabella cookies in documentazione

### Modificare Durata Cookies
```python
# ltcboxoffice/settings/base.py
SESSION_COOKIE_AGE = 3600  # secondi (60 minuti)
CSRF_COOKIE_AGE = 31449600  # 1 anno
```

### Escludere URL da Middleware
```python
# accounts/cookie_middleware.py
EXEMPT_URLS = [
    # ... esistenti ...
    '/nuovo/percorso/',
]
```

## Compatibilità

- ✅ Django 4.2.11
- ✅ Python 3.13
- ✅ Bootstrap 4
- ✅ Font Awesome 4.7
- ✅ jQuery 3.6.4
- ✅ Browser moderni (Chrome, Firefox, Safari, Edge)
- ✅ Responsive design (mobile, tablet, desktop)

## Risorse

- [GDPR Cookie Compliance](https://gdpr.eu/cookies/)
- [Django Session Framework](https://docs.djangoproject.com/en/4.2/topics/http/sessions/)
- [Django Middleware](https://docs.djangoproject.com/en/4.2/topics/http/middleware/)

## Changelog

### v1.0.0 (2025-11-14)
- ✅ Implementato middleware controllo consenso
- ✅ Creata pagina consenso per utenti autenticati
- ✅ Implementato banner cookie per visitatori
- ✅ Modal settings con scelta granulare
- ✅ Cookie policy completa
- ✅ Integrazione con sistema login
- ✅ Test e validazione Django

---

**Autore**: GitHub Copilot  
**Progetto**: LTC Box Office - Teatro Cambiano  
**Licenza**: Proprietaria
