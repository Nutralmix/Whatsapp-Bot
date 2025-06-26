import pandas as pd
import json
from datetime import datetime

# === RUTAS ===
ARCHIVO_JSON = "empleados.json"

# === LINK DE GOOGLE DRIVE (formato Excel) ===
FILE_ID = "16wSPIFXfitC4hh7n6GOJnhx3OiLHZq5n"  # Reemplazalo con el tuyo si cambia
url = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === CARGAR JSON EXISTENTE ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === LEER PLANILLA DE PRÉSTAMOS DESDE GOOGLE DRIVE ===
df_prestamos = pd.read_excel(url, sheet_name="Resumen para BOT")
df_prestamos.columns = df_prestamos.columns.str.strip()

# === ACTUALIZAR PRÉSTAMOS EN JSON ===
for _, row in df_prestamos.iterrows():
    legajo_raw = row.get("Leg", "")  # << Cambiado de 'Legajo' a 'Leg'
    legajo = str(legajo_raw).strip().lstrip("0")

    if legajo in empleados:
        empleados[legajo]["prestamo"] = {
            "fecha_prestamo": row["Fecha de Pedido"].strftime("%d-%m-%Y") if pd.notna(row["Fecha de Pedido"]) else "",
            "monto": float(row.get("Monto Pedido", 0)),
            "cuotas": int(row.get("Cantidad de cuotas", 0)),
            "cancelado": float(row.get("Cancelado", 0)),
            "pendiente": float(row.get("Pendiente", 0)),
            "proxima_cuota": float(row.get("Proxima Cuota", 0)),
            "cuotas_pendientes": int(row.get("Cant Cuotas Pendientes", 0)),
            "fecha_cancelacion": row["Fecha Cancelacion"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha Cancelacion")) else ""
        }
        print(f"✅ Actualizado préstamo para legajo {legajo}")
    else:
        print(f"⚠️ Legajo {legajo} no encontrado en empleados.json")

# === GUARDAR CAMBIOS ===
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de préstamos finalizada.")

import subprocess
subprocess.run("python git_push.py", shell=True)

