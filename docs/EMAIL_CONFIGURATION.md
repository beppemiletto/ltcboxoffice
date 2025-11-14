# Configurazione Email - ltcboxoffice

## Problema: Email non arrivano dopo la prenotazione

### Modalità Development (Attuale)
In `ltcboxoffice/settings/development.py` (riga 31):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Comportamento**: Le email vengono **stampate nella console** di Django invece di essere inviate realmente.

**Dove vedere le email**: Nel terminale dove gira `python manage.py runserver`, vedrai il contenuto completo dell'email stampato.

---

## Soluzioni

### Opzione 1: Inviare email reali in Development

Modifica `ltcboxoffice/settings/development.py`:

```python
# Cambia da console.EmailBackend a smtp.EmailBackend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.teatrocambiano.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreply@teatrocambiano.com'  # Usa credenziali reali
EMAIL_HOST_PASSWORD = 'la-tua-password-smtp'     # Password SMTP
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@teatrocambiano.com'
```

⚠️ **ATTENZIONE**: Non committare la password in Git! Usa variabili d'ambiente:
```python
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
```

### Opzione 2: Testare con file invece di console

Modifica `ltcboxoffice/settings/development.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR.parent, 'sent_emails')  # Salva email come file
```

Le email verranno salvate come file `.txt` nella cartella `sent_emails/` e potrai aprirle per leggerle.

### Opzione 3: Usare Mailtrap per testing (Consigliato)

Mailtrap cattura le email senza inviarle davvero:

1. Registrati su https://mailtrap.io (gratis)
2. Ottieni le credenziali SMTP
3. Modifica `development.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 2525
EMAIL_HOST_USER = 'il-tuo-username-mailtrap'
EMAIL_HOST_PASSWORD = 'la-tua-password-mailtrap'
EMAIL_USE_TLS = True
```

---

## Modalità Production

In `ltcboxoffice/settings/production.py` (linee 39-45):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
```

**Comportamento**: Invia email reali tramite SMTP usando variabili d'ambiente.

**Configurazione server di produzione**:
```bash
# File .env o variabili d'ambiente
EMAIL_HOST=smtp.teatrocambiano.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@teatrocambiano.com
EMAIL_HOST_PASSWORD=password-sicura
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@teatrocambiano.com
```

---

## Come verificare che le email funzionano

### Development con console backend
1. Avvia Django: `python manage.py runserver`
2. Completa una prenotazione
3. Controlla il terminale - dovresti vedere:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Conferma prenotazione
From: noreply@teatrocambiano.com
To: cliente@example.com
Date: ...

[Contenuto dell'email qui]
```

### Development con SMTP reale
1. Configura EMAIL_BACKEND = smtp.EmailBackend
2. Completa una prenotazione
3. Controlla la casella email del cliente

### Production
1. Configura variabili d'ambiente
2. Avvia con `DJANGO_ENV=production python manage.py runserver`
3. Le email vengono inviate automaticamente

---

## Risoluzione problemi

### "SMTPAuthenticationError"
- Credenziali SMTP errate
- Verifica EMAIL_HOST_USER e EMAIL_HOST_PASSWORD

### "SMTPServerDisconnected"
- EMAIL_PORT sbagliato (prova 587 o 465)
- EMAIL_USE_TLS deve essere True per porta 587

### "Connection refused"
- EMAIL_HOST sbagliato
- Server SMTP non raggiungibile

### Email non arriva ma nessun errore
- Controlla spam/posta indesiderata
- Verifica DEFAULT_FROM_EMAIL sia valido
- Controlla i log del server SMTP

---

## File modificati per risolvere il bug del barcode

### `templates/booking/booking_complete.html` (linea 81)
```html
<!-- PRIMA (barcode non appariva) -->
<img src="{% static 'images/'%}{{orderevent.barcode}}" alt="Tickets booking barcode">

<!-- DOPO (barcode funziona) -->
<img src="/{{orderevent.barcode_path}}" alt="Tickets booking barcode">
```

Il problema era che usava solo il nome del file invece del percorso completo `static/images/filename.png`.

---

## Riepilogo

| Ambiente | EMAIL_BACKEND | Dove finiscono le email |
|----------|---------------|-------------------------|
| Development | `console.EmailBackend` | Stampate in console Django |
| Development (SMTP) | `smtp.EmailBackend` | Inviate realmente |
| Development (file) | `filebased.EmailBackend` | Salvate come file .txt |
| Production | `smtp.EmailBackend` | Inviate realmente via SMTP |

**Raccomandazione**: Per testing locale usa Mailtrap, per produzione usa SMTP reale con variabili d'ambiente.
