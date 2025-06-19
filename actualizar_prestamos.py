import pandas as pd
import json
from datetime import datetime

# === RUTAS ===
ARCHIVO_PRESTAMOS = "C:/Programas Pyt/Bot RRHH/Legajos y Prestamos/Planilla PRESTAMOS AGUS.xlsx"
ARCHIVO_JSON = "empleados.json"

# === CARGAR JSON EXISTENTE ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === LEER PLANILLA DE PRÉSTAMOS ===
df_prestamos = pd.read_excel(r"C:\Programas Pyt\Bot_RRHH\Legajos y Prestamos\Planilla PRESTAMOS AGUS.xlsx")
df_prestamos.columns = df_prestamos.columns.str.strip()

# === ACTUALIZAR PRÉSTAMOS EN JSON ===
for _, row in df_prestamos.iterrows():
    legajo = str(row.get("Legajo", "")).strip()
    if legajo in empleados:
        empleados[legajo]["prestamo"] = {
            "fecha_prestamo": row["Fecha Pedido"].strftime("%d-%m-%Y") if pd.notna(row["Fecha Pedido"]) else "",
            "monto": float(row.get("Monto Pedido", 0)),
            "cuotas": int(row.get("Cantidad de cuotas", 0)),
            "cancelado": float(row.get("Cancelado", 0)),
            "pendiente": float(row.get("Pendiente", 0)),
            "proxima_cuota": float(row.get("Proxima Cuota", 0)),
            "cuotas_pendientes": int(row.get("Cant Cuotas Pendientes", 0)),
            "fecha_cancelacion": row["Fecha cancelacion"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha cancelacion")) else ""
        }
        print(f"✅ Actualizado préstamo para legajo {legajo}")
    else:
        print(f"⚠️ Legajo {legajo} no encontrado en empleados.json")

# === GUARDAR CAMBIOS ===
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de préstamos finalizada.")
