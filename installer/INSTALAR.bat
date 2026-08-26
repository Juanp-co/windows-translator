@echo off
title traslatetool - instalador
cd /d "%~dp0"

echo.
echo   traslatetool - instalador
echo   =========================
echo.
echo   Iniciando... (aceptar el aviso de Windows si aparece)
echo.

REM La elevacion la hace instalar.ps1, no este .bat: PowerShell reporta
REM los errores en vez de cerrar la ventana en silencio.
REM -ExecutionPolicy Bypass: Windows no ejecuta .ps1 sin firmar por defecto.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
set RC=%errorlevel%

if not "%RC%"=="0" (
    echo.
    echo   El instalador termino con codigo %RC%.
    echo   Alternativa manual:
    echo     https://github.com/Juanp-co/windows-translator/releases/latest
    echo.
)

REM pause SIEMPRE: sin esto, cualquier fallo cierra la ventana sin que se lea.
pause
