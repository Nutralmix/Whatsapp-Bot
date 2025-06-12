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
