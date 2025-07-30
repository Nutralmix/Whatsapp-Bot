@echo off
chcp 65001 > nul
echo ===============================
echo Iniciando servidor Flask Bot_RRHH...
echo ===============================

cd /d C:\Bot_RRHH

REM Ejecutar directamente con Python del entorno virtual
C:\Bot_RRHH\.venv\Scripts\python.exe -m waitress --host 0.0.0.0 --port 10000 app:app
