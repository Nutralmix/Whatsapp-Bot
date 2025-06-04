# utils.py
import json

def cargar_empleados_activos():
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)
    return {
        legajo: datos for legajo, datos in empleados.items()
        if datos.get("estado") == "Activo"
    }
