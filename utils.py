import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

def cargar_empleados_activos():
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)
    return {
        legajo: datos for legajo, datos in empleados.items()
        if datos.get("estado") == "Activo"
    }

def calcular_antiguedad(fecha_ingreso_str):
    try:
        fecha_ingreso = datetime.strptime(fecha_ingreso_str, "%d-%m-%Y")
        hoy = datetime.now()
        diferencia = relativedelta(hoy, fecha_ingreso)
        return f"{diferencia.years} años y {diferencia.months} meses"
    except:
        return "?"


import requests
from datetime import datetime
from bs4 import BeautifulSoup

def obtener_proximos_feriados():
    url = "https://www.argentina.gob.ar/interior/feriados-nacionales-2025"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        # Suponiendo que los feriados están en <h3> de mes y <li> fechas:
        items = soup.select("h3 ~ ul li")
        feriados = [li.get_text(strip=True) for li in items]
    except Exception as e:
        return f"❌ No pude obtener los feriados: {e}"

    hoy = datetime.now()
    proximos = []
    for f in feriados:
        # cada f es tipo "3 de marzo: Carnaval" — parse simple
        try:
            dia_str = f.split(" ")[0]
            mes_str = f.split(" ")[2]  # "marzo" etc.
            fecha = datetime.strptime(f"{dia_str}-{mes_str}-{hoy.year}", "%d-%B-%Y")
            if fecha >= hoy:
                proximos.append(f)
        except:
            continue

    if not proximos:
        return "✅ No quedan feriados en lo que resta del año."

    texto = "✅ Próximos feriados:\n"
    for f in proximos[:5]:  # solo los primeros 5
        texto += f"- {f}\n"
    return texto
