@echo off
chcp 65001 > nul
echo ===============================
echo Iniciando servidor Flask RRHH...
echo Fecha y hora: %DATE% %TIME%
echo ===============================

cd /d C:\Bot_RRHH

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Ejecutar el BOT (actualizaciones, git, etc.)
echo Ejecutando bot.py...
python bot.py > bot_log.txt 2>&1
echo bot.py terminado. Salida guardada en bot_log.txt

REM Iniciar el servidor Flask con waitress
echo Iniciando servidor Flask con Waitress...
python -m waitress --host 0.0.0.0 --port 10000 app:app >> log.txt 2>&1
