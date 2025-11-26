# 🐛 Debug Scanner QR Mobile - Guida Sviluppo

## Problema: Accesso Fotocamera Richiede HTTPS

### ⚠️ Limitazione Browser
I browser moderni (Chrome, Safari, Firefox) **richiedono HTTPS** per accedere alla fotocamera, tranne per `localhost`.

**Errori Comuni:**
```
DOMException: Permission denied
getUserMedia is not supported
Camera access denied
```

## ✅ Soluzioni per Debug Locale

### Opzione 1: Usa ngrok (Consigliato - Più Semplice) ⭐

**ngrok** crea un tunnel HTTPS verso il tuo server locale.

#### 1. Installa ngrok
```bash
# Scarica da https://ngrok.com/download
# Oppure con Chocolatey
choco install ngrok

# Oppure con Scoop
scoop install ngrok
```

#### 2. Avvia il Server Django
```bash
cd c:\Users\Asus\projects\python\ltcboxoffice
python manage.py runserver 0.0.0.0:8000
```

#### 3. Avvia ngrok
```bash
ngrok http 8000
```

**Output ngrok:**
```
Session Status                online
Account                       your@email.com
Version                       3.0.0
Region                        United States (us)
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

#### 4. Configura Django

Aggiungi l'URL ngrok in `settings.py`:

```python
# settings/base.py o settings.py
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'abc123.ngrok.io',  # Sostituisci con il tuo URL ngrok
    '*.ngrok.io',  # Oppure usa wildcard
]

# Per CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://abc123.ngrok.io',
    'https://*.ngrok.io',
]
```

#### 5. Testa sul Cellulare

1. Apri browser su smartphone
2. Vai a `https://abc123.ngrok.io/boxoffice/qr_scanner/1/`
3. Concedi permessi fotocamera
4. Scansiona QR code!

**✅ Vantaggi ngrok:**
- Setup velocissimo (2 minuti)
- HTTPS automatico
- Funziona su qualsiasi rete
- URL condivisibile con altri dispositivi
- Ispeziona richieste HTTP (dashboard su `http://127.0.0.1:4040`)

**⚠️ Limiti versione gratuita:**
- URL cambia ad ogni avvio (soluzione: piano a pagamento ~$8/mese)
- Timeout sessione dopo 2 ore
- Limite banda

---

### Opzione 2: Certificato SSL Self-Signed

Crea un certificato SSL per `localhost` riconosciuto dal browser.

#### 1. Installa mkcert

```bash
# Con Chocolatey
choco install mkcert

# Oppure scarica da: https://github.com/FiloSottile/mkcert/releases
```

#### 2. Installa Root CA

```bash
mkcert -install
```

Questo installa un'autorità di certificazione locale trusted dal sistema.

#### 3. Genera Certificato per localhost

```bash
cd c:\Users\Asus\projects\python\ltcboxoffice

# Crea certificati
mkcert localhost 127.0.0.1 ::1

# Output:
# Created a new certificate valid for the following names:
#  - "localhost"
#  - "127.0.0.1"
# The certificate is at "./localhost+2.pem"
# The key file is at "./localhost+2-key.pem"
```

#### 4. Avvia Django con HTTPS

```bash
# Installa django-extensions se non hai già
pip install django-extensions Werkzeug pyOpenSSL

# Aggiungi a INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'django_extensions',
]

# Avvia con HTTPS
python manage.py runserver_plus --cert-file localhost+2.pem --key-file localhost+2-key.pem 0.0.0.0:8000
```

#### 5. Configura per Rete Locale

Per testare da smartphone sulla stessa WiFi:

```bash
# Trova il tuo IP locale
ipconfig  # Windows
# Cerca "IPv4 Address" -> es. 192.168.1.100

# Genera certificato con IP locale
mkcert localhost 127.0.0.1 192.168.1.100

# Avvia server
python manage.py runserver_plus --cert-file localhost+3.pem --key-file localhost+3-key.pem 0.0.0.0:8000
```

#### 6. Accedi da Smartphone

```
https://192.168.1.100:8000/boxoffice/qr_scanner/1/
```

**⚠️ Problema:** Lo smartphone non trusted il certificato!

**Soluzione:**
1. Copia il file Root CA sul telefono:
   - Percorso CA: `%LOCALAPPDATA%\mkcert\rootCA.pem`
   - Invia via email/AirDrop al telefono
2. Installa il certificato:
   - **iOS**: Impostazioni → Profilo scaricato → Installa → Generali → Info → Affidabilità certificato
   - **Android**: Impostazioni → Sicurezza → Installa da archivio

**✅ Vantaggi:**
- Controllo completo
- Nessun servizio esterno
- Più veloce (rete locale)

**❌ Svantaggi:**
- Setup più complesso
- Installazione certificato su ogni dispositivo
- Solo sulla stessa rete WiFi

---

### Opzione 3: Django HTTPS con gunicorn (Produzione-like)

Per testare setup più vicino a produzione:

#### 1. Installa gunicorn

```bash
pip install gunicorn
```

#### 2. Avvia con SSL

```bash
gunicorn ltcboxoffice.wsgi:application \
    --bind 0.0.0.0:8443 \
    --certfile=localhost+2.pem \
    --keyfile=localhost+2-key.pem \
    --reload
```

#### 3. Accedi

```
https://localhost:8443/boxoffice/qr_scanner/1/
```

---

### Opzione 4: USB Debugging (Solo Android)

Debug remoto tramite Chrome DevTools.

#### 1. Abilita Debug USB

- Android: Impostazioni → Info telefono → Tocca "Numero build" 7 volte
- Attiva "Opzioni sviluppatore" → Debug USB

#### 2. Collega via USB al PC

```bash
# Installa Android SDK Platform Tools
choco install adb

# Verifica connessione
adb devices
```

#### 3. Port Forwarding

```bash
# Forward porta 8000 da PC a telefono
adb reverse tcp:8000 tcp:8000
```

#### 4. Accedi da Android

```
http://localhost:8000/boxoffice/qr_scanner/1/
```

**✅ Vantaggi:**
- Non serve HTTPS per localhost
- Console log visibile su Chrome DevTools

**❌ Svantaggi:**
- Solo Android
- Cablato via USB
- Può essere instabile

---

## 🔍 Debug Console e Network

### Chrome DevTools Remoto (Android)

#### 1. Setup
1. Chrome desktop → `chrome://inspect`
2. Collega Android via USB
3. Apri browser su Android
4. Vedrai il dispositivo in Chrome inspect

#### 2. Debug JavaScript
- Vedi console.log in tempo reale
- Breakpoint nel codice
- Ispeziona network requests

### Safari Web Inspector (iOS)

#### 1. Setup iPhone
- Impostazioni → Safari → Avanzate → Web Inspector: ON

#### 2. Setup Mac
- Safari → Preferenze → Avanzate → Mostra menu Sviluppo
- Collega iPhone via USB
- Safari (Mac) → Sviluppo → [iPhone Name] → [Tab]

#### 3. Debug
- Console JavaScript
- Network inspector
- Element inspector

---

## 🧪 Test QR Code Senza Fotocamera

### 1. Usa Input Manuale

Clicca "⌨️ Inserimento Manuale" e testa con codici:

```
# Formato valido
00001_000001_000001

# Formato invalido
12345

# Codice inesistente
99999_999999_999999
```

### 2. Genera QR Code di Test

```python
# Script Python per generare QR code di test
import qrcode

# Crea QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data("00001_000001_000001")
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("test_qr.png")
print("QR code salvato in test_qr.png")
```

Apri `test_qr.png` su un secondo device e testa la scansione.

### 3. Mock Camera per Unit Test

```javascript
// Nel template, aggiungi modalità debug
const DEBUG_MODE = true;  // Imposta true per debug

if (DEBUG_MODE) {
    // Simula scansione ogni 3 secondi
    setInterval(() => {
        const testCode = "00001_000001_000001";
        onScanSuccess(testCode);
    }, 3000);
}
```

---

## 📊 Logging e Monitoring

### 1. Aggiungi Logging nel Template

Modifica `qr_scanner_mobile.html`:

```javascript
function validateQRCode(code) {
    console.log('🔍 Validating QR code:', code);
    console.log('🌐 Event ID:', eventId);
    console.log('🔐 CSRF Token:', csrfToken.substring(0, 10) + '...');

    showMessage('🔍 Verifica in corso...', 'warning');

    const requestUrl = `/boxoffice/api/validate-qr/${eventId}/`;
    console.log('📡 Request URL:', requestUrl);

    fetch(requestUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ qr_code: code })
    })
    .then(response => {
        console.log('📥 Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('✅ Response data:', data);
        // ... resto del codice
    })
    .catch(error => {
        console.error('❌ Fetch error:', error);
        showMessage('❌ Errore di rete', 'error');
    });
}
```

### 2. Logging Server-Side

Aggiungi in `boxoffice/views.py`:

```python
import logging
logger = logging.getLogger(__name__)

@login_required(login_url='login')
def validate_qr_code_api(request, event_id:int=None):
    logger.info(f"📱 QR Validation request from user: {request.user.username}")
    logger.info(f"🎫 Event ID: {event_id}")

    if request.method != 'POST':
        logger.warning(f"⚠️ Invalid method: {request.method}")
        return JsonResponse({'valid': False, 'message': 'Metodo non permesso'}, status=405)

    try:
        data = json.loads(request.body)
        qr_code = data.get('qr_code', '').strip()
        logger.info(f"🔍 Validating QR: {qr_code}")

        # ... resto della validazione

        if orderevent.expired:
            logger.warning(f"⚠️ QR code already used: {qr_code}")
            return JsonResponse({
                'valid': False,
                'message': 'Prenotazione già utilizzata/evasa'
            })

        logger.info(f"✅ Valid QR code: {qr_code} - User: {orderevent.user.email}")
        # ... resto del codice

    except Exception as e:
        logger.error(f"❌ Error validating QR: {str(e)}", exc_info=True)
        return JsonResponse({
            'valid': False,
            'message': f'Errore server: {str(e)}'
        }, status=500)
```

### 3. Configura Logging in settings.py

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'qr_scanner_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'boxoffice': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 🎯 Workflow Debug Raccomandato

### Step-by-Step

1. **Setup Veloce con ngrok** (5 minuti)
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ngrok http 8000
   # Aggiungi URL ngrok a ALLOWED_HOSTS
   ```

2. **Crea Prenotazione di Test**
   - Vai al frontend: crea una prenotazione
   - Salva il numero ordine: `00042_000123_000456`
   - Trova il QR code in `static/images/qrcode_img_00042_000123_000456.png`

3. **Test Desktop Prima**
   - Apri lo scanner su PC: `https://abc123.ngrok.io/boxoffice/qr_scanner/1/`
   - Testa input manuale con il codice
   - Verifica che la validazione funzioni

4. **Test Mobile**
   - Apri stesso URL su smartphone
   - Concedi permessi fotocamera
   - Apri `qrcode_img_*.png` su secondo device
   - Scansiona

5. **Monitor in Tempo Reale**
   - Terminal: vedi log Django
   - ngrok dashboard: `http://127.0.0.1:4040` - vedi requests HTTP
   - Chrome DevTools: vedi console JavaScript

---

## 🔥 Troubleshooting Comune

### Problema: "Camera access denied"

**Cause:**
- Browser non ha permesso
- HTTPS non configurato
- Browser non supportato

**Debug:**
```javascript
// Aggiungi nel template
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        console.log('✅ Camera access OK');
        stream.getTracks().forEach(track => track.stop());
    })
    .catch(err => {
        console.error('❌ Camera error:', err.name, err.message);
    });
```

### Problema: "CSRF verification failed"

**Soluzione:**
```python
# settings.py
CSRF_TRUSTED_ORIGINS = [
    'https://abc123.ngrok.io',
    'https://*.ngrok.io',
]
```

### Problema: "Mixed Content" (HTTP/HTTPS)

**Causa:** Stai caricando risorse HTTP in pagina HTTPS

**Debug:**
```javascript
// Console browser
// Cerca: "Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure..."
```

**Soluzione:** Usa URL relativi o HTTPS per tutte le risorse:
```html
<!-- ❌ Male -->
<script src="http://example.com/lib.js"></script>

<!-- ✅ Bene -->
<script src="https://example.com/lib.js"></script>
<script src="/static/js/lib.js"></script>
```

---

## 📱 Test su Dispositivi Fisici

### Dispositivi Consigliati

**Per Testing:**
- iPhone 8 o superiore (iOS 12+)
- Samsung Galaxy S8 o superiore (Android 8+)
- Google Pixel 3 o superiore

**Browser da Testare:**
- Safari (iOS)
- Chrome (Android/iOS)
- Firefox (Android)
- Samsung Internet (Android)

---

## ✅ Checklist Pre-Test

Prima di ogni sessione debug:

- [ ] Server Django attivo su porta 8000
- [ ] ngrok attivo e URL copiato
- [ ] `ALLOWED_HOSTS` aggiornato con URL ngrok
- [ ] `CSRF_TRUSTED_ORIGINS` configurato
- [ ] Almeno 1 prenotazione di test nel DB
- [ ] QR code di test generato e visibile
- [ ] Smartphone su stessa rete (o ngrok)
- [ ] Console DevTools aperta (desktop)
- [ ] Log Django visibile in terminal

---

## 🚀 Quick Start Command

```bash
# One-liner per debug rapido
python manage.py runserver 0.0.0.0:8000 & ngrok http 8000

# Poi aggiungi l'URL ngrok in settings.py
# E vai a: https://ABC123.ngrok.io/boxoffice/qr_scanner/1/
```

---

**Buon debug! 🐛🔍**

Per ulteriore assistenza, controlla i log in `qr_scanner_debug.log` o contatta il team di sviluppo.
