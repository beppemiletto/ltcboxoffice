@echo off
REM ========================================
REM Script per avviare debug QR Scanner
REM ========================================

echo.
echo ========================================
echo   Scanner QR Mobile - Debug Setup
echo ========================================
echo.

REM Controlla se ngrok è installato
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ngrok non trovato!
    echo.
    echo Installalo con:
    echo   choco install ngrok
    echo.
    echo Oppure scarica da: https://ngrok.com/download
    echo.
    pause
    exit /b 1
)

echo [1/4] Attivazione ambiente virtuale...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Impossibile attivare venv!
    pause
    exit /b 1
)

echo [2/4] Avvio server Django su porta 8000...
start "Django Server" cmd /k "python manage.py runserver 0.0.0.0:8000"

REM Attendi 3 secondi per dare tempo al server di avviarsi
timeout /t 3 /nobreak >nul

echo [3/4] Avvio tunnel ngrok...
start "ngrok Tunnel" cmd /k "ngrok http 8000"

REM Attendi 2 secondi per dare tempo a ngrok
timeout /t 2 /nobreak >nul

echo [4/4] Recupero URL ngrok...
timeout /t 2 /nobreak >nul

REM Prova a ottenere l'URL da API ngrok
powershell -Command "$response = Invoke-RestMethod -Uri 'http://localhost:4040/api/tunnels'; $url = $response.tunnels[0].public_url; Write-Host ''; Write-Host '========================================' -ForegroundColor Green; Write-Host '  Setup Completato!' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Green; Write-Host ''; Write-Host 'URL NGROK:' $url -ForegroundColor Yellow; Write-Host ''; Write-Host 'PROSSIMI PASSI:' -ForegroundColor Cyan; Write-Host '1. Aggiungi questo URL in settings.py:' -ForegroundColor White; Write-Host '   ALLOWED_HOSTS = [..., '''$url.Replace('https://', '').Replace('http://', '')''']' -ForegroundColor Gray; Write-Host '   CSRF_TRUSTED_ORIGINS = [..., '''$url''']' -ForegroundColor Gray; Write-Host ''; Write-Host '2. Riavvia il server Django' -ForegroundColor White; Write-Host ''; Write-Host '3. Apri sul cellulare:' -ForegroundColor White; Write-Host '   '$url'/boxoffice/qr_scanner/1/' -ForegroundColor Yellow; Write-Host ''; Write-Host 'Dashboard ngrok: http://127.0.0.1:4040' -ForegroundColor Magenta; Write-Host '';"

echo.
echo ========================================
echo   Servizi Avviati
echo ========================================
echo.
echo - Django Server: http://localhost:8000
echo - ngrok Dashboard: http://127.0.0.1:4040
echo.
echo Premi un tasto per aprire la dashboard ngrok...
pause >nul
start http://127.0.0.1:4040

echo.
echo Per fermare i servizi, chiudi le finestre del terminale.
echo.
pause
