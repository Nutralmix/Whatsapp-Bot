@echo off
chcp 65001 > nul
echo ===============================
echo Iniciando servidor Flask Bot_RRHH...
echo ===============================

cd /d C:\Bot_RRHH

REM Ejecutar la app con Flask directamente
C:\Bot_RRHH\.venv\Scripts\python.exe app.py
