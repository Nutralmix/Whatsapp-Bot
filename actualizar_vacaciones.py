import pandas as pd
import json
import os

# === CONFIGURACIÓN ===
ARCHIVO_JSON = "C:/Programas Pyt/Bot_RRHH/empleados.json"
FILE_ID = "14tl_3tukdjrQigtartUbIOrAMvaBUo3f"  # ID de Google Sheets
url = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === LEER JSON EXISTENTE ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === LEER HOJA DE EXCEL DESDE GOOGLE SHEETS ===
df = pd.read_excel(url, sheet_name="Resumen para BOT")
df.columns = df.columns.str.strip()

# === ACTUALIZAR VACACIONES ===
for _, row in df.iterrows():
    if pd.isna(row["Legajo"]):
        continue  # Evita error si hay filas vacías

    legajo = str(int(row["Legajo"])).strip()
    dias = row.get("Dias Disponibles", 0)

    try:
        dias = int(dias)
    except:
        dias = 0

    if legajo in empleados:
        empleados[legajo]["vacaciones"] = dias
        print(f"✅ Vacaciones actualizadas para legajo {legajo}: {dias} días")
    else:
        print(f"⚠️ Legajo {legajo} no encontrado")

# === GUARDAR CAMBIOS EN EL JSON ===
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de vacaciones completada")
print("📄 JSON guardado en:", os.path.abspath(ARCHIVO_JSON))

import subprocess
subprocess.run("python git_push.py", shell=True)

