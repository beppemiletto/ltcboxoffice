@echo off
REM Script per installare Ghostscript usando Chocolatey
REM Richiede privilegi di amministratore

echo ================================================
echo   Installazione Ghostscript per LTC BoxOffice
echo ================================================
echo.

REM Controlla se lo script è eseguito come amministratore
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERRORE: Questo script deve essere eseguito come Amministratore!
    echo.
    echo Come fare:
    echo 1. Click destro su questo file .bat
    echo 2. Seleziona "Esegui come amministratore"
    echo.
    pause
    exit /b 1
)

echo Installazione di Ghostscript in corso...
echo.

choco install ghostscript -y

if %errorLevel% EQU 0 (
    echo.
    echo ================================================
    echo   Ghostscript installato con successo!
    echo ================================================
    echo.
    echo Verifica installazione:
    where gswin64c
    echo.
    echo Versione:
    gswin64c --version
    echo.
    echo Ora puoi riavviare il server Django e riprovare.
) else (
    echo.
    echo ================================================
    echo   ERRORE durante l'installazione
    echo ================================================
    echo.
    echo Prova l'installazione manuale:
    echo https://www.ghostscript.com/releases/gsdnld.html
)

echo.
pause
