# Deployment — prenota.teatrocambiano.com

Guida al deployment reale del progetto sul server di produzione.

## Infrastruttura

| Componente | Dettaglio |
|---|---|
| Server | Linux Mint, utente `ltc` |
| Dominio | `prenota.teatrocambiano.com` |
| Web server | Apache 2.4 (reverse proxy, SSL, media files) |
| WSGI server | Gunicorn (porta 8000, gestito da systemd) |
| Database | MariaDB, db `ltcboxoffice`, utente `djangodbuser` |
| Cache | Redis (`redis://127.0.0.1:6379/1`) |
| SSL | Let's Encrypt / Certbot (rinnovo automatico) |
| Python | 3.10, virtualenv in `.env/` |
| Settings | `ltcboxoffice.settings.production` |

---

## Primo deploy (da zero)

### 1. Dipendenze di sistema

```bash
sudo apt install apache2 libapache2-mod-proxy libapache2-mod-headers
sudo apt install mariadb-server redis-server python3.10-venv
sudo apt install certbot python3-certbot-apache
sudo a2enmod proxy proxy_http headers ssl rewrite
```

### 2. Virtualenv e dipendenze Python

```bash
cd /home/ltc/projects/ltcboxoffice/ltcboxoffice
python3.10 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

### 3. Variabili d'ambiente

Il file `.env.production` (non versionato) va creato nella root del progetto:

```
SECRET_KEY=<chiave segreta>
DB_NAME=ltcboxoffice
DB_USER=djangodbuser
DB_PASSWORD=<password db>
DB_HOST=127.0.0.1
DB_PORT=3306
EMAIL_HOST=smtp.teatrocambiano.com
EMAIL_PORT=587
EMAIL_HOST_USER=ltcboxoffice@teatrocambiano.com
EMAIL_HOST_PASSWORD=<password email>
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=ltcboxoffice@teatrocambiano.com
ALLOWED_HOSTS=prenota.teatrocambiano.com,127.0.0.1,localhost
REDIS_URL=redis://127.0.0.1:6379/1
```

### 4. Database e file statici

```bash
export $(grep -v '^#' .env.production | xargs)
export DJANGO_SETTINGS_MODULE=ltcboxoffice.settings.production
source .env/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5. Servizio Gunicorn (systemd)

Crea `/etc/systemd/system/ltcboxoffice.service` (vedi `APACHE_PRODUCTION.md` per il contenuto completo), poi:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ltcboxoffice
sudo systemctl start ltcboxoffice
```

### 6. Apache e SSL

Configura i VirtualHost HTTP e HTTPS come documentato in `APACHE_PRODUCTION.md`, poi ottieni il certificato:

```bash
sudo certbot --apache -d prenota.teatrocambiano.com
```

**Attenzione ai permessi filesystem** — Apache (`www-data`) deve poter attraversare la home directory:

```bash
chmod o+x /home/ltc/projects
```

Senza questo comando le immagini `/media/` restituiscono 403. Vedi `APACHE_PRODUCTION.md` per la spiegazione completa.

---

## Aggiornamenti (deploy ordinario)

```bash
cd /home/ltc/projects/ltcboxoffice/ltcboxoffice
git pull

source .env/bin/activate
export $(grep -v '^#' .env.production | xargs)
export DJANGO_SETTINGS_MODULE=ltcboxoffice.settings.production

python manage.py migrate          # solo se ci sono nuove migrazioni
python manage.py collectstatic --noinput   # solo se cambia il CSS/JS

sudo systemctl restart ltcboxoffice
```

---

## Comandi operativi

```bash
# Stato servizi
sudo systemctl status ltcboxoffice
sudo systemctl status apache2
sudo systemctl status redis-server

# Log applicazione
sudo journalctl -u ltcboxoffice -n 50 -f

# Log Apache
sudo tail -f /var/log/apache2/prenota_error.log

# Riavvio rapido dopo modifica al codice
sudo systemctl restart ltcboxoffice
```

---

## Backup database

```bash
mysqldump -u djangodbuser -p ltcboxoffice > backup_$(date +%Y%m%d).sql
```

---

## Documentazione correlata

- `APACHE_PRODUCTION.md` — configurazione dettagliata Apache, permessi filesystem, SSL
