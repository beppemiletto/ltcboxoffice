# Configurazione Apache + Gunicorn in produzione

Documentazione della configurazione reale del server `prenota.teatrocambiano.com`.

## Architettura

```
Internet → Apache :80/:443 → Gunicorn :8000 → Django
                ↓
         /media/  servito direttamente da Apache
         /static/ servito da WhiteNoise (dentro Gunicorn)
```

- **Apache** — reverse proxy, terminazione SSL, serving file media
- **Gunicorn** — WSGI server Django, porta 8000, gestito da systemd
- **Redis** — cache Django
- **Let's Encrypt / Certbot** — certificato SSL con rinnovo automatico

---

## File di configurazione Apache

### HTTP — `/etc/apache2/sites-available/prenota.conf`

```apache
<VirtualHost *:80>
    ServerName prenota.teatrocambiano.com
    ServerAdmin info@teatrocambiano.com

    # Serve certbot ACME challenge direttamente
    Alias /.well-known/acme-challenge/ /var/www/html/.well-known/acme-challenge/
    <Directory /var/www/html/.well-known/acme-challenge/>
        Options None
        AllowOverride None
        Require all granted
    </Directory>

    # Proxy tutto il resto a gunicorn
    ProxyPreserveHost On
    ProxyPass /.well-known/acme-challenge/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    RequestHeader set X-Forwarded-Proto "http"

    ErrorLog ${APACHE_LOG_DIR}/prenota_error.log
    CustomLog ${APACHE_LOG_DIR}/prenota_access.log combined

    # Redirect automatico HTTP → HTTPS (aggiunto da certbot)
    RewriteEngine on
    RewriteCond %{SERVER_NAME} =prenota.teatrocambiano.com
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>
```

### HTTPS — `/etc/apache2/sites-available/prenota-le-ssl.conf`

```apache
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName prenota.teatrocambiano.com
    ServerAdmin info@teatrocambiano.com

    # Serve certbot ACME challenge direttamente
    Alias /.well-known/acme-challenge/ /var/www/html/.well-known/acme-challenge/
    <Directory /var/www/html/.well-known/acme-challenge/>
        Options None
        AllowOverride None
        Require all granted
    </Directory>

    # Serve media files direttamente (Django non le serve in produzione)
    Alias /media/ /home/ltc/projects/ltcboxoffice/ltcboxoffice/media/
    <Directory /home/ltc/projects/ltcboxoffice/ltcboxoffice/media/>
        Options None
        AllowOverride None
        Require all granted
    </Directory>

    # Proxy tutto il resto a gunicorn
    ProxyPreserveHost On
    ProxyPass /.well-known/acme-challenge/ !
    ProxyPass /media/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    # Necessario per evitare redirect loop con SECURE_SSL_REDIRECT = True
    RequestHeader set X-Forwarded-Proto "https"

    ErrorLog ${APACHE_LOG_DIR}/prenota_error.log
    CustomLog ${APACHE_LOG_DIR}/prenota_access.log combined

    SSLCertificateFile /etc/letsencrypt/live/prenota.teatrocambiano.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/prenota.teatrocambiano.com/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf
</VirtualHost>
</IfModule>
```

**Punti critici:**
- `ProxyPass /media/ !` — il `!` significa "non fare proxy, lascia che Apache gestisca questo path"
- `RequestHeader set X-Forwarded-Proto "https"` — deve essere `"https"` (non `"http"`) nel VirtualHost SSL, altrimenti Django vede tutte le richieste come HTTP e fa redirect infinito
- L'ordine dei `ProxyPass` è importante: le eccezioni (`!`) devono venire prima del catch-all `/`

---

## Permessi filesystem

Apache gira come utente `www-data`. Per servire i file media deve poter **attraversare** tutte le directory nel path.

### Path completo dei file media

```
/home/ltc/projects/ltcboxoffice/ltcboxoffice/media/
```

### Permessi necessari

Ogni directory nel path deve avere il bit `x` (execute/search) attivo per "others":

| Directory | Permessi minimi | Nota |
|-----------|----------------|------|
| `/home/ltc/` | `drwxr-xr-x` (755) | OK di default |
| `/home/ltc/projects/` | `drwx--x--x` | **Problema comune** — di default è 700 |
| `/home/ltc/projects/ltcboxoffice/` | `drwxrwxr-x` (775) | OK |
| `.../ltcboxoffice/media/` | `drwxrwxr-x` (775) | OK |

### Comando da eseguire (una volta sola)

```bash
chmod o+x /home/ltc/projects
```

Questo aggiunge solo il permesso di attraversamento (`x`) senza rendere leggibile il contenuto della directory (sicuro: `www-data` può entrare ma non listare i file di `projects/`).

### Verifica

```bash
sudo -u www-data ls /home/ltc/projects/ltcboxoffice/ltcboxoffice/media/photos/billboard/
```

Se restituisce i file senza errori, la configurazione è corretta.

### Sintomo se mancante

Errore nei log Apache (`/var/log/apache2/prenota_error.log`):

```
(13)Permission denied: [client x.x.x.x] AH00035: access to /media/foto.jpg denied
(filesystem path '/home/ltc/projects/ltcboxoffice') because search permissions are
missing on a component of the path
```

---

## Servizio Gunicorn (systemd)

File: `/etc/systemd/system/ltcboxoffice.service`

```ini
[Unit]
Description=LTC BoxOffice - Gunicorn (production)
After=network.target mariadb.service redis-server.service
Requires=mariadb.service redis-server.service

[Service]
Type=notify
User=ltc
WorkingDirectory=/home/ltc/projects/ltcboxoffice/ltcboxoffice
EnvironmentFile=/home/ltc/projects/ltcboxoffice/ltcboxoffice/.env.production
Environment="DJANGO_SETTINGS_MODULE=ltcboxoffice.settings.production"
ExecStart=/home/ltc/projects/ltcboxoffice/ltcboxoffice/.env/bin/gunicorn \
    ltcboxoffice.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Comandi utili:

```bash
sudo systemctl status ltcboxoffice      # stato
sudo systemctl restart ltcboxoffice     # riavvio (dopo modifiche al codice)
sudo journalctl -u ltcboxoffice -n 50   # ultimi 50 log
```

---

## SSL / Let's Encrypt

Certificato ottenuto con certbot in modalità standalone (Apache temporaneamente fermato):

```bash
sudo certbot --apache -d prenota.teatrocambiano.com
```

Rinnovo automatico via timer systemd (già attivo):

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run   # test rinnovo
```

---

## Moduli Apache richiesti

```bash
sudo a2enmod proxy proxy_http headers ssl rewrite
sudo systemctl restart apache2
```

---

## Sequenza di riavvio dopo aggiornamenti

```bash
# 1. Aggiorna codice
cd /home/ltc/projects/ltcboxoffice/ltcboxoffice
git pull

# 2. Attiva virtualenv e aggiorna dipendenze se necessario
source .env/bin/activate
pip install -r requirements.txt

# 3. Migrazioni e static files
export $(grep -v '^#' .env.production | xargs)
export DJANGO_SETTINGS_MODULE=ltcboxoffice.settings.production
python manage.py migrate
python manage.py collectstatic --noinput

# 4. Riavvia Gunicorn
sudo systemctl restart ltcboxoffice

# 5. Apache non va riavviato salvo modifiche ai suoi config file
```
