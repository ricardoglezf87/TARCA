@echo off
setlocal

REM Arranca TARCA desde la carpeta donde vive este .bat.
set "SCRIPT_DIR=%~dp0"

if /I "%~1"=="console" goto console
if /I "%~1"=="visible" goto console
if /I "%~1"=="background" goto background
if /I "%~1"=="hidden" goto background

echo.
echo TARCA - modo de inicio
echo.
echo   1. Consola visible con respuestas y errores
echo   2. Segundo plano sin consola
echo.
choice /C 12 /N /M "Elige una opcion [1-2]: "
if errorlevel 2 goto background

:console
title TARCA - consola
echo.
echo Iniciando TARCA con consola visible...
echo Cierra esta ventana o usa el menu de bandeja para salir.
echo.
python.exe "%SCRIPT_DIR%main.py"
echo.
echo TARCA se ha cerrado.
pause
goto end

:background
start "TARCA" /B pythonw.exe "%SCRIPT_DIR%main.py"
goto end

:end
endlocal
