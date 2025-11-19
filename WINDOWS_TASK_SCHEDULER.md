# Configurazione Windows Task Scheduler per Cleanup Carrelli

## Opzione 1: Interfaccia Grafica

1. **Apri Task Scheduler**:
   - Premi `Win + R`
   - Digita `taskschd.msc`
   - Invio

2. **Crea Task**:
   - Click su "Create Task" nel pannello destro
   - **General Tab**:
     - Name: `LTC BoxOffice - Cleanup Carrelli`
     - Description: `Libera posti abbandonati ogni 15 minuti`
     - Run whether user is logged on or not: ✓
     - Run with highest privileges: ✓

3. **Triggers Tab**:
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Daily`
   - Recur every: `1 days`
   - Repeat task every: `15 minutes`
   - for a duration of: `1 day`
   - Enabled: ✓
   - OK

4. **Actions Tab**:
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `powershell.exe`
   - Add arguments:
     ```
     -ExecutionPolicy Bypass -File "C:\Users\Asus\projects\python\ltcboxoffice\scripts\cleanup_carts_scheduled.ps1"
     ```
   - OK

5. **Conditions Tab**:
   - Deseleziona "Start the task only if the computer is on AC power"
   - ✓ Wake the computer to run this task (se necessario)

6. **Settings Tab**:
   - ✓ Allow task to be run on demand
   - ✓ If the task fails, restart every: `5 minutes` (3 tentativi)
   - Stop the task if it runs longer than: `10 minutes`

7. **Save** e inserisci password se richiesta

---

## Opzione 2: PowerShell Script

Esegui questo script PowerShell **come Amministratore**:

```powershell
# Crea scheduled task per cleanup carrelli
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\Users\Asus\projects\python\ltcboxoffice\scripts\cleanup_carts_scheduled.ps1"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "LTC BoxOffice - Cleanup Carrelli" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Libera posti abbandonati ogni 15 minuti" `
    -RunLevel Highest
```

---

## Opzione 3: Cron-style (WSL/Linux)

Se usi Windows Subsystem for Linux:

```bash
# Modifica crontab
crontab -e

# Aggiungi questa linea (esegue ogni 15 minuti)
*/15 * * * * cd /mnt/c/Users/Asus/projects/python/ltcboxoffice && /mnt/c/Users/Asus/projects/python/ltcboxoffice/venv/bin/python manage.py cleanup_abandoned_carts --verbosity 0 >> /var/log/cleanup_carts.log 2>&1
```

---

## Verifica Configurazione

### Test Manuale Task
```powershell
# In PowerShell normale (non admin)
cd C:\Users\Asus\projects\python\ltcboxoffice
.\scripts\cleanup_carts_scheduled.ps1
```

### Verifica Task Scheduler
```powershell
# Lista tutti i task
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Cleanup*"}

# Esegui task manualmente
Start-ScheduledTask -TaskName "LTC BoxOffice - Cleanup Carrelli"

# Controlla ultimo risultato
Get-ScheduledTaskInfo -TaskName "LTC BoxOffice - Cleanup Carrelli"
```

### Logs
I log saranno in:
- `C:\Users\Asus\projects\python\ltcboxoffice\logs\cleanup_carts.log`
- Event Viewer: Task Scheduler Operational logs

---

## Alternativa: Python APScheduler

Se preferisci gestire lo scheduling dentro l'applicazione Django:

```python
# Installa
pip install apscheduler

# In settings.py
INSTALLED_APPS += ['django_apscheduler']

# Crea job
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: call_command('cleanup_abandoned_carts'),
        'interval',
        minutes=15,
        id='cleanup_carts',
        replace_existing=True
    )
    scheduler.start()

# In wsgi.py o apps.py
from .scheduler import start_scheduler
start_scheduler()
```

---

## Note Python 3.13

**Problema Celery:**
- Celery 5.3.6 usa `billiard` che non supporta ancora Python 3.13
- `logging._acquireLock()` rimosso in Python 3.13
- Issue aperta: https://github.com/celery/billiard/issues/377

**Workaround Temporaneo:**
Usare Task Scheduler fino a quando Celery/billiard verranno aggiornati.

**Monitoring:**
```powershell
# Crea cartella logs se non esiste
New-Item -ItemType Directory -Force -Path C:\Users\Asus\projects\python\ltcboxoffice\logs

# Visualizza log
Get-Content C:\Users\Asus\projects\python\ltcboxoffice\logs\cleanup_carts.log -Tail 20 -Wait
```

---

## Produzione (Linux/Ubuntu)

Per il server di produzione:

```bash
# Crontab
crontab -e

# Aggiungi (ogni 15 minuti)
*/15 * * * * cd /var/www/ltcboxoffice && /var/www/ltcboxoffice/venv/bin/python manage.py cleanup_abandoned_carts --verbosity 0 >> /var/log/ltc/cleanup_carts.log 2>&1

# Systemd timer (alternativa)
sudo systemctl enable cleanup-carts.timer
sudo systemctl start cleanup-carts.timer
```

File systemd:
```ini
# /etc/systemd/system/cleanup-carts.service
[Unit]
Description=LTC BoxOffice Cleanup Abandoned Carts

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/var/www/ltcboxoffice
ExecStart=/var/www/ltcboxoffice/venv/bin/python manage.py cleanup_abandoned_carts

# /etc/systemd/system/cleanup-carts.timer
[Unit]
Description=Run cleanup every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
```
