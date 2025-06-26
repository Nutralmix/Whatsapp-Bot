import pandas as pd
import json
from datetime import datetime

# === ARCHIVOS DE ENTRADA ===
ARCHIVO_LEGAJOS = "C:/Programas Pyt/Bot_RRHH/Legajos y Prestamos/legajos para prueba.xlsx"

# === LEER EXCEL con Teléfono como texto ===
df_legajos = pd.read_excel(ARCHIVO_LEGAJOS, dtype={"Telefono": str})
df_legajos.columns = df_legajos.columns.str.strip()

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
        "edad": int(row.get("Edad", 0)) if not pd.isna(row.get("Edad")) else 0,
        "telefono": str(row.get("Telefono", "")).strip(),
        "rol": "empleado",
        "notas": "",
        "prestamo": {}
    }

    empleados[legajo] = empleado
    print(f"📞 Legajo {legajo} - Teléfono: {empleado['telefono']}")

# --- GUARDAR EN JSON ---
with open("empleados.json", "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ empleados.json generado correctamente.")
