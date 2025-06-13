import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

def cargar_empleados_activos():
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)
    return {
        legajo: datos for legajo, datos in empleados.items()
        if datos.get("estado") == "Activo"
    }

def calcular_antiguedad(fecha_ingreso_str):
    try:
        fecha_ingreso = datetime.strptime(fecha_ingreso_str, "%d-%m-%Y")
        hoy = datetime.now()
        diferencia = relativedelta(hoy, fecha_ingreso)
        return f"{diferencia.years} años y {diferencia.months} meses"
    except:
        return "?"


import requests
from datetime import datetime

def obtener_proximos_feriados():
    anio = datetime.now().year
    url = f"https://api.argentinadatos.com/v1/feriados/{anio}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    feriados = resp.json()
    hoy = datetime.now().date()
    # Filtramos solo los que vienen después de hoy
    proxs = [f for f in feriados if datetime.fromisoformat(f["fecha"]).date() >= hoy]
    return sorted(proxs, key=lambda f: f["fecha"])



