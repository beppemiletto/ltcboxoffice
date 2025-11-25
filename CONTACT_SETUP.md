# Configurazione Sistema di Contatto Email

## Panoramica

Il sistema di contatto email permette ai visitatori del sito di inviare messaggi direttamente a `ltcboxoffice@teatrocambiano.com` attraverso un form protetto da Google reCAPTCHA v3.

## Funzionalità Implementate

### 1. Form di Contatto
- **URL**: `/contact/`
- **Template**: `templates/contact/contact.html`
- **Campi**:
  - Nome
  - Email
  - Oggetto
  - Messaggio
- **Protezione anti-spam**: Google reCAPTCHA v3 (invisibile)

### 2. Bottone Email nella Navbar
- Il bottone "Email" nella navbar superiore è stato collegato alla pagina di contatto
- **File modificato**: `templates/includes/navbar.html` (riga 19)

### 3. Bottone Backoffice Admin
- Nuovo bottone "Backoffice Admin" visibile solo per utenti staff/admin
- Appare nella navbar accanto ad "Area Riservata"
- Reindirizza direttamente al pannello di amministrazione Django
- **File modificato**: `templates/includes/navbar.html` (riga 23)

### 4. Salvataggio Messaggi
- Tutti i messaggi vengono salvati nel database
- Modello `ContactMessage` con campi: nome, email, oggetto, messaggio, data, IP
- Visibile nell'admin Django per gli amministratori

## Configurazione

### 1. Ottenere le Chiavi reCAPTCHA

1. Vai su [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Accedi con il tuo account Google
3. Clicca su "+" per creare un nuovo sito
4. Compila il form:
   - **Label**: LTC Box Office Contact Form
   - **reCAPTCHA type**: reCAPTCHA v3
   - **Domains**:
     - `localhost` (per development)
     - `127.0.0.1` (per development)
     - `prenota.teatrocambiano.com` (per production)
     - `teatrocambiano.com` (per production)
   - Accetta i termini e clicca "Submit"
5. Copia la **SITE KEY** e la **SECRET KEY**

### 2. Configurare le Variabili d'Ambiente

Aggiungi le chiavi reCAPTCHA al file `.env`:

```bash
# Google reCAPTCHA v3 Configuration
RECAPTCHA_SITE_KEY=6Lc...tua-site-key...AAA
RECAPTCHA_SECRET_KEY=6Lc...tua-secret-key...AAA
```

**IMPORTANTE**: NON committare mai il file `.env` su Git! Le chiavi devono rimanere private.

### 3. Eseguire le Migrazioni

Applica le migrazioni per creare la tabella `contact_contactmessage`:

```bash
# Attiva la virtualenv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Esegui le migrazioni
python manage.py migrate contact
```

### 4. Verificare la Configurazione Email

Assicurati che le impostazioni email siano configurate correttamente nel file `.env`:

```bash
# Email Configuration
EMAIL_HOST=smtp.teatrocambiano.com
EMAIL_PORT=587
EMAIL_HOST_USER=ltcboxoffice@teatrocambiano.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=ltcboxoffice@teatrocambiano.com
```

## Testing

### Development

In modalità development, puoi usare il backend console per visualizzare le email nella console:

1. In `ltcboxoffice/settings/development.py`, cambia:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

2. Le email verranno stampate nella console invece di essere inviate

### Testing reCAPTCHA

Google reCAPTCHA v3 funziona in modo invisibile e assegna uno score (0.0 - 1.0) ad ogni richiesta:
- Score > 0.5: richiesta probabilmente legittima
- Score < 0.5: possibile bot

Durante il development con localhost, reCAPTCHA funzionerà normalmente.

## Gestione Messaggi nell'Admin

1. Accedi all'admin Django: `/admin/`
2. Vai alla sezione "Messaggi di Contatto"
3. Vedrai tutti i messaggi ricevuti con:
   - Nome e email del mittente
   - Oggetto e testo del messaggio
   - Data e ora di ricezione
   - Indirizzo IP del mittente

**Nota**: I messaggi sono in sola lettura nell'admin (non possono essere modificati o aggiunti manualmente).

## Struttura File

```
ltcboxoffice/
├── contact/                          # Nuova app per il sistema di contatto
│   ├── __init__.py
│   ├── admin.py                      # Configurazione admin
│   ├── apps.py                       # Configurazione app
│   ├── forms.py                      # Form di contatto
│   ├── models.py                     # Modello ContactMessage
│   ├── urls.py                       # URL routing
│   ├── views.py                      # View per gestire il form
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py           # Migrazione iniziale
│
├── templates/
│   ├── contact/
│   │   └── contact.html              # Template form di contatto
│   └── includes/
│       └── navbar.html               # Navbar modificata (Email + Admin)
│
├── ltcboxoffice/
│   ├── settings/
│   │   └── base.py                   # Settings aggiornati
│   └── urls.py                       # URL principale aggiornato
│
├── .env.example                      # Esempio variabili d'ambiente
└── CONTACT_SETUP.md                  # Questa documentazione
```

## Sicurezza

- **reCAPTCHA v3**: Protezione anti-bot invisibile
- **CSRF Protection**: Token CSRF Django su tutti i form
- **IP Logging**: Gli IP vengono salvati per tracciabilità
- **Email Validation**: Validazione lato client e server
- **XSS Protection**: Template Django con auto-escape

## Troubleshooting

### Il form non funziona
1. Controlla che le chiavi reCAPTCHA siano configurate correttamente
2. Verifica che la console del browser non mostri errori JavaScript
3. Assicurati che il dominio sia registrato in Google reCAPTCHA

### Le email non vengono inviate
1. Verifica le credenziali email nel file `.env`
2. Controlla i log di Django per eventuali errori
3. In development, usa `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

### Errore "No module named 'contact'"
Assicurati di aver aggiunto `'contact'` in `INSTALLED_APPS` nel file `settings/base.py`

### Il bottone Admin non appare
Il bottone "Backoffice Admin" appare solo se:
- L'utente è autenticato (`user.id is not None`)
- L'utente ha il flag `is_staff=True`

## Personalizzazione

### Modificare l'Email di Destinazione

Per cambiare l'indirizzo email dove vengono ricevuti i messaggi, modifica in `contact/views.py`:

```python
send_mail(
    subject,
    message_body,
    settings.DEFAULT_FROM_EMAIL,
    ['tuoindirizzo@example.com'],  # Cambia qui
    fail_silently=False,
)
```

### Modificare lo Threshold di reCAPTCHA

Per rendere il filtro anti-spam più o meno severo, modifica in `contact/views.py`:

```python
if not result.get('success', False) or result.get('score', 0) < 0.5:
    # Cambia 0.5 con un valore diverso (0.0 - 1.0)
    # 0.5 è il valore raccomandato da Google
```

## Supporto

Per problemi o domande, contatta il team di sviluppo.
