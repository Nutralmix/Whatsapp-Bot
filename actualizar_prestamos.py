import pandas as pd
import json
from datetime import datetime

# === RUTAS ===
ARCHIVO_JSON = "empleados.json"


# === LINK DE GOOGLE DRIVE (formato Excel) ===
FILE_ID = "16wSPIFXfitC4hh7n6GOJnhx3OiLHZq5n"  # Reemplazalo con el tuyo si cambia
url = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === CARGA JSON ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === CARGA EXCEL ===
df = pd.read_excel(url, sheet_name=0)
df.columns = df.columns.str.strip()

legajos_con_prestamo = set()

# === ACTUALIZA PRÉSTAMOS ===
for _, row in df.iterrows():
    legajo = str(int(row.get("Leg", 0))).strip()
    if legajo in empleados:
        empleados[legajo]["prestamo"] = {
            "fecha_prestamo": row["Fecha Pedido"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha Pedido")) else "",
            "monto": float(row.get("Monto Pedido", 0)),
            "cuotas": int(row.get("Cantidad de cuotas", 0)),
            "cancelado": float(row.get("Cancelado", 0)),
            "pendiente": float(row.get("Pendiente", 0)),
            "proxima_cuota": float(row.get("Proxima Cuota", 0)),
            "cuotas_pendientes": int(row.get("Cant Cuotas Pendientes", 0)),
            "fecha_cancelacion": row["Fecha cancelacion"].strftime("%d-%m-%Y") if pd.notna(row.get("Fecha cancelacion")) else ""
        }
        legajos_con_prestamo.add(legajo)
        print(f"✅ Prestamo actualizado para legajo {legajo}")
    else:
        print(f"⚠️ Legajo {legajo} no encontrado")

# === BORRAR PRÉSTAMOS ANTIGUOS ===
for legajo, e in empleados.items():
    if legajo not in legajos_con_prestamo:
        if "prestamo" in e and e["prestamo"]:
            e["prestamo"] = {}
            print(f"🧹 Prestamo eliminado para legajo {legajo}")

# === GUARDAR JSON ACTUALIZADO ===
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de préstamos completada.")
