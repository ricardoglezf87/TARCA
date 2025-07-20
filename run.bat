@echo off
REM Este script inicia la aplicaciÃ³n TARCA sin una ventana de consola visible.
REM Utiliza 'pythonw.exe', el intÃ©rprete para aplicaciones Python sin ventana/GUI.

REM Obtiene el directorio donde se encuentra este archivo .bat para que el script sea portable.
set "SCRIPT_DIR=%~dp0"

REM El comando 'start "TÃ­tulo" /B' inicia un programa sin crear una nueva ventana.
REM Usamos la ruta completa al script de Python para asegurar que se ejecute correctamente.
start "TARCA" /B pythonw.exe "%SCRIPT_DIR%TARCA.py"