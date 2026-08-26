@echo off
REM traslatetool - lanzador. Doble clic y listo.
REM Se auto-eleva a administrador: importar el certificado lo exige.

net session >nul 2>&1
if %errLevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

REM -ExecutionPolicy Bypass: por defecto Windows no ejecuta .ps1 sin firmar.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
