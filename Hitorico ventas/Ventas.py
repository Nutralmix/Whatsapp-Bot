import pandas as pd
import sqlite3
from datetime import datetime
import os

# === CONFIGURACIÓN ===
archivo_excel = r"C:\Users\SebastianAtia-Nutral\OneDrive - NUTRALMIX SRL\Planilla formulas en uso\FORMULAS ALIMENTOS Abril.xlsb"
nombre_hoja = "Lista de precios"

# === 1. Verificar archivo ===
if not os.path.exists(archivo_excel):
    print("⚠️ El archivo no existe.")
    exit()

# === 2. Leer hoja desde fila 5 (header=4), columnas B a H ===
try:
    df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja, engine="pyxlsb", header=4, usecols="B:H")

    df.columns = [
        "Nombre del producto",
        "Precio 9 de Julio",
        "Precio de lista 9dj",
        "Variacion 9dj",
        "Precio Trenque",
        "Precio de LIsta TL",
        "Variacion TL"
    ]

    # Eliminar filas vacías o de encabezado intermedio
    df = df[df["Nombre del producto"].notna()]
    df = df[~df["Nombre del producto"].astype(str).str.contains("PRODUCTO|VARIACION", case=False, na=False)]

except Exception as e:
    print("❌ Error leyendo el archivo:", e)
    exit()

# === 3. Convertir porcentajes como corresponde ===
def convertir_a_decimal(valor):
    try:
        valor = str(valor).replace(",", ".").replace("%", "").strip()
        return round(float(valor) / 100, 6)
    except:
        return None

for col in ["Variacion 9dj", "Variacion TL"]:
    if col in df.columns:
        df[col] = df[col].apply(convertir_a_decimal)

# === 4. Agregar fecha ===
df["Fecha"] = datetime.today().strftime('%Y-%m-%d')

# === 5. Guardar en base de datos ===
conn = sqlite3.connect("historial_precios.db")

try:
    df.to_sql("precios", conn, if_exists="append", index=False)
    print("✅ Datos con porcentajes corregidos guardados correctamente.")
except Exception as e:
    print("❌ Error al guardar en la base:", e)
finally:
    conn.close()
