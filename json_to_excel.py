import json
import pandas as pd
from datetime import datetime

# === Cargar empleados desde JSON ===
try:
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados_data = json.load(f)
except FileNotFoundError:
    print("❌ No se encontró el archivo empleados.json.")
    exit()

# === Convertir a lista de diccionarios ===
empleados_lista = []
for legajo, datos in empleados_data.items():
    empleado = {"legajo": legajo}
    empleado.update(datos)

    # Si el campo 'prestamo' es un diccionario, lo expandimos
    if isinstance(empleado.get("prestamo"), dict):
        for k, v in empleado["prestamo"].items():
            empleado[f"prestamo_{k}"] = v
        del empleado["prestamo"]

    empleados_lista.append(empleado)

# === Crear DataFrame y exportar ===
df = pd.DataFrame(empleados_lista)

# Ordenar columnas si querés
columnas_orden = ["legajo", "apellido", "nombre", "cuil", "sector", "sede",
                  "fecha_nacimiento", "fecha_ingreso", "estado", "fecha_baja",
                  "motivo_baja", "antiguedad", "edad", "telefono", "rol", "notas",
                  "last_interaction_date",
                  "prestamo_fecha_prestamo", "prestamo_monto", "prestamo_cuotas",
                  "prestamo_cancelado", "prestamo_pendiente", "prestamo_proxima_cuota",
                  "prestamo_cuotas_pendientes", "prestamo_fecha_cancelacion"]
df = df[[col for col in columnas_orden if col in df.columns]]

# === Guardar como Excel ===
fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = f"empleados_exportados_{fecha}.xlsx"
df.to_excel(output_file, index=False)

print(f"✅ Nómina exportada correctamente a {output_file}")
