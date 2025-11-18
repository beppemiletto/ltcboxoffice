# Activate production environment
.\venv\Scripts\Activate.ps1
$env:DJANGO_SETTINGS_MODULE = "ltcboxoffice.settings.production"
Write-Host "Production environment activated" -ForegroundColor Red
Write-Host "DJANGO_SETTINGS_MODULE = $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Cyan

# Production environment variables (set these before deploying)
# $env:SECRET_KEY = "your-secret-key-here"
# $env:DB_NAME = "ltcboxoffice_prod"
# $env:DB_USER = "produser"
# $env:DB_PASSWORD = "prodpassword"
# $env:PRINTER_HOST = "192.168.1.100"
