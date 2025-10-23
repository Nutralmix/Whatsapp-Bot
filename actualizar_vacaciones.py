import pandas as pd
import json
import os
import requests
import shutil
import time
import re
import subprocess
import sys

# === CONFIGURACIÓN (unificar rutas con el resto de tus scripts) ===
ARCHIVO_JSON = "empleados.json"
ARCHIVO_EXCEL = "vacaciones.xlsx"

FILE_ID = "14tl_3tukdjrQigtartUbIOrAMvaBUo3f"
URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# === Utilidades ===
def descargar_excel_desde_google(url: str, destino: str) -> None:
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Error al descargar el archivo: {r.status_code}")
    with open(destino, "wb") as f:
        f.write(r.content)
    print("✅ Excel de vacaciones descargado correctamente.")

def backup_json(path_json: str) -> str:
    ts = int(time.time())
    bak = f"{path_json}.bak.{ts}"
    shutil.copyfile(path_json, bak)
    print(f"🧷 Backup creado: {bak}")
    return bak

def mapear_legajo_a_clave(raw_legajo: str, claves_json) -> str | None:
    """
    Empareja por dígitos sin destruir ceros a la izquierda de la clave real.
    Si raw_legajo = '0264', '264', '264-TR' -> matchea la clave '0264' o '264' según exista.
    """
    if raw_legajo is None:
        return None
    s = str(raw_legajo).strip()
    if not s or s.lower() == "nan":
        return None
    target = re.sub(r"\D", "", s)
    if not target:
        return None
    for k in claves_json:
        if re.sub(r"\D", "", k) == target:
            return k
    return None

def to_int_safe(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

# === Flujo ===
# 1) Descargar Excel
descargar_excel_desde_google(URL, ARCHIVO_EXCEL)

# 2) Leer JSON existente
with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
    empleados = json.load(f)

# 3) Backup antes de tocar nada
backup_json(ARCHIVO_JSON)

# 4) Leer hoja
df = pd.read_excel(ARCHIVO_EXCEL, sheet_name="Resumen para BOT")
df.columns = df.columns.str.strip()
print(f"🔍 Filas encontradas en hoja de vacaciones: {len(df)}")
print(f"🔍 Columnas: {df.columns.tolist()}")

# 5) Determinar posibles nombres de columna para legajo
posibles_cols_legajo = [c for c in df.columns if c.lower() in ("legajo", "leg", "leg.")]
if not posibles_cols_legajo:
    raise RuntimeError("No se encontró columna de legajo (esperado: 'Legajo', 'Leg' o similar).")
col_legajo = posibles_cols_legajo[0]

# 6) Actualizar SOLO 'vacaciones' in-place (sin tocar otros campos)
claves = set(empleados.keys())
actualizados, no_encontrados = 0, 0

for _, row in df.iterrows():
    raw_leg = row.get(col_legajo)
    if pd.isna(raw_leg):
        continue

    clave = mapear_legajo_a_clave(raw_leg, claves)
    if not clave:
        no_encontrados += 1
        print(f"⚠️ Legajo '{raw_leg}' no encontrado en JSON; no se actualiza.")
        continue

    dias = to_int_safe(row.get("Dias Disponibles", 0), default=0)

    # Aseguramos que la entrada sea un dict y no tocamos nada más
    emp = empleados.get(clave, {})
    if not isinstance(emp, dict):
        # Entrada inesperada; no la sobreescribimos para no perder datos
        print(f"❗ Entrada no dict para clave {clave}; se omite por seguridad.")
        continue

    emp["vacaciones"] = dias
    empleados[clave] = emp
    actualizados += 1
    print(f"✅ Vacaciones actualizadas para legajo {clave}: {dias} días")

print(f"📊 Resumen: {actualizados} actualizados, {no_encontrados} legajos no encontrados.")

# 7) Guardar cambios (sin filtrar ni rearmar el diccionario)
with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(empleados, f, indent=4, ensure_ascii=False)

print("✅ Actualización de vacaciones completada")
print("📄 JSON guardado en:", os.path.abspath(ARCHIVO_JSON))

# 8) Push a git (si falla, no impide la actualización)
try:
    print("🚀 Ejecutando git_push.py...")
    res = subprocess.run([sys.executable, "git_push.py"], cwd=os.path.dirname(__file__), shell=True)
    print("🔧 git_push.py ->", res.returncode)
except Exception as e:
    print(f"❌ Error al ejecutar git_push.py: {e}")
