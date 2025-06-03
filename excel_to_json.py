import pandas as pd
import json
from datetime import datetime

# === ARCHIVOS DE ENTRADA ===
ARCHIVO_LEGAJOS = "C:/Programas Pyt/Bot RRHH/Legajos y Prestamos/legajos para prueba.xlsx"
ARCHIVO_PRESTAMOS = "C:/Programas Pyt/Bot RRHH/Legajos y Prestamos/Planilla PRESTAMOS AGUS.xlsx"

# === LEER EXCEL DE LEGAJOS ===
df_legajos = pd.read_excel(ARCHIVO_LEGAJOS, sheet_name=0)
print(df_legajos.columns)
df_prestamos = pd.read_excel(ARCHIVO_PRESTAMOS, sheet_name=0)
print(df_prestamos.columns)

# Normalizamos nombres de columnas (por las dudas)
df_legajos.columns = df_legajos.columns.str.strip()
df_prestamos.columns = df_prestamos.columns.str.strip()

# --- TRANSFORMAR A JSON ---
empleados = {}

for _, row in df_legajos.iterrows():
    legajo = str(row["Legajo"]).strip()
    nombre = f"{row['Nombre']} {row['Apellido']}",

    empleado = {
        "legajo": legajo,
        "cuil": str(row["CUIL"]),
        "apellido": str(row["Apellido"]),
        "nombre": str(row["Nombre"]),
        "sector": str(row["Area"]),
        "sede": str(row["Sede"]),
        "fecha_ingreso": row["Fecha Ingreso"].strftime("%d-%m-%Y") if not pd.isna(row["Fecha Ingreso"]) else "",
        "estado": str(row["Estado"]),
        "fecha_baja": row["Fecha de desvinculación"].strftime("%d-%m-%Y") if not pd.isna(row["Fecha de desvinculación"]) else "",
        "motivo_baja": str(row["Motivo de Baja"]) if not pd.isna(row["Motivo de Baja"]) else "",
        "fecha_nacimiento": row["Fecha de nacimiento"].strftime("%d-%m-%Y") if not pd.isna(row["Fecha de nacimiento"]) else "",
        "antiguedad": str(row.get("Antiguedad", "")),
        "edad": int(row.get("Edad", 0)),
        "telefono": "",
        "rol": "empleado",
        "notas": "",
        "prestamo": {}  # Lo llenamos más abajo si existe
    }

    empleados[legajo] = empleado

# --- CRUZAR CON PRÉSTAMOS ---
for _, row in df_prestamos.iterrows():
    legajo = str(row["Legajo"]).strip()
    if legajo in empleados:
        empleados[legajo]["prestamo"] = {
            "fecha_prestamo": row["Fecha Pedido"].strftime("%d-%m-%Y") if not pd.isna(row["Fecha Pedido"]) else "",
            "monto": float(row["Monto Pedido"]),
            "cuotas": int(row["Cantidad de cuotas"]),
            "cancelado": float(row["Cancelado"]),
            "pendiente": float(row["Pendiente"]),
            "proxima_cuota": float(row["Proxima Cuota"]),
            "cuotas_pendientes": int(row["Cant Cuotas Pendientes"]),
            "fecha_cancelacion": row["Fecha cancelacion"].strftime("%d-%m-%Y") if not pd.isna(row["Fecha cancelacion"]) else ""
        }

# --- GUARDAR EN JSON ---
with open("empleados.json", "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ empleados.json generado correctamente.")
