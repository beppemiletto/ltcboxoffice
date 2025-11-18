# Activate development environment
.\venv\Scripts\Activate.ps1
$env:DJANGO_SETTINGS_MODULE = "ltcboxoffice.settings.development"
Write-Host "Development environment activated" -ForegroundColor Green
Write-Host "DJANGO_SETTINGS_MODULE = $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Cyan
