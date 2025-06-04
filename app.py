from flask import Flask, render_template, request, redirect, url_for
import json
import os
import unicodedata
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# Normalizador

def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

# App Flask
app = Flask(__name__)

# Filtro personalizado
@app.template_filter('format_num')
def format_num(value):
    return f"{int(value):,}".replace(",", ".")

@app.route("/")
def portada():
    return render_template("portada.html")

@app.route("/panel")
def panel():
    return render_template("panel.html")

@app.route("/ver_todos")
def ver_todos():
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)
    return render_template("ver_empleados.html", empleados=empleados)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        nuevo_empleado = {
            "apellido": request.form["apellido"],
            "nombre": request.form["nombre"],
            "cuil": request.form["cuil"],
            "sector": request.form["sector"],
            "fecha_ingreso": request.form["fecha_ingreso"],
            "fecha_nacimiento": request.form["fecha_nacimiento"],
            "telefono": request.form["telefono"],
            "direccion": request.form["direccion"],
            "email": request.form["email"],
            "vacaciones": int(request.form["vacaciones"] or 0)
        }

        legajo = request.form["legajo"]

        empleados = {}
        if os.path.exists("empleados.json"):
            with open("empleados.json", "r", encoding="utf-8") as f:
                empleados = json.load(f)

        empleados[legajo] = nuevo_empleado

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)

        return redirect(url_for('ver_todos'))

    return render_template("agregar_empleado.html")

@app.route('/editar/<legajo>', methods=['GET', 'POST'])
def editar_empleado(legajo):
    print("📝 Editando legajo:", legajo)
    print("🧾 Datos recibidos:", request.form)
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    if request.method == 'POST':
        empleados[legajo] = {
            "apellido": request.form["apellido"],
            "nombre": request.form["nombre"],
            "cuil": request.form["cuil"],
            "sector": request.form["sector"],
            "fecha_ingreso": request.form["fecha_ingreso"],
            "fecha_nacimiento": request.form["fecha_nacimiento"],
            "telefono": request.form["telefono"],
            "direccion": request.form["direccion"],
            "email": request.form["email"],
            "vacaciones": int(request.form["vacaciones"] or 0)
        }

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)

        return redirect(url_for('ver_todos'))

    empleado = empleados.get(legajo)
    if not empleado:
        return f"<h2>No se encontró el empleado con legajo {legajo}</h2>"
    return render_template("editar_empleado.html", empleado=empleado, legajo=legajo)

@app.route("/eliminar/<legajo>")
def eliminar(legajo):
    empleados = {}
    if os.path.exists("empleados.json"):
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)

    if legajo in empleados:
        del empleados[legajo]
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)
        return redirect(url_for('ver_todos'))
    else:
        return f"<h2>Empleado con legajo {legajo} no encontrado</h2>"

@app.route("/info", methods=["GET", "POST"])
def info():
    empleados = {}
    resultado = None

    if os.path.exists("empleados.json"):
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)

    if request.method == "POST":
        consulta = normalizar(request.form["consulta"])
        for legajo, emp in empleados.items():
            if (consulta in normalizar(legajo) or
                consulta in normalizar(emp.get("nombre", "")) or
                consulta in normalizar(emp.get("apellido", "")) or
                consulta in normalizar(emp.get("cuil", ""))):
                resultado = {"legajo": legajo, **emp}

                # 👇 Agregar cálculo de antigüedad
                try:
                    ingreso = datetime.strptime(emp.get("fecha_ingreso", ""), "%d-%m-%Y")
                    hoy = datetime.now()
                    antiguedad = hoy.year - ingreso.year
                    if (hoy.month, hoy.day) < (ingreso.month, ingreso.day):
                        antiguedad -= 1
                    resultado["antiguedad"] = antiguedad
                except:
                    resultado["antiguedad"] = "?"

                break

    return render_template("consultar_info.html", resultado=resultado)

@app.route("/archivos/<legajo>")
def ver_archivos(legajo):
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    empleado = empleados.get(legajo)
    if not empleado:
        return f"No se encontró el empleado con legajo {legajo}"

    apellido = empleado.get("apellido", "sin_apellido").strip().replace(" ", "_")
    nombre = empleado.get("nombre", "sin_nombre").strip().replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")

    archivos = os.listdir(carpeta) if os.path.exists(carpeta) else []

    return render_template("ver_archivos.html", legajo=legajo, archivos=archivos, empleado=empleado)

@app.route("/archivos/<legajo>/subir", methods=["POST"])
def subir_archivo(legajo):
    archivo = request.files.get("archivo")
    if not archivo or archivo.filename == "":
        return "❌ No se seleccionó ningún archivo."

    if not os.path.exists("empleados.json"):
        return "❌ No se encontró la base de empleados."

    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    empleado = empleados.get(legajo)
    if not empleado:
        return f"❌ No se encontró el empleado con legajo {legajo}"

    apellido = empleado.get("apellido", "sin_apellido").strip().replace(" ", "_")
    nombre = empleado.get("nombre", "sin_nombre").strip().replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")

    os.makedirs(carpeta, exist_ok=True)

    nombre_seguro = secure_filename(archivo.filename)
    ruta_final = os.path.join(carpeta, nombre_seguro)
    archivo.save(ruta_final)

    return redirect(url_for("ver_archivos", legajo=legajo))

@app.route("/subir_archivo_a_empleado", methods=["GET", "POST"])
def elegir_empleado_para_subir_archivo():
    error = None
    if request.method == "POST":
        entrada = normalizar(request.form.get("busqueda", "").strip())

        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)

        for legajo, emp in empleados.items():
            if (
                entrada == normalizar(legajo)
                or entrada == normalizar(emp.get("cuil", ""))
                or entrada == normalizar(f"{emp.get('nombre', '')} {emp.get('apellido', '')}")
                or entrada == normalizar(f"{emp.get('apellido', '')} {emp.get('nombre', '')}")
            ):
                return redirect(url_for("ver_archivos", legajo=legajo))

        error = "❌ No se encontró ningún empleado con ese dato."

    return render_template("elegir_empleado_subir.html", error=error)

@app.route("/cumples")
def cumples():
    hoy = datetime.now()
    empleados_cumples = []
    cumples_restantes = []

    if os.path.exists("empleados.json"):
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)

        for legajo, emp in empleados.items():
            fecha_nac_str = emp.get("fecha_nacimiento", "")
            ingreso_str = emp.get("fecha_ingreso", "")

            try:
                fecha_nac = datetime.strptime(fecha_nac_str, "%d-%m-%Y")
                cumple_este_anio = fecha_nac.replace(year=hoy.year)
                edad = hoy.year - fecha_nac.year

                if cumple_este_anio < hoy:
                    continue

                dias_para_cumple = (cumple_este_anio - hoy).days

                try:
                    fecha_ingreso = datetime.strptime(ingreso_str, "%d-%m-%Y")
                    antiguedad = hoy.year - fecha_ingreso.year
                    if hoy.month < fecha_ingreso.month or (hoy.month == fecha_ingreso.month and hoy.day < fecha_ingreso.day):
                        antiguedad -= 1
                except:
                    antiguedad = "?"

                data = {
                    "legajo": legajo,
                    "nombre": emp.get("nombre", ""),
                    "apellido": emp.get("apellido", ""),
                    "fecha": cumple_este_anio.strftime("%d/%m"),
                    "edad": edad,
                    "antiguedad": antiguedad
                }

                if dias_para_cumple <= 30:
                    empleados_cumples.append(data)
                else:
                    cumples_restantes.append(data)

            except ValueError:
                continue

    empleados_cumples.sort(key=lambda x: datetime.strptime(x["fecha"], "%d/%m"))
    cumples_restantes.sort(key=lambda x: datetime.strptime(x["fecha"], "%d/%m"))

    return render_template("cumples.html", empleados=empleados_cumples, restantes=cumples_restantes)

@app.route("/logout")
def logout():
    return render_template("portada.html")

@app.route("/prestamo/<legajo>")
def ver_prestamo(legajo):
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    empleado = empleados.get(legajo)
    if not empleado:
        return f"Empleado con legajo {legajo} no encontrado."

    prestamo = empleado.get("prestamo")
    return render_template("ver_prestamo.html", empleado=empleado, prestamo=prestamo)

@app.route("/prestamos")
def ver_prestamos():
    if not os.path.exists("empleados.json"):
        return "<h2>No hay empleados cargados</h2>"

    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    empleados_con_prestamo = {
        legajo: emp for legajo, emp in empleados.items() if emp.get("prestamo")
    }

    return render_template("ver_prestamos.html", empleados=empleados_con_prestamo)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
