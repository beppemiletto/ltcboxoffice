# Cleanup Automatico Carrelli Abbandonati

Sistema automatico per liberare i posti bloccati in carrelli non finalizzati dopo un timeout configurabile.

## Funzionalità

### 1. Comando Management Django

**Uso Manuale:**
```bash
# Esecuzione standard (timeout 15 minuti)
python manage.py cleanup_abandoned_carts

# Con timeout personalizzato
python manage.py cleanup_abandoned_carts --minutes 20

# Dry-run (mostra solo cosa verrebbe fatto)
python manage.py cleanup_abandoned_carts --dry-run

# Per un evento specifico
python manage.py cleanup_abandoned_carts --event-id 42
```

**Cosa fa:**
1. Trova tutti i `SellingSeats` creati oltre X minuti fa
2. Filtra solo quelli senza `orderevent` (non finalizzati)
3. Aggiorna i file JSON degli eventi (status 4 → 0)
4. Elimina i record dal database
5. Mostra report dettagliato

**Output esempio:**
```
⚠ Trovati 12 posti in 2 eventi:

  Evento: La Locandiera (19/11/2025 21:00)
  Posti da liberare: 8
    Posti: C05, C06, C07, D05, D06, D07, E05, E06
    Sessioni: 2 diverse
    Più vecchio: 23 minuti fa

✓ Cleanup completato:
  - 12 record SellingSeats eliminati dal database
  - 12 posti liberati nei file JSON
  - 2 eventi aggiornati
```

### 2. Task Celery Automatico

**Configurazione:**
Il task è già configurato in `settings/base.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-abandoned-carts': {
        'task': 'boxoffice.cleanup_abandoned_carts',
        'schedule': crontab(minute='*/15'),  # Ogni 15 minuti
        'kwargs': {'timeout_minutes': 15},
    },
}
```

**Avvio Celery Beat:**
```bash
# Terminal 1 - Worker
celery -A ltcboxoffice worker -l info

# Terminal 2 - Beat scheduler
celery -A ltcboxoffice beat -l info
```

**In produzione (supervisord/systemd):**
```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A ltcboxoffice worker -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

[program:celery_beat]
command=/path/to/venv/bin/celery -A ltcboxoffice beat -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
```

### 3. Azione Admin Django

**Accesso:** `/admin/boxoffice/sellingseats/`

**Features:**
- Colonna "Età" con colori:
  - Verde: < 15 min
  - Arancione: 15-60 min
  - Rosso: > 60 min
  
- Colonna "Stato":
  - ✓ OK: Posto finalizzato o recente
  - ⚠ ABBANDONATO: Senza orderevent e > 15 min

- Azione bulk: "🧹 Libera posti abbandonati selezionati"
  - Seleziona i record da pulire
  - Click su "Azione" → "Libera posti abbandonati"
  - Conferma

**Screenshot esempio:**
```
| Evento          | Posto | OrderEvent | Session ID | Età      | Stato          |
|-----------------|-------|------------|------------|----------|----------------|
| La Locandiera   | C05   | -          | a3f5b2... | 18 min   | ⚠ ABBANDONATO  |
| La Locandiera   | C06   | 00042_... | a3f5b2... | 5 min    | ✓ OK           |
| Il Malato...    | D08   | -          | c7d9e1... | 2 ore    | ⚠ ABBANDONATO  |
```

## Configurazione

### Timeout Default
Modifica in `settings/base.py`:

```python
# Per cambiare il timeout globale
CELERY_BEAT_SCHEDULE = {
    'cleanup-abandoned-carts': {
        'task': 'boxoffice.cleanup_abandoned_carts',
        'schedule': crontab(minute='*/15'),
        'kwargs': {'timeout_minutes': 20},  # ← Cambia qui
    },
}
```

### Frequenza Esecuzione
```python
# Ogni 10 minuti
'schedule': crontab(minute='*/10'),

# Ogni ora
'schedule': crontab(minute=0),

# Solo nelle ore di punta (18-23)
'schedule': crontab(minute='*/15', hour='18-23'),
```

## Monitoraggio

### Log Celery
I task automatici loggano in Celery:

```bash
tail -f /var/log/celery/worker.log
```

Output:
```
[2025-11-19 15:30:00] Task boxoffice.cleanup_abandoned_carts succeeded:
{
  'status': 'success',
  'freed_seats': 8,
  'deleted_records': 8,
  'updated_events': 2,
  'timeout_minutes': 15
}
```

### Django Admin Log
Le azioni admin sono registrate nel log di Django:

```python
# In settings.py - già configurato
LOGGING = {
    'loggers': {
        'boxoffice': {
            'level': 'INFO',
            'handlers': ['file'],
        },
    }
}
```

### Metriche Custom
Aggiungi monitoring con `django-prometheus` o `sentry`:

```python
from celery.signals import task_success

@task_success.connect(sender=cleanup_abandoned_carts_task)
def log_cleanup_metrics(sender, result, **kwargs):
    # Invia metriche a Prometheus/Grafana
    freed_seats_metric.inc(result['freed_seats'])
```

## Troubleshooting

### Problema: I posti rimangono bloccati
**Causa:** Celery beat non è avviato
**Soluzione:**
```bash
celery -A ltcboxoffice beat -l info
# Verifica output: "Scheduler: Sending due task cleanup-abandoned-carts"
```

### Problema: Errore "JSON file not found"
**Causa:** File JSON evento mancante
**Soluzione:**
```python
# Rigenera JSON da admin o shell
from store.models import Event
event = Event.objects.get(id=42)
event.init_hall_json()  # Se metodo esiste
```

### Problema: Record eliminati ma JSON non aggiornato
**Causa:** Permessi file o path errato
**Soluzione:**
```bash
# Verifica permessi
ls -la hall_jsons/
chmod 664 hall_jsons/*.json
chown www-data:www-data hall_jsons/
```

### Problema: Task Celery non si avvia
**Causa:** Redis non raggiungibile
**Soluzione:**
```bash
# Verifica Redis
redis-cli ping
# PONG

# Controlla settings
echo $CELERY_BROKER_URL
# redis://localhost:6379
```

## Best Practices

### 1. Timeout Progressivo
Configurare timeout diversi per orari diversi:

```python
# settings/production.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Ore di punta: cleanup più frequente, timeout breve
    'cleanup-peak-hours': {
        'task': 'boxoffice.cleanup_abandoned_carts',
        'schedule': crontab(minute='*/10', hour='18-23'),
        'kwargs': {'timeout_minutes': 10},
    },
    # Ore normali: meno frequente, timeout standard
    'cleanup-normal-hours': {
        'task': 'boxoffice.cleanup_abandoned_carts',
        'schedule': crontab(minute='*/30', hour='9-17,0-8'),
        'kwargs': {'timeout_minutes': 20},
    },
}
```

### 2. Notifiche Anomalie
Aggiungi alert se troppi carrelli abbandonati:

```python
# boxoffice/tasks.py
@shared_task
def cleanup_abandoned_carts_task(timeout_minutes=15):
    # ... cleanup code ...
    
    if result['freed_seats'] > 50:
        # Troppi abbandoni - possibile problema UX
        send_admin_email(
            subject="Alert: Molti carrelli abbandonati",
            message=f"Liberati {result['freed_seats']} posti in un solo ciclo"
        )
    
    return result
```

### 3. Backup Prima di Cleanup
Per sicurezza, backup JSON prima di modificare:

```python
# boxoffice/management/commands/cleanup_abandoned_carts.py
import shutil
from datetime import datetime

# Backup JSON
backup_dir = f"hall_jsons/backups/{datetime.now():%Y%m%d_%H%M%S}"
os.makedirs(backup_dir, exist_ok=True)
shutil.copy(json_file_path, backup_dir)
```

## Performance

### Ottimizzazione Query
Il comando usa `select_related('event')` per ridurre query:

```python
# Invece di N+1 queries:
for seat in SellingSeats.objects.all():
    event = seat.event  # Query per ogni seat

# Usa select_related:
for seat in SellingSeats.objects.select_related('event'):
    event = seat.event  # No extra query
```

### Batch Processing
Per grandi quantità (>1000 posti):

```python
# Processa a batch
BATCH_SIZE = 100
abandoned = SellingSeats.objects.filter(...)

for i in range(0, abandoned.count(), BATCH_SIZE):
    batch = abandoned[i:i+BATCH_SIZE]
    # Process batch
```

### Index Database
Aggiungi index per performance:

```python
# boxoffice/models.py
class SellingSeats(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['orderevent', 'created_at']),
            models.Index(fields=['event', 'created_at']),
        ]
```

Migration:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing

### Test Manuale
```bash
# 1. Crea carrello test
python manage.py shell
>>> from boxoffice.models import SellingSeats
>>> from store.models import Event
>>> seat = SellingSeats.objects.create(
...     event=Event.objects.first(),
...     seat='Z99',
...     session_id='test-session'
... )

# 2. Forza timestamp vecchio
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> seat.created_at = timezone.now() - timedelta(minutes=20)
>>> seat.save()

# 3. Esegui cleanup
python manage.py cleanup_abandoned_carts --dry-run

# 4. Verifica
>>> SellingSeats.objects.filter(seat='Z99').exists()
False  # ✓ Eliminato
```

### Test Automatico
```python
# boxoffice/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import SellingSeats
from .tasks import cleanup_abandoned_carts_task

class CleanupTest(TestCase):
    def test_cleanup_old_abandoned_seats(self):
        # Setup
        event = Event.objects.create(...)
        old_seat = SellingSeats.objects.create(
            event=event,
            seat='A01',
            created_at=timezone.now() - timedelta(minutes=20)
        )
        
        # Execute
        result = cleanup_abandoned_carts_task(timeout_minutes=15)
        
        # Verify
        self.assertEqual(result['freed_seats'], 1)
        self.assertFalse(SellingSeats.objects.filter(pk=old_seat.pk).exists())
```

## Migrazione da Sistema Vecchio

Se hai già posti bloccati senza `created_at`:

```bash
# 1. Cleanup manuale iniziale
python manage.py shell
>>> from boxoffice.models import SellingSeats
>>> SellingSeats.objects.filter(orderevent__isnull=True).delete()

# 2. Oppure assegna timestamp fittizio
>>> from django.utils import timezone
>>> SellingSeats.objects.filter(created_at__isnull=True).update(
...     created_at=timezone.now()
... )
```

## Riferimenti

- Comando: `boxoffice/management/commands/cleanup_abandoned_carts.py`
- Task Celery: `boxoffice/tasks.py`
- Admin: `boxoffice/admin.py` (azione `cleanup_abandoned_seats`)
- Configurazione: `ltcboxoffice/settings/base.py` (CELERY_BEAT_SCHEDULE)
- Test: `TEST_MULTI_CASSA.md` (Scenario 4)
