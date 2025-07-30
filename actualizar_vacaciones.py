import pandas as pd
import json
import os
import requests
import subprocess

# === CONFIGURACIÓN ===
ARCHIVO_JSON = "C:/Programas Pyt/Bot_RRHH/empleados.json"
ARCHIVO_EXCEL = "vacaciones.xlsx"

FILE_ID = "14tl_3tukdjrQigtartUbIOrAMvaBUo3f"
URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === DESCARGAR ARCHIVO DESDE GOOGLE SHEETS ===
def descargar_excel_desde_google(url, destino):
    response = requests.get(url)
    if response.status_code == 200:
        with open(destino, "wb") as f:
            f.write(response.content)
        print("✅ Excel de vacaciones descargado correctamente.")
    else:
        print(f"❌ Error al descargar el archivo: {response.status_code}")
        exit(1)

descargar_excel_desde_google(URL, ARCHIVO_EXCEL)

# === LEER JSON EXISTENTE ===
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# === LEER HOJA DE EXCEL DESCARGADA ===
df = pd.read_excel(ARCHIVO_EXCEL, sheet_name="Resumen para BOT")
df.columns = df.columns.str.strip()

# === ACTUALIZAR VACACIONES ===
for _, row in df.iterrows():
    if pd.isna(row["Legajo"]):
        continue

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

# === EJECUTAR PUSH A GIT ===
subprocess.run("python git_push.py", shell=True)
