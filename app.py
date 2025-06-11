from flask import Flask, render_template, request, redirect, url_for
import json
import os
import unicodedata
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from auto_git_push import auto_push_archivos


# ---------------------------
# Función para normalizar texto
# ---------------------------
def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

# ---------------------------
# Logging simple
# ---------------------------
def log_debug(mensaje):
    with open("logs_app.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")
        
def registrar_log_simple(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("bot_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensaje}\n")        

# ---------------------------
# Cargar solo empleados activos
# ---------------------------
def cargar_empleados_activos():
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
        log_debug("Empleados activos cargados correctamente")
        return {
            legajo: datos for legajo, datos in empleados.items()
            if datos.get("estado", "").lower() == "activo"
        }
    except Exception as e:
        log_debug(f"Error al cargar empleados activos: {e}")
        return {}

# ---------------------------
# Configuración de Flask
# ---------------------------
app = Flask(__name__, static_url_path='/static', static_folder='static')

# ---------------------------
# Filtro para formatear números
# ---------------------------
@app.template_filter('format_num')
def format_num(value):
    return f"{int(value):,}".replace(",", ".")

# ---------------------------
# Rutas
# ---------------------------

@app.route("/")
def portada():
    log_debug("Acceso a portada")
    return render_template("portada.html")

@app.route("/panel")
def panel():
    log_debug("Acceso a panel")
    return render_template("panel.html")

@app.route("/ver_todos")
def ver_todos():
    empleados = cargar_empleados_activos()
    log_debug("Visualización de todos los empleados")
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
            "vacaciones": int(request.form["vacaciones"] or 0),
            "estado": "Activo"
        }
        legajo = request.form["legajo"]

        empleados = {}
        if os.path.exists("empleados.json"):
            with open("empleados.json", "r", encoding="utf-8") as f:
                empleados = json.load(f)

        empleados[legajo] = nuevo_empleado

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)

        log_debug(f"Nuevo empleado agregado: {legajo} - {nuevo_empleado['nombre']}")
        return redirect(url_for('ver_todos'))

    return render_template("agregar_empleado.html")

@app.route('/editar/<legajo>', methods=['GET', 'POST'])
def editar_empleado(legajo):
    log_debug(f"Entrando a editar empleado {legajo}")
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
            "vacaciones": int(request.form["vacaciones"] or 0),
            "estado": request.form.get("estado", "Activo")
        }

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)

        log_debug(f"Empleado {legajo} actualizado")
        return redirect(url_for('ver_todos'))

    empleado = empleados.get(legajo)
    if not empleado:
        log_debug(f"No se encontró el empleado {legajo}")
        return f"<h2>No se encontró el empleado con legajo {legajo}</h2>"

    return render_template("editar_empleado.html", empleado=empleado, legajo=legajo)

@app.route("/eliminar/<legajo>")
def eliminar(legajo):
    log_debug(f"Eliminando empleado {legajo}")
    empleados = {}
    if os.path.exists("empleados.json"):
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)

    if legajo in empleados:
        del empleados[legajo]
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=4)
        log_debug(f"Empleado {legajo} eliminado")
        return redirect(url_for('ver_todos'))
    else:
        log_debug(f"Intento fallido de eliminar legajo {legajo}")
        return f"<h2>Empleado con legajo {legajo} no encontrado</h2>"

@app.route("/info", methods=["GET", "POST"])
def info():
    log_debug("Consulta de info iniciada")
    empleados = cargar_empleados_activos()
    resultado = None
    resultados = []

    if request.method == "POST":
        consulta = normalizar(request.form["consulta"])
        log_debug(f"Búsqueda de: {consulta}")
        for legajo, emp in empleados.items():
            if (consulta in normalizar(legajo) or
                consulta in normalizar(emp.get("nombre", "")) or
                consulta in normalizar(emp.get("apellido", "")) or
                consulta in normalizar(emp.get("cuil", ""))):
                resultados.append({"legajo": legajo, **emp})

        if len(resultados) == 1:
            resultado = resultados[0]
            try:
                from dateutil.relativedelta import relativedelta
                hoy = datetime.now()
                ingreso_str = resultado.get("fecha_ingreso", "")
                fecha_ingreso = datetime.strptime(ingreso_str, "%d-%m-%Y")
                diferencia = relativedelta(hoy, fecha_ingreso)
                resultado["antiguedad"] = f"{diferencia.years} años y {diferencia.months} meses"
            except:
                resultado["antiguedad"] = "?"
        else:
            resultado = None

    return render_template("consultar_info.html", resultado=resultado, resultados=resultados)

@app.route("/cumples")
def cumples():
    hoy = datetime.now()
    empleados_cumples = []
    cumples_restantes = []

    empleados = cargar_empleados_activos()
    log_debug("Consulta de próximos cumpleaños")

    for legajo, emp in empleados.items():
        fecha_nac_str = emp.get("fecha_nacimiento", "")
        ingreso_str = emp.get("fecha_ingreso", "")

        try:
            fecha_nac = datetime.strptime(fecha_nac_str, "%d-%m-%Y")
            cumple_este_anio = fecha_nac.replace(year=hoy.year)
            edad = hoy.year - fecha_nac.year

            # Si ya pasó el cumpleaños este año, usar el del año siguiente
            if cumple_este_anio < hoy:
                cumple_este_anio = fecha_nac.replace(year=hoy.year + 1)
                edad += 1

            dias_para_cumple = (cumple_este_anio - hoy).days

            try:
                fecha_ingreso = datetime.strptime(ingreso_str, "%d-%m-%Y")
                antiguedad = hoy.year - fecha_ingreso.year
                if hoy.month < fecha_ingreso.month or (hoy.month == fecha_ingreso.month and hoy.day < fecha_ingreso.day):
                    antiguedad -= 1
            except:
                antiguedad = "?"

            # Agregar mensaje especial según la cercanía
            if dias_para_cumple == 0:
                mensaje_extra = "🎉 ¡Cumple HOY!"
            elif dias_para_cumple == 1:
                mensaje_extra = "🎈 Cumple mañana"
            else:
                mensaje_extra = ""

            data = {
                "legajo": legajo,
                "nombre": emp.get("nombre", ""),
                "apellido": emp.get("apellido", ""),
                "fecha": cumple_este_anio.strftime("%d/%m"),
                "edad": edad,
                "antiguedad": antiguedad,
                "mensaje_extra": mensaje_extra
            }

            if dias_para_cumple <= 30:
                empleados_cumples.append(data)
            else:
                cumples_restantes.append(data)

        except ValueError:
            log_debug(f"Fecha de nacimiento inválida para {emp.get('nombre', legajo)}")
            continue

    empleados_cumples.sort(key=lambda x: datetime.strptime(x["fecha"], "%d/%m"))
    cumples_restantes.sort(key=lambda x: datetime.strptime(x["fecha"], "%d/%m"))

    return render_template("cumples.html", empleados=empleados_cumples, restantes=cumples_restantes)

@app.route("/logout")
def logout():
    log_debug("Logout desde panel web")
    return render_template("portada.html")

@app.route("/prestamo/<legajo>")
def ver_prestamo(legajo):
    log_debug(f"Consulta de préstamo para {legajo}")
    with open("empleados.json", "r", encoding="utf-8") as f:
        empleados = json.load(f)

    empleado = empleados.get(legajo)
    if not empleado:
        log_debug(f"No se encontró empleado con legajo {legajo} para ver préstamo")
        return f"Empleado con legajo {legajo} no encontrado."

    prestamo = empleado.get("prestamo")
    return render_template("ver_prestamo.html", empleado=empleado, prestamo=prestamo)

@app.route("/prestamos")
def ver_prestamos():
    log_debug("Consulta de todos los préstamos")
    empleados = cargar_empleados_activos()

    empleados_con_prestamo = {
        legajo: emp for legajo, emp in empleados.items() if emp.get("prestamo")
    }

    return render_template("ver_prestamos.html", empleados=empleados_con_prestamo)

@app.route("/exportar_excel")
def exportar_excel():
    import pandas as pd

    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
    except Exception as e:
        return f"❌ Error al leer empleados.json: {e}"

    empleados_lista = []
    for legajo, datos in empleados.items():
        fila = {"legajo": legajo}
        fila.update(datos)

        if isinstance(fila.get("prestamo"), dict):
            for k, v in fila["prestamo"].items():
                fila[f"prestamo_{k}"] = v
            del fila["prestamo"]

        empleados_lista.append(fila)

    df = pd.DataFrame(empleados_lista)
    output_path = os.path.join("static", "exportados", "empleados_exportados.xlsx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_excel(output_path, index=False)

    registrar_log_simple("🔄 Exportación de empleados a Excel realizada desde el panel web.")
    return redirect("/static/exportados/empleados_exportados.xlsx")

@app.route('/subir_archivo_empleado', methods=['GET', 'POST'])
def subir_archivo_empleado():
    log_debug("Acceso a subir archivo a empleado (privado)")
    mensaje = ""
    resultado = None

    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
    except:
        empleados = {}

    if request.method == 'POST':
        if 'consulta' in request.form:
            consulta = normalizar(request.form['consulta'])

            for legajo, emp in empleados.items():
                if (consulta in normalizar(legajo) or
                    consulta in normalizar(emp.get("nombre", "")) or
                    consulta in normalizar(emp.get("apellido", "")) or
                    consulta in normalizar(emp.get("cuil", ""))):
                    resultado = {"legajo": legajo, **emp}
                    break

            if not resultado:
                mensaje = "❌ No se encontró ningún empleado con ese dato."
                log_debug(mensaje)

        elif 'archivo' in request.files and 'legajo' in request.form:
            legajo = request.form.get("legajo")
            archivo = request.files.get("archivo")

            if not legajo or not archivo:
                mensaje = "❌ Faltan datos: legajo o archivo."
                log_debug(mensaje)
            else:
                emp = empleados.get(legajo)
                if not emp:
                    mensaje = "❌ Legajo no válido."
                else:
                    # Carpeta: static/archivos/Apellido_Nombre
                    nombre = emp.get("nombre", "nombre")
                    apellido = emp.get("apellido", "apellido")
                    carpeta_nombre = f"{apellido}_{nombre}".replace(" ", "_")
                    carpeta_destino = os.path.join("static", "archivos", carpeta_nombre)
                    os.makedirs(carpeta_destino, exist_ok=True)

                    filename = secure_filename(archivo.filename)
                    ruta_archivo = os.path.join(carpeta_destino, filename)
                    try:
                        archivo.save(ruta_archivo)
                        auto_push_archivos()
                        mensaje = f"✅ Archivo <strong>{filename}</strong> subido correctamente."
                        log_debug(f"Archivo {filename} subido a {carpeta_destino}")
                        registrar_log_simple(f"📁 Archivo subido por panel: {filename} en {carpeta_destino}")
                    except Exception as e:
                        mensaje = f"❌ Error al guardar archivo: {e}"
                        log_debug(mensaje)

                    resultado = {"legajo": legajo, **emp}

    return render_template("subir_archivo_empleado.html", mensaje=mensaje, resultado=resultado)

@app.route('/subir_archivo_publico', methods=['GET', 'POST'])
def subir_archivo_publico():
    log_debug("Acceso a subir archivo público")
    mensaje = ""

    if request.method == 'POST':
        archivo = request.files.get("archivo")
        if not archivo:
            mensaje = "❌ No se seleccionó ningún archivo."
            log_debug(mensaje)
        else:
            filename = secure_filename(archivo.filename)
            carpeta_destino = os.path.join("static", "archivos", "publicos")
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta_archivo = os.path.join(carpeta_destino, filename)
            archivo.save(ruta_archivo)
            auto_push_archivos()
            mensaje = f"✅ Archivo público {filename} subido correctamente."
            log_debug(mensaje)

    return render_template("subir_archivo_publico.html", mensaje=mensaje)

@app.route("/archivos/<legajo>")
def ver_archivos_empleado(legajo):
    log_debug(f"Vista web de archivos para {legajo}")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
    except Exception as e:
        return f"❌ Error al cargar empleados: {e}"

    emp = empleados.get(legajo)
    if not emp:
        return f"Empleado con legajo {legajo} no encontrado."

    apellido = emp.get("apellido", "SinApellido").replace(" ", "_")
    nombre = emp.get("nombre", "SinNombre").replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")

    archivos = []
    if os.path.exists(carpeta):
        for archivo in os.listdir(carpeta):
            archivos.append({
                "nombre": archivo,
                "url": f"/static/archivos/{apellido}_{nombre}/{archivo}".replace(" ", "%20")
            })

    return render_template("ver_archivos_empleado.html", archivos=archivos, nombre_completo=f"{emp['nombre']} {emp['apellido']}")


# ---------------------------
# Ejecutar la app
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    log_debug("Servidor Flask iniciado")
    app.run(host="0.0.0.0", port=port)
