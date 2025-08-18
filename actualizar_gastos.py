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

# Google Sheets del usuario
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
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    negativo = s.startswith("(") and s.endswith(")")
    s = s.replace("(", "").replace(")", "")
    s = re.sub(r"[^0-9,.-]", "", s)
    s = s.replace(".", "").replace(",", ".")
    try:
        num = float(s)
    except:
        num = 0.0
    return -num if negativo else num

def normalizar_columnas(df):
    df = df.copy()
    df.columns = [c.strip().upper() for c in df.columns]
    return df

def col(df, *alternativas):
    columnas = {c.lower(): c for c in df.columns}
    for alt in alternativas:
        alt_lower = alt.lower()
        if alt_lower in columnas:
            return columnas[alt_lower]
    raise KeyError(f"Falta columna: {alternativas}")

# ========= DETECCIÓN DE ENCABEZADO CORRECTO =========
def cargar_df_gastos(ruta_xlsx: str) -> pd.DataFrame:
    xls = pd.ExcelFile(ruta_xlsx)
    for sheet in xls.sheet_names:
        raw = pd.read_excel(ruta_xlsx, sheet_name=sheet, header=None)
        for i, row in raw.iterrows():
            lower = [str(v).strip().lower() for v in row.values]
            if "legajo" in lower and ("fecha" in lower or "proveedor" in lower):
                df = pd.read_excel(ruta_xlsx, sheet_name=sheet, header=i)
                return df
    return pd.read_excel(ruta_xlsx, sheet_name=0)

# ========= AGRUPACIÓN =========
def agrupar_por_mes_y_articulo(df, legajo):
    if df.empty:
        return {}

    c_leg   = col(df, "LEGAJO", "LEG", "LEGAJ")
    c_fecha = col(df, "FECHA")
    c_prov  = col(df, "PROVEEDOR", "PROV")
    c_comp  = col(df, "COMPROBANTE", "COMPROBAN", "COMPROB")
    c_art   = col(df, "ARTICULO")
    c_ley   = col(df, "LEYENDA")
    c_imp   = col(df, "IMPORTE_GABI", "IMPORTE", "IMPORTE_GAB")

    df[c_leg] = df[c_leg].astype(str).str.strip()
    legajo_str = str(legajo).strip()
    dfl = df[df[c_leg] == legajo_str].copy()

    if dfl.empty:
         print(f"🔎 No se encontraron filas para legajo {legajo_str} (columna usada: {c_leg})")


    dfl[c_fecha] = pd.to_datetime(dfl[c_fecha], dayfirst=True, errors="coerce")
    dfl = dfl.dropna(subset=[c_fecha])
    dfl["MES"] = dfl[c_fecha].dt.to_period("M").astype(str)
    dfl["IMP_NUM"] = dfl[c_imp].apply(parse_importe)

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
    descargar_excel_desde_google(URL, ARCHIVO_EXCEL)

    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        empleados = json.load(f)

    df = cargar_df_gastos(ARCHIVO_EXCEL)
    df = normalizar_columnas(df)

    for legajo, emp in empleados.items():
        emp["gastos_agrupados"] = {}

    # 5) Calcular agrupación por legajo
    for legajo in list(empleados.keys()):
        agrupado = agrupar_por_mes_y_articulo(df, legajo)

        if agrupado:
            print(f"✅ Gastos encontrados para legajo {legajo}: {len(agrupado)} mes(es)")
        else:
            print(f"⚠️ SIN gastos para legajo {legajo}")

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
