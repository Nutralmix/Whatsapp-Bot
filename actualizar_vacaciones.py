import pandas as pd
import json

# === CONFIGURACIÓN ===
ARCHIVO_JSON = "empleados.json"
FILE_ID = "14tl_3tukdjrQigtartUbIOrAMvaBUo3f"  # reemplazá por tu ID real
url = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === LEER JSON ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === LEER HOJA DE EXCEL ===
df = pd.read_excel(url, sheet_name="Resumen para BOT")
df.columns = df.columns.str.strip()

# === ACTUALIZAR VACACIONES ===
for _, row in df.iterrows():
    legajo = str(int(row["Legajo"])).strip()  # chequeá que sea entero
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

# === GUARDAR JSON ACTUALIZADO ===
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de vacaciones completada")
