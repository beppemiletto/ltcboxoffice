# Deployment Guide

## Production Deployment Checklist

### Before Deployment

- [ ] Set `DJANGO_ENV=production`
- [ ] Generate a new `SECRET_KEY` (never use the development key)
- [ ] Configure all environment variables in `.env`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure database with production credentials
- [ ] Set up email server
- [ ] Configure Redis for Celery
- [ ] Review and test all security settings

### Environment Variables

Required production environment variables:

```bash
DJANGO_ENV=production
SECRET_KEY=your-secure-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=ltcboxoffice
DB_USER=production_user
DB_PASSWORD=strong-database-password
DB_HOST=localhost
DB_PORT=3306

# Email
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=email-password
EMAIL_USE_TLS=True

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

### Server Setup

#### Option 1: Traditional VPS/Dedicated Server

1. **Install system dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.11 python3.11-venv python3-pip
   sudo apt-get install -y mysql-server redis-server nginx
   sudo apt-get install -y libmysqlclient-dev pkg-config
   ```

2. **Clone and setup project**
   ```bash
   git clone https://github.com/beppemiletto/ltcboxoffice.git
   cd ltcboxoffice
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

4. **Run migrations and collect static**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. **Set up Gunicorn service**
   Create `/etc/systemd/system/ltcboxoffice.service`:
   ```ini
   [Unit]
   Description=LTC Box Office Gunicorn
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/ltcboxoffice
   Environment="PATH=/path/to/ltcboxoffice/venv/bin"
   ExecStart=/path/to/ltcboxoffice/venv/bin/gunicorn \
             --workers 3 \
             --bind unix:/run/ltcboxoffice.sock \
             ltcboxoffice.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

6. **Set up Celery services**
   Create `/etc/systemd/system/ltcboxoffice-celery.service`:
   ```ini
   [Unit]
   Description=LTC Box Office Celery Worker
   After=network.target

   [Service]
   Type=forking
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/ltcboxoffice
   Environment="PATH=/path/to/ltcboxoffice/venv/bin"
   ExecStart=/path/to/ltcboxoffice/venv/bin/celery -A ltcboxoffice worker --loglevel=info

   [Install]
   WantedBy=multi-user.target
   ```

7. **Configure Nginx**
   Create `/etc/nginx/sites-available/ltcboxoffice`:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       ssl_certificate /path/to/ssl/cert.pem;
       ssl_certificate_key /path/to/ssl/key.pem;

       client_max_body_size 20M;

       location /static/ {
           alias /path/to/ltcboxoffice/staticfiles/;
       }

       location /media/ {
           alias /path/to/ltcboxoffice/media/;
       }

       location / {
           proxy_pass http://unix:/run/ltcboxoffice.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

8. **Enable and start services**
   ```bash
   sudo systemctl enable ltcboxoffice
   sudo systemctl enable ltcboxoffice-celery
   sudo systemctl enable nginx
   sudo systemctl start ltcboxoffice
   sudo systemctl start ltcboxoffice-celery
   sudo systemctl restart nginx
   ```

#### Option 2: Docker Deployment

1. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

### Database Backup

Set up automated backups:

```bash
#!/bin/bash
# /usr/local/bin/backup-ltcboxoffice.sh

BACKUP_DIR="/backups/ltcboxoffice"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
mysqldump -u $DB_USER -p$DB_PASSWORD ltcboxoffice > "$BACKUP_DIR/db_$DATE.sql"

# Media files backup
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /path/to/ltcboxoffice/media/

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Add to crontab: `0 2 * * * /usr/local/bin/backup-ltcboxoffice.sh`

### Monitoring

- Set up application monitoring (Sentry, New Relic, etc.)
- Monitor server resources (CPU, memory, disk)
- Set up log rotation
- Monitor Celery queues
- Set up uptime monitoring

### Security

- Keep system packages updated
- Use fail2ban for SSH protection
- Configure firewall (ufw/iptables)
- Regular security audits
- Monitor access logs
- Use strong passwords everywhere

### Maintenance

```bash
# Update application
cd /path/to/ltcboxoffice
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart ltcboxoffice
sudo systemctl restart ltcboxoffice-celery
```
