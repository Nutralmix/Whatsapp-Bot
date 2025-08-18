# actualizar_gastos.py
import os
import re
import json
import requests
import subprocess
import pandas as pd
from datetime import datetime

# ========= CONFIG =========
ARCHIVO_JSON  = "empleados.json"
ARCHIVO_EXCEL = "gastos.xlsx"

# Google Sheets del usuario (usa el gid que enviaste)
FILE_ID = "1RKa8eVJWwAlZXOjTpfyxe_L0v7zaAprg"
GID     = "609445557"
URL     = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx&gid={GID}"

# ========= DESCARGA =========
def descargar_excel_desde_google(url, destino):
    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Error al descargar Excel: {r.status_code}")
        raise SystemExit(1)
    with open(destino, "wb") as f:
        f.write(r.content)
    print("✅ Excel de gastos descargado.")

# ========= PARSEOS =========
def parse_importe(valor):
    """Convierte '$301.081,92' o '($7.150,24)' a float, maneja ya-numéricos."""
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    negativo = s.startswith("(") and s.endswith(")")
    s = s.replace("(", "").replace(")", "")
    # deja solo números, . , y -
    s = re.sub(r"[^0-9,.-]", "", s)
    # miles con . -> quitar; coma como decimal -> punto
    s = s.replace(".", "").replace(",", ".")
    try:
        num = float(s)
    except:
        num = 0.0
    return -num if negativo else num

def normalizar_columnas(df):
    """Devuelve el mismo DF con columnas en MAYÚSCULAS y sin espacios."""
    df = df.copy()
    df.columns = [c.strip().upper() for c in df.columns]
    return df

def col(df, *alternativas):
    """Busca la primera columna presente de una lista de alternativas."""
    cols = list(df.columns)
    for a in alternativas:
        # coincidencia exacta
        if a.upper() in df.columns:
            return a.upper()
        # por prefijo (por si el nombre quedó cortado en el Excel)
        for c in cols:
            if c.startswith(a.upper()):
                return c
    raise KeyError(f"Falta columna: {alternativas}")

# ========= AGRUPACIÓN =========
def agrupar_por_mes_y_articulo(df, legajo):
    """
    Devuelve dict:
    {
      'YYYY-MM': {
         'total_mes': float,
         'por_articulo': {
             'Combustibles': {'total': float, 'items': [ {fecha, proveedor, comprobante, leyenda, importe} ]},
             ...
         }
      },
      ...
    }
    """
    if df.empty:
        return {}

    # Columnas (robusto a variaciones)
    c_leg   = col(df, "LEGAJO", "LEG", "LEGAJ")
    c_fecha = col(df, "FECHA")
    c_prov  = col(df, "PROVEEDOR", "PROV")
    c_comp  = col(df, "COMPROBANTE", "COMPROBAN", "COMPROB")
    c_art   = col(df, "ARTICULO")
    c_ley   = col(df, "LEYENDA")
    c_imp   = col(df, "IMPORTE_GABI", "IMPORTE", "IMPORTE_GAB")

    dfl = df[df[c_leg].astype(str).str.strip() == str(legajo)].copy()
    if dfl.empty:
        return {}

    # fechas e importes
    dfl[c_fecha] = pd.to_datetime(dfl[c_fecha], dayfirst=True, errors="coerce")
    dfl = dfl.dropna(subset=[c_fecha])
    dfl["MES"] = dfl[c_fecha].dt.to_period("M").astype(str)  # '2025-07'
    dfl["IMP_NUM"] = dfl[c_imp].apply(parse_importe)

    # strings limpios
    for c in [c_prov, c_comp, c_art, c_ley]:
        dfl[c] = dfl[c].astype(str).str.strip()

    resultado = {}
    for mes, df_mes in dfl.groupby("MES"):
        total_mes = float(df_mes["IMP_NUM"].sum())
        por_art = {}
        for art, df_art in df_mes.groupby(c_art):
            total_art = float(df_art["IMP_NUM"].sum())
            items = (
                df_art.sort_values(c_fecha)[[c_fecha, c_prov, c_comp, c_ley, "IMP_NUM"]]
                      .rename(columns={
                          c_fecha: "fecha",
                          c_prov:  "proveedor",
                          c_comp:  "comprobante",
                          c_ley:   "leyenda",
                          "IMP_NUM":"importe"
                      })
            )
            # formato de fecha amigable
            items["fecha"] = items["fecha"].dt.strftime("%Y-%m-%d")
            por_art[art] = {
                "total": total_art,
                "items": items.to_dict(orient="records")
            }
        resultado[mes] = {
            "total_mes": total_mes,
            "por_articulo": por_art
        }
    return resultado

# ========= MAIN =========
def main():
    # 1) Descargar
    descargar_excel_desde_google(URL, ARCHIVO_EXCEL)

    # 2) Cargar empleados
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        empleados = json.load(f)

    # 3) Leer Excel
    df = pd.read_excel(ARCHIVO_EXCEL, sheet_name=0)
    print("🧩 Columnas encontradas en el Excel:", df.columns.tolist())
    df = normalizar_columnas(df)

    # 4) Limpiar campo previo y recalcular
    for legajo, emp in empleados.items():
        emp["gastos_agrupados"] = {}

    # 5) Calcular agrupación por legajo
    for legajo in list(empleados.keys()):
        agrupado = agrupar_por_mes_y_articulo(df, legajo)
        empleados[legajo]["gastos_agrupados"] = agrupado

    # 6) Guardar JSON
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(empleados, f, ensure_ascii=False, indent=4)

    print("✅ Gastos agrupados actualizados en empleados.json")

    # 7) Push automático (como tus otros scripts)
    res = subprocess.run("python git_push.py", shell=True)
    print("🔧 git_push.py ->", res.returncode)

if __name__ == "__main__":
    main()
