import json
from datetime import datetime, timedelta
import os

# --- LOGGING SIMPLE ---
def log_debug(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("bot_debug.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")

# --- Funciones de Utilidad ---

def _obtener_saludo_dinamico(nombre, last_interaction_date_str):
    """Genera un saludo dinámico basado en la hora del día y la última interacción."""
    ahora = datetime.now()
    saludo_parte = ""

    if 5 <= ahora.hour < 12:
        saludo_parte = "¡Buenos días"
    elif 12 <= ahora.hour < 19:
        saludo_parte = "¡Buenas tardes"
    else:
        saludo_parte = "¡Buenas noches"

    bienvenida_parte = ""
    if last_interaction_date_str:
        try:
            last_interaction_date = datetime.strptime(last_interaction_date_str, "%Y-%m-%d")
            if last_interaction_date.date() == ahora.date():
                bienvenida_parte = "! ¡Qué bueno verte de nuevo!"
            elif last_interaction_date.date() == (ahora - timedelta(days=1)).date():
                bienvenida_parte = "! ¡Bienvenido de vuelta!"
            else:
                bienvenida_parte = "! ¡Me alegra que regreses!" 
        except ValueError:
            bienvenida_parte = "! ¡Bienvenido al Bot de RRHH!"
    else:
        bienvenida_parte = "! ¡Es un gusto conocerte!"

    return f"{saludo_parte}, {nombre}{bienvenida_parte}"

def _actualizar_last_interaction(telefono):
    """Actualiza la fecha de la última interacción del usuario en empleados.json."""
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except FileNotFoundError:
        log_debug("Error: empleados.json no encontrado al actualizar la interacción.")
        return
    except json.JSONDecodeError:
        log_debug("Error: Formato inválido de empleados.json al actualizar interacción.")
        return

    encontrado = False
    telefono_limpio = str(telefono).replace("whatsapp:", "").replace("+", "").strip()

    for emp_id, emp_info in empleados_data.items():
        emp_telefono_limpio = str(emp_info.get("telefono", "")).replace("+", "").strip()

        if emp_telefono_limpio == telefono_limpio:
            emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
            encontrado = True
            break
        if telefono_limpio.startswith("549") and emp_telefono_limpio == telefono_limpio[3:]:
            emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
            encontrado = True
            break
        if telefono_limpio.startswith("54") and emp_telefono_limpio == telefono_limpio[2:]:
            emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
            encontrado = True
            break

    if encontrado:
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)
        log_debug(f"✅ Se actualizó last_interaction_date para {telefono}")
    else:
        log_debug(f"⚠️ No se encontró empleado con teléfono {telefono} para actualizar last_interaction.")

# --- Funciones de Menú ---

def mostrar_menu_admin(nombre_admin, telefono_admin=None):
    saludo = ""
    if telefono_admin:
        empleado_info = obtener_usuario_por_telefono(telefono_admin)
        if empleado_info:
            saludo = f"👋 ¡Hola {nombre_admin}! Bienvenido al panel de RRHH.\nEstoy acá para ayudarte a gestionar todo. 🛠️"

    if not saludo:
        saludo = f"👋 ¡Hola {nombre_admin}! Bienvenido al panel de RRHH."

    menu_text = (
        f"{saludo}\n\n"
        "📋 Panel del Administrador\n\n"
        "1️⃣ Agregar Empleado ➕\n"
        "2️⃣ Editar Empleado ✏️\n"
        "3️⃣ Eliminar Empleado 🗑️\n"
        "4️⃣ Ver Todos 👥\n"
        "5️⃣ Consultar Info 🔍\n"
        "6️⃣ Subir Archivo a Empleado ⬆️\n"
        "7️⃣ Próximos Cumples 📅\n"
        "8️⃣ Cerrar Sesión 🔒"
    )
    return menu_text

def mostrar_menu_empleado(nombre_empleado, telefono_empleado=None):
    saludo = ""
    if telefono_empleado:
        empleado_info = obtener_usuario_por_telefono(telefono_empleado)
        if empleado_info:
            saludo = f"👋 ¡Hola {nombre_empleado}! Soy tu asistente de RRHH.\nEstoy acá para ayudarte con tus consultas. 💼"

    if not saludo:
        saludo = f"👋 ¡Hola {nombre_empleado}! Bienvenido al Bot de RRHH."

    menu_text = (
       f"{saludo}\n\n"
       "📋 Menú Principal - Empleado\n\n"
       "1️⃣ Vacaciones 🏖️\n"
       "2️⃣ Préstamo 💰\n"
       "3️⃣ Mi Información 🧾\n"
       "4️⃣ Mis Archivos 📁\n"
       "5️⃣ Próximos Cumples 📅\n"
       "6️⃣ Archivos Públicos 📂\n"
       "7️⃣ Salir ❌"
    ) 

    return menu_text
# --- Funciones de Procesamiento de Opciones ---

def procesar_opcion_admin(usuario, opcion, current_state=None, base_url=""):
    log_debug(f"Admin {usuario['nombre']} seleccionó opción {opcion}")
    response_text = ""
    next_state = None

    if opcion == "1":
        response_text = (
            "Ingresá los datos del nuevo empleado en el siguiente formato:\n"
            "nombre, rol, sector, fecha_nacimiento (DD-MM-YYYY), fecha_ingreso (DD-MM-YYYY), "
            "vacaciones (días), préstamo (monto), notas, telefono (sin 'whatsapp:')\n"
            "Ejemplo: Juan Pérez, empleado, Ventas, 15-06-1990, 01-01-2015, 10, 5000, "
            "Buen rendimiento, 54911xxxxxxxx"
        )
        next_state = "crear_empleado_paso_1_datos"
    elif opcion == "2":
        response_text = "Ingresá el ID del empleado que querés editar."
        next_state = "editar_empleado_paso_1_id"
    elif opcion == "3":
        response_text = "Ingresá el ID del empleado que querés eliminar."
        next_state = "eliminar_empleado_paso_1_id"
    elif opcion == "4":
        response_text = listar_todos_los_empleados()
        next_state = "menu_admin"
    elif opcion == "5":
        response_text = "Ingresá el nombre o ID del empleado a consultar."
        next_state = "esperando_nombre_info_empleado"
    elif opcion == "6":
        response_text = "Ingresá el nombre del empleado a quien querés subir un archivo."
        next_state = "esperando_nombre_subir_archivo_admin_paso_1"
    elif opcion == "7":
        response_text = obtener_proximos_cumpleanos()
        next_state = "menu_admin"
    elif opcion == "8":
        response_text = "Sesión cerrada. ¡Hasta luego!"
        registrar_log(usuario, "Admin cerró sesión.")
        next_state = "cerrar"
    else:
        response_text = "❌ Opción no válida. Por favor, elegí una opción del menú."
        next_state = current_state

    return response_text, next_state

def procesar_opcion_empleado(usuario, opcion, base_url):
    if opcion == "1":
        return "📆 Tus días de vacaciones disponibles son: {} días.".format(
            usuario.get("vacaciones", 0)
        ), "menu_empleado"

    elif opcion == "2":
        prestamo = usuario.get("prestamo")
        if prestamo:
            return (
                f"💳 Tenés un préstamo activo:\n"
                f"- Monto: ${prestamo.get('monto')}\n"
                f"- Cuotas: {prestamo.get('cuotas')}\n"
                f"- Restan pagar: {prestamo.get('restan')}",
                "menu_empleado"
            )
        else:
            return "💸 No tenés préstamos activos registrados.", "menu_empleado"

    elif opcion == "3":
        return (
            f"📄 Información:\n"
            f"Nombre: {usuario.get('nombre')} {usuario.get('apellido')}\n"
            f"Legajo: {usuario.get('legajo')}\n"
            f"CUIL: {usuario.get('cuil')}\n"
            f"Sector: {usuario.get('sector')}\n"
            f"Fecha de ingreso: {usuario.get('fecha_ingreso')}\n"
            f"Antigüedad: {usuario.get('antiguedad')} años",
            "menu_empleado"
        )

    elif opcion == "4":
        url = f"{base_url}/archivos/{usuario['legajo']}"
        return f"📁 Podés ver tus archivos acá:\n{url}", "menu_empleado"

    #elif opcion == "5":
     #   return "📤 Para subir un archivo, ingresá al siguiente enlace:\n" \
      #         f"{base_url}/subir_archivo_empleado", "menu_empleado"

    elif opcion == "5":
        return obtener_proximos_cumpleanos(), "menu_empleado"

    elif opcion == "6":
        return f"📂 Archivos públicos disponibles:\n{base_url}/archivos/publicos", "menu_empleado"

    elif opcion == "7":
        return "👋 Hasta luego. Escribí 'menu' para volver a empezar.", None

    else:
        return "❌ Opción no válida. Escribí 'menu' para volver a empezar.", "menu_empleado"

    return response_text, next_state

# --- Funciones de Procesamiento de Empleados (EXISTENTES) ---

def obtener_usuario_por_telefono(telefono):
    log_debug(f"Buscando usuario por teléfono: {telefono}")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except FileNotFoundError:
        log_debug("Error: empleados.json no encontrado.")
        return None
    except json.JSONDecodeError:
        log_debug("Error: Formato inválido de empleados.json.")
        return None

    telefono_limpio = str(telefono).replace("whatsapp:", "").replace("+", "").strip()

    for emp_id, emp_info in empleados_data.items():
        emp_telefono_limpio = str(emp_info.get("telefono", "")).replace("+", "").strip()

        if emp_telefono_limpio == telefono_limpio:
            return emp_info
        if telefono_limpio.startswith("549") and emp_telefono_limpio == telefono_limpio[3:]:
            return emp_info
        if telefono_limpio.startswith("54") and emp_telefono_limpio == telefono_limpio[2:]:
            return emp_info

    log_debug(f"⚠️ No se encontró usuario con teléfono {telefono_limpio}")
    return None

def registrar_log(usuario_info, mensaje):
    log_file = "bot_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_identifier = usuario_info.get("nombre", usuario_info.get("telefono", "Desconocido"))
    log_entry = f"[{timestamp}] Usuario: {user_identifier} - Acción: {mensaje}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    log_debug(f"Registrado en log: {mensaje} para usuario {user_identifier}")

def procesar_datos_nuevo_empleado(message_body):
    log_debug(f"Procesando alta de nuevo empleado con datos: {message_body}")
    try:
        data = [item.strip() for item in message_body.split(',')]
        if len(data) != 9:
            return "❌ Formato incorrecto. Deben ser 9 campos separados por comas.", None

        nombre, rol, sector, fecha_nacimiento, fecha_ingreso, vacaciones_str, prestamo_str, notas, telefono = data

        if rol.lower() not in ["admin", "empleado"]:
            return "❌ Rol inválido. Debe ser 'admin' o 'empleado'.", None

        try:
            vacaciones = int(vacaciones_str)
            prestamo = float(prestamo_str)
        except ValueError:
            return "❌ Vacaciones y Préstamo deben ser números válidos.", None

        try:
            datetime.strptime(fecha_nacimiento, "%d-%m-%Y")
            datetime.strptime(fecha_ingreso, "%d-%m-%Y")
        except ValueError:
            return "❌ Formato de fecha incorrecto. Usá DD-MM-YYYY.", None

        empleados_data = {}
        try:
            with open("empleados.json", "r", encoding="utf-8") as f:
                empleados_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            empleados_data = {}

        new_id = str(max([int(k) for k in empleados_data.keys()] or [0]) + 1)

        empleados_data[new_id] = {
            "nombre": nombre,
            "rol": rol.lower(),
            "sector": sector,
            "fecha_nacimiento": fecha_nacimiento,
            "fecha_ingreso": fecha_ingreso,
            "vacaciones": vacaciones,
            "prestamo": prestamo,
            "notas": notas,
            "telefono": telefono.replace("+", "").strip(),
            "last_interaction_date": datetime.now().strftime("%Y-%m-%d")
        }

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)

        log_debug(f"Empleado {nombre} agregado con ID {new_id}")
        return f"✅ Empleado {nombre} agregado con ID {new_id}!", new_id
    except Exception as e:
        log_debug(f"❌ Error procesando nuevo empleado: {e}")
        return f"❌ Error al procesar los datos: {e}. Asegurate del formato correcto.", None

def procesar_edicion_empleado(empleado_id, campo, nuevo_valor):
    log_debug(f"Editando empleado {empleado_id}: campo {campo} → {nuevo_valor}")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ Error: Archivo de empleados no encontrado o inválido.", False

    if empleado_id not in empleados_data:
        return f"❌ Empleado con ID *{empleado_id}* no encontrado.", False

    empleado = empleados_data[empleado_id]
    campo = campo.lower()
    allowed_fields = {
        "nombre": str, "rol": str, "sector": str,
        "fecha_nacimiento": str, "fecha_ingreso": str,
        "vacaciones": int, "prestamo": float, "notas": str,
        "telefono": str, "last_interaction_date": str
    }

    if campo not in allowed_fields:
        return f"❌ Campo '{campo}' no es válido para edición. Campos permitidos: {', '.join(allowed_fields.keys())}.", False

    try:
        if campo in ["vacaciones", "prestamo"]:
            converted_value = allowed_fields[campo](nuevo_valor)
            if converted_value < 0:
                return f"❌ El valor para '{campo}' no puede ser negativo.", False
            empleado[campo] = converted_value
        elif campo == "rol":
            if nuevo_valor.lower() not in ["admin", "empleado"]:
                return "❌ Rol inválido. Debe ser 'admin' o 'empleado'.", False
            empleado[campo] = nuevo_valor.lower()
        elif campo in ["fecha_nacimiento", "fecha_ingreso", "last_interaction_date"]:
            if campo in ["fecha_nacimiento", "fecha_ingreso"]:
                datetime.strptime(nuevo_valor, "%d-%m-%Y")
            else:
                datetime.strptime(nuevo_valor, "%Y-%m-%d")
            empleado[campo] = nuevo_valor
        elif campo == "telefono":
            empleado[campo] = nuevo_valor.replace("+", "").strip()
        else:
            empleado[campo] = allowed_fields[campo](nuevo_valor)

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)

        log_debug(f"Empleado ID {empleado_id} actualizado: {campo} = {nuevo_valor}")
        return f"✅ Empleado ID *{empleado_id}* actualizado. Campo '{campo}' ahora es '{nuevo_valor}'.", True
    except ValueError:
        return f"❌ Error de formato para el campo '{campo}'. El valor '{nuevo_valor}' no es válido para este tipo.", False
    except Exception as e:
        log_debug(f"❌ Error al editar el empleado {empleado_id}: {e}")
        return f"❌ Error desconocido al editar el empleado: {e}", False

def eliminar_empleado(empleado_id):
    log_debug(f"Intentando eliminar empleado con ID: {empleado_id}")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ Error: Archivo de empleados no encontrado o inválido."

    if empleado_id in empleados_data:
        del empleados_data[empleado_id]
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)
        log_debug(f"Empleado {empleado_id} eliminado.")
        return f"✅ Empleado con ID *{empleado_id}* eliminado."
    else:
        return f"❌ Empleado con ID *{empleado_id}* no encontrado."

def listar_todos_los_empleados():
    log_debug("Listando todos los empleados.")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ No hay empleados registrados."

    if not empleados_data:
        return "❌ No hay empleados registrados."
    
    response_lines = ["👥 *Lista de Empleados:*\n"]
    for emp_id, emp_info in empleados_data.items():
        response_lines.append(f"• ID: {emp_id} - Nombre: {emp_info.get('nombre', 'N/A')} ({emp_info.get('rol', 'N/A')})")
    return "\n".join(response_lines)
def obtener_info_empleado_por_nombre_o_id(query):
    log_debug(f"Buscando info de empleado por query: {query}")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ No hay empleados registrados."

    empleado_encontrado = None
    if query.isdigit() and query in empleados_data:
        empleado_encontrado = empleados_data[query]
    else:
        for emp_id, emp_info in empleados_data.items():
            if emp_info.get('nombre', '').lower() == query.lower():
                empleado_encontrado = emp_info
                break

    if empleado_encontrado:
        info_lines = [f"ℹ️ *Información de {empleado_encontrado['nombre']}*:\n"]
        for key, value in empleado_encontrado.items():
            if key != "telefono":
                info_lines.append(f"• {key.replace('_', ' ').title()}: {value}")

        fecha_ingreso_str = empleado_encontrado.get('fecha_ingreso')
        if fecha_ingreso_str:
            try:
                fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%d-%m-%Y')
                hoy = datetime.now()
                anos = hoy.year - fecha_ingreso.year - ((hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day))
                meses = (hoy.month - fecha_ingreso.month) % 12
                info_lines.append(f"• Antigüedad: {anos} años y {meses} meses")
            except ValueError:
                info_lines.append("• Antigüedad: Fecha inválida")
        return "\n".join(info_lines)
    return f"❌ Empleado '{query}' no encontrado por nombre o ID."

def consultar_dias_vacaciones(telefono):
    log_debug(f"Consultando vacaciones para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario and "vacaciones" in usuario:
        return f"🏖️ Tenés {usuario['vacaciones']} días de vacaciones disponibles."
    return "❌ No se pudo obtener la información de vacaciones."

def consultar_prestamo(telefono):
    log_debug(f"Consultando préstamo para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario:
        prestamo = usuario.get("prestamo")
        if isinstance(prestamo, (int, float)) and prestamo > 0:
            return f"💰 Tu préstamo actual es de ${prestamo:,.2f}."
        else:
            return "ℹ️ No tenés un préstamo registrado actualmente."
    return "❌ No se pudo obtener la información del préstamo."

def consultar_cumpleanos_y_edad(telefono):
    log_debug(f"Consultando cumpleaños y edad para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario and usuario.get("fecha_nacimiento"):
        try:
            nacimiento = datetime.strptime(usuario["fecha_nacimiento"], "%d-%m-%Y")
            hoy = datetime.now()
            edad = hoy.year - nacimiento.year
            cumple = datetime(hoy.year, nacimiento.month, nacimiento.day)

            if cumple < hoy:
                cumple = datetime(hoy.year + 1, nacimiento.month, nacimiento.day)
                edad += 1

            dias = (cumple - hoy).days

            respuesta = f"🎂 Tu cumpleaños es el {nacimiento.strftime('%d/%m')}."
            if dias == 0:
                respuesta += f" ¡Es hoy! Cumplís {edad} años. 🎉"
            elif dias == 1:
                respuesta += f" ¡Es mañana! Cumplís {edad} años. 🎂"
            else:
                respuesta += f" Faltan {dias} días. Vas a cumplir {edad} años."
            return respuesta
        except ValueError:
            return "❌ Fecha de nacimiento inválida."
    return "❌ No se pudo obtener la información de cumpleaños."

def obtener_proximos_cumpleanos():
    log_debug("Buscando próximos cumpleaños")
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ Error al leer los datos."

    hoy = datetime.now().date()
    cumpleanos = []

    for emp in empleados_data.values():
        if emp.get("estado", "").lower() != "activo":
            continue
        if not emp.get("fecha_nacimiento"):
            continue

        try:
            dia, mes, anio = map(int, emp["fecha_nacimiento"].split("-"))
            fecha = datetime(hoy.year, mes, dia).date()
            if fecha < hoy:
                fecha = datetime(hoy.year + 1, mes, dia)

            dias_faltantes = (fecha - hoy).days
            if dias_faltantes <= 30:
                edad = hoy.year - anio + (1 if fecha.year > hoy.year else 0)
                cumpleanos.append({
                    "nombre": f"{emp.get('nombre', '')} {emp.get('apellido', '')}".strip(),
                    "fecha": fecha,
                    "dias": dias_faltantes,
                    "edad": edad
                })

        except Exception as e:
            log_debug(f"Error parseando fecha para {emp.get('nombre')}: {e}")
            continue

    cumpleanos.sort(key=lambda x: x["fecha"])
    if not cumpleanos:
        return "🎉 No hay cumpleaños en los próximos 30 días."

    lineas = ["🎉 *Cumpleaños próximos:*\n"]
    for c in cumpleanos:
        fecha = c["fecha"].strftime("%d/%m")
        if c["dias"] == 0:
            lineas.append(f"• {c['nombre']}: ¡HOY! 🎉 Cumple {c['edad']} años.")
        elif c["dias"] == 1:
            lineas.append(f"• {c['nombre']} ({fecha}): Mañana. Cumple {c['edad']} años. 🎂")
        else:
            lineas.append(f"• {c['nombre']} ({fecha}): en {c['dias']} días. Cumple {c['edad']} años.")
    return "\n".join(lineas)

def ver_informacion_completa(telefono):
    log_debug(f"Consultando información completa para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se pudo obtener tu información completa."

    info_lines = [f"ℹ️ *Tu Información Completa ({usuario['nombre']}):*\n"]
    for key, value in usuario.items():
        if key != "telefono":
            info_lines.append(f"• {key.replace('_', ' ').title()}: {value}")

    fecha_ingreso_str = usuario.get('fecha_ingreso')
    if fecha_ingreso_str:
        try:
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%d-%m-%Y')
            hoy = datetime.now()
            anos = hoy.year - fecha_ingreso.year - ((hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day))
            meses = (hoy.month - fecha_ingreso.month) % 12
            info_lines.append(f"• Antigüedad: {anos} años y {meses} meses")
        except ValueError:
            info_lines.append("• Antigüedad: Fecha inválida")
    return "\n".join(info_lines)

def listar_archivos_empleado(telefono, base_url):
    log_debug(f"Listando archivos para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se encontró tu información."

    apellido = usuario.get("apellido", "SinApellido").strip().replace(" ", "_")
    nombre = usuario.get("nombre", "SinNombre").strip().replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")

    if not os.path.exists(carpeta) or not os.listdir(carpeta):
        return "📁 No tenés archivos subidos en tu carpeta personal."

    archivos = os.listdir(carpeta)
    archivos.sort()

    lineas = [f"📂 *Tus archivos ({usuario['nombre']}):*\n"]
    for archivo in archivos:
        url = f"{base_url}/static/archivos/{apellido}_{nombre}/{archivo}".replace(" ", "%20")
        lineas.append(f"• {archivo} → {url}")
    return "\n".join(lineas)

def guardar_archivo_enviado_por_whatsapp(telefono, media_path, mime_type, filename=None):
    log_debug(f"Guardando archivo recibido por WhatsApp para {telefono}")
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se encontró tu información para guardar el archivo."

    apellido = usuario.get("apellido", "SinApellido").strip().replace(" ", "_")
    nombre = usuario.get("nombre", "SinNombre").strip().replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")
    os.makedirs(carpeta, exist_ok=True)

    if not filename:
        extension = mime_type.split("/")[-1]
        filename = f"archivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

    ruta_destino = os.path.join(carpeta, filename)

    try:
        with open(media_path, "rb") as source, open(ruta_destino, "wb") as dest:
            dest.write(source.read())
        log_debug(f"Archivo guardado: {ruta_destino}")
        return f"✅ Archivo recibido y guardado como *{filename}*."
    except Exception as e:
        log_debug(f"Error al guardar archivo: {e}")
        return f"❌ Error al guardar el archivo: {e}"
