@echo off
REM ========================================
REM Fix Chocolatey Pending Process Block
REM ========================================

echo.
echo ========================================
echo   Fix Chocolatey Pending Process
echo ========================================
echo.

echo [Metodo 1] Terminazione processi Chocolatey...
echo.

REM Termina tutti i processi chocolatey
taskkill /F /IM choco.exe 2>nul
taskkill /F /IM chocolatey.exe 2>nul
taskkill /F /IM ShimGen.exe 2>nul

echo.
echo [Metodo 2] Rimozione file di lock...
echo.

REM Rimuovi i file di lock
if exist "%TEMP%\.chocolatey\*" (
    echo Rimozione file temporanei Chocolatey...
    rmdir /S /Q "%TEMP%\.chocolatey\" 2>nul
)

if exist "%ProgramData%\chocolatey\.chocolatey\*.lock" (
    echo Rimozione file lock...
    del /F /Q "%ProgramData%\chocolatey\.chocolatey\*.lock" 2>nul
)

if exist "%ProgramData%\chocolatey\lib-pending\*" (
    echo Pulizia installazioni pending...
    rmdir /S /Q "%ProgramData%\chocolatey\lib-pending\" 2>nul
)

echo.
echo [Metodo 3] Reset stato Chocolatey...
echo.

REM Reset cache chocolatey
if exist "%LocalAppData%\Temp\chocolatey\*" (
    echo Pulizia cache locale...
    rmdir /S /Q "%LocalAppData%\Temp\chocolatey\" 2>nul
)

echo.
echo ========================================
echo   Cleanup Completato!
echo ========================================
echo.
echo Ora puoi riprovare l'installazione:
echo   choco install ngrok
echo.
echo OPPURE scarica ngrok manualmente da:
echo   https://ngrok.com/download
echo.

pause
