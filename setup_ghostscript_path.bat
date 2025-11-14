@echo off
REM Script per aggiungere Ghostscript al PATH di sistema
REM Richiede privilegi di amministratore

echo ================================================
echo   Configurazione PATH per Ghostscript
echo ================================================
echo.

REM Controlla se lo script è eseguito come amministratore
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo NOTA: Per aggiungere al PATH di sistema serve eseguire come Amministratore
    echo       Al momento verrà aggiunto solo al PATH utente.
    echo.
    pause
)

set "GS_PATH=C:\Program Files\gs\gs10.06.0\bin"

REM Verifica che Ghostscript sia installato
if not exist "%GS_PATH%\gswin64c.exe" (
    echo ERRORE: Ghostscript non trovato in %GS_PATH%
    echo.
    echo Installa Ghostscript prima di eseguire questo script:
    echo   - Esegui: install_ghostscript.bat
    echo   - Oppure: choco install ghostscript -y
    echo.
    pause
    exit /b 1
)

echo Ghostscript trovato in: %GS_PATH%
echo.

REM Aggiunge al PATH utente
echo Aggiunta al PATH utente in corso...
setx PATH "%PATH%;%GS_PATH%" >nul 2>&1

echo.
echo ================================================
echo   Configurazione completata!
echo ================================================
echo.
echo PATH aggiornato. Ghostscript è ora disponibile.
echo.
echo Verifica installazione:
where gswin64c
echo.
echo Versione installata:
"%GS_PATH%\gswin64c.exe" --version
echo.
echo ================================================
echo   IMPORTANTE
echo ================================================
echo.
echo Per rendere effettive le modifiche:
echo 1. Chiudi TUTTI i terminali PowerShell/CMD aperti
echo 2. Chiudi VS Code (se aperto)
echo 3. Riapri VS Code e il terminale
echo 4. Riavvia il server Django: python manage.py runserver
echo.
echo Ora i barcode verranno generati automaticamente!
echo.
pause
