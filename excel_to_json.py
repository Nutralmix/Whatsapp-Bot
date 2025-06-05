import pandas as pd
import json
from datetime import datetime

# === ARCHIVOS DE ENTRADA ===
ARCHIVO_LEGAJOS = "C:/Programas Pyt/Bot RRHH/Legajos y Prestamos/legajos para prueba.xlsx"
ARCHIVO_PRESTAMOS = "C:/Programas Pyt/Bot RRHH/Legajos y Prestamos/Planilla PRESTAMOS AGUS.xlsx"

# === LEER EXCEL ===
df_legajos = pd.read_excel(ARCHIVO_LEGAJOS)
df_prestamos = pd.read_excel(ARCHIVO_PRESTAMOS)

df_legajos.columns = df_legajos.columns.str.strip()
df_prestamos.columns = df_prestamos.columns.str.strip()

empleados = {}

for _, row in df_legajos.iterrows():
    estado = str(row.get("Estado", "")).strip().lower()
    if estado != "activo":
        continue  # Salteamos empleados dados de baja

    legajo = str(row["Legajo"]).strip()

    # Calcular antigüedad
    fecha_ingreso = row.get("Fecha Ingreso")
    if pd.notna(fecha_ingreso):
        hoy = datetime.now()
        antiguedad_años = hoy.year - fecha_ingreso.year - ((hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day))
        antiguedad = f"{antiguedad_años} años"
    else:
        antiguedad = ""

    empleado = {
        "legajo": legajo,
        "cuil": str(row.get("CUIL", "")),
        "apellido": str(row.get("Apellido", "")).strip(),
        "nombre": str(row.get("Nombre", "")).strip(),
        "sector": str(row.get("Area", "")).strip(),
        "sede": str(row.get("Sede", "")).strip(),
        "fecha_ingreso": fecha_ingreso.strftime("%d-%m-%Y") if pd.notna(fecha_ingreso) else "",
        "estado": estado.capitalize(),
        "fecha_baja": row["Fecha de desvinculación"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha de desvinculación")) else "",
        "motivo_baja": str(row.get("Motivo de Baja", "")) if pd.notna(row.get("Motivo de Baja")) else "",
        "fecha_nacimiento": row["Fecha de nacimiento"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha de nacimiento")) else "",
        "antiguedad": antiguedad,
        "edad": int(row.get("Edad", 0)) if not pd.isna(row.get("Edad")) else 0,
        "telefono": "",
        "rol": "empleado",
        "notas": "",
        "prestamo": {}
    }

    empleados[legajo] = empleado

# --- CRUZAR CON PRÉSTAMOS ---
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

# --- GUARDAR EN JSON ---
with open("empleados.json", "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ empleados.json generado correctamente.")
