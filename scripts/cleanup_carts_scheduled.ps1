# Script PowerShell per cleanup automatico carrelli
# Da configurare in Windows Task Scheduler

# Attiva ambiente virtuale
& "C:\Users\Asus\projects\python\ltcboxoffice\venv\Scripts\Activate.ps1"

# Esegui cleanup
python "C:\Users\Asus\projects\python\ltcboxoffice\manage.py" cleanup_abandoned_carts --verbosity 0

# Logging (opzionale)
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "C:\Users\Asus\projects\python\ltcboxoffice\logs\cleanup_carts.log" -Value "[$timestamp] Cleanup executed"
